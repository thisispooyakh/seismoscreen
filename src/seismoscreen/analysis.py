# src/seismoscreen/analysis.py
"""
Pushover analysis on the frame built by model.build_frame().
Returns the base-shear vs. roof-drift curve and key performance points.
"""

import openseespy.opensees as ops


def run_pushover(info, target_drift=0.025, n_steps=200, pattern="triangular"):
    """
    Apply gravity, then a lateral load pattern, and push with
    DisplacementControl on the roof node until target_drift is reached.

    pattern: "triangular" (default) or "uniform"
    Returns dict with drift[], base_shear[], yield_point, max_shear.
    """
    n_stories = info["n_stories"]
    h = info["story_height"]
    roof_node = info["roof_node"]
    node_tags = info["node_tags"]
    n_bays = len(info["xs"]) - 1

    # --- gravity ---
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for j in range(1, n_stories + 1):
        for i in range(n_bays + 1):
            ops.load(node_tags[(i, j)], 0.0, -info["node_weight"][i], 0.0)

    ops.system("BandGeneral")
    ops.numberer("Plain")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 0.1)
    ops.algorithm("Newton")
    ops.analysis("Static")
    ops.analyze(1)

    ops.loadConst("-time", 0.0)

    # --- lateral load pattern ---
    ops.timeSeries("Linear", 2)
    ops.pattern("Plain", 2, 2)
    for j in range(1, n_stories + 1):
        if pattern == "triangular":
            f = j / n_stories
        else:
            f = 1.0
        for i in range(n_bays + 1):
            ops.load(node_tags[(i, j)], f, 0.0, 0.0)

    # --- pushover ---
    total_height = n_stories * h
    target_disp = target_drift * total_height
    dU = target_disp / n_steps

    ops.integrator("DisplacementControl", roof_node, 1, dU)
    ops.algorithm("Newton")
    ops.test("EnergyIncr", 1e-5, 100, 0)
    ops.analysis("Static")

    drift = [0.0]
    base_shear = [0.0]

    for _ in range(n_steps):
        ok = ops.analyze(1)
        if ok != 0:
            print(f"Solver did not converge at step {len(drift)} "
                  f"(drift = {drift[-1]*100:.2f}%). Analysis stopped.")
            break
        ops.reactions()
        # base shear = sum of horizontal reactions at fixed base
        V = sum(-ops.nodeReaction(node_tags[(i, 0)], 1)
                for i in range(n_bays + 1))
        d = ops.nodeDisp(roof_node, 1)
        drift.append(d / total_height)
        base_shear.append(V)

    # 0.75*Vmax reference point (not a bilinear yield)
    V_max = max(base_shear)
    V_ref = 0.75 * V_max
    ref_idx = next((k for k, v in enumerate(base_shear) if v >= V_ref), 0)

    return {
        "drift": drift,
        "base_shear": base_shear,
        "ref_point": (drift[ref_idx], base_shear[ref_idx]),
        "V_at_target": base_shear[-1],
        "V_max_observed": V_max,
        "target_drift": target_drift,
    }