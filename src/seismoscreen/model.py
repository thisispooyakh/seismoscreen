# src/seismoscreen/model.py
"""
Build a 2D reinforced concrete moment frame in OpenSeesPy.
Assumes: regular bay widths, regular story heights, fixed base.
"""

import openseespy.opensees as ops


# --- material defaults ---
FC = -30e3        # concrete compressive strength (kPa, negative)
FCU = -6e3       # crushing strength
EPS_U = -0.004    # crushing strain
EPS_C0= -0.002
FY = 420e3        # steel yield (kPa)
ES = 200e6        # steel modulus (kPa)
B_STEEL = 0.01    # strain hardening ratio


def build_frame(
    n_stories=3,
    n_bays=2,
    bay_width=6.0,
    story_height=3.0,
    col_dim=0.4,
    beam_dim=0.4,
    rho_long=0.01,
    gravity_load=20.0, # kN/m (beam line load)
    n_fibers=10,
):
    """
    Build the frame. Returns a dict with node tags, elements, geometry,
    and the roof node tag for the analysis module.
    """
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3)

    # --- geometry ---
    xs = [i * bay_width for i in range(n_bays + 1)]
    ys = [i * story_height for i in range(n_stories + 1)]

    # --- nodes ---
    tag = 1
    node_tags = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            ops.node(tag, x, y)
            node_tags[(i, j)] = tag
            tag += 1

    # --- boundary: fixed base ---
    for i in range(n_bays + 1):
        ops.fix(node_tags[(i, 0)], 1, 1, 1)

    # --- materials ---
    ops.uniaxialMaterial("Concrete02", 1, FC, EPS_C0, FCU, EPS_U, 0.1, 0.0, 0.0)
    ops.uniaxialMaterial("Steel02", 2, FY, ES, B_STEEL, 20.0, 0.925, 0.15)

    # --- fiber section builder ---
    def make_section(sec_tag, dim, rho):
        cover = 0.04
        n = n_fibers
        ops.section("Fiber", sec_tag)

        # concrete
        ops.patch("rect", 1, n, n, -dim / 2, -dim / 2, dim / 2, dim / 2)

        # steel: uniform perimeter layout
        As_total = rho * dim * dim
        bars_per_face = 3
        n_bars = 4 * bars_per_face - 4
        bar_area = As_total / n_bars
        yc = dim / 2 - cover

        xs_bars = [-yc + 2 * yc * k / (bars_per_face - 1)
                   for k in range(bars_per_face)]
        for x in xs_bars:
            ops.fiber(x,  yc, bar_area, 2)
            ops.fiber(x, -yc, bar_area, 2)

        ys_bars = [-yc + 2 * yc * k / (bars_per_face - 1)
                   for k in range(1, bars_per_face - 1)]
        for y in ys_bars:
            ops.fiber( yc, y, bar_area, 2)
            ops.fiber(-yc, y, bar_area, 2)

    make_section(1, col_dim, rho_long)
    make_section(2, beam_dim, rho_long)

    # --- geometric transformation ---
    ops.geomTransf("Linear", 1)

    # --- integration (Gauss-Lobatto) ---
    ops.beamIntegration("Lobatto", 1, 1, 5)   # columns: sec 1
    ops.beamIntegration("Lobatto", 2, 2, 5)   # beams:   sec 2

    # --- elements ---
    col_tag = 1000
    beam_tag = 2000
    elements = {"cols": [], "beams": []}

    for j in range(n_stories):
        for i in range(n_bays + 1):
            n1 = node_tags[(i, j)]
            n2 = node_tags[(i, j + 1)]
            ops.element("forceBeamColumn", col_tag, n1, n2, 1, 1)
            elements["cols"].append(col_tag)
            col_tag += 1

    for j in range(1, n_stories + 1):
        for i in range(n_bays):
            n1 = node_tags[(i, j)]
            n2 = node_tags[(i + 1, j)]
            ops.element("forceBeamColumn", beam_tag, n1, n2, 1, 2)
            elements["beams"].append(beam_tag)
            beam_tag += 1

    node_weight = {i: gravity_load * bay_width * (0.5 if i in (0, n_bays) else 1.0)
                   for i in range(n_bays + 1)}
    for j in range(1, n_stories + 1):
        for i in range(n_bays + 1):
            m = node_weight[i] / 9.81
            ops.mass(node_tags[(i, j)], m, m, 0.0)

    return {
        "node_tags": node_tags,
        "elements": elements,
        "xs": xs,
        "ys": ys,
        "roof_node": node_tags[(n_bays, n_stories)],
        "n_stories": n_stories,
        "story_height": story_height,
        "node_weight": node_weight
    }