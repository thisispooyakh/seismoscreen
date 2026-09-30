# seismoscreen

Parametric pushover of RC moment frames using OpenSeesPy.

![Pushover]

## What it does
Builds a parametric 2D RC moment frame, runs a nonlinear pushover, and reports
the base shear at the last converged step along with a pushover curve. It is a
first-pass check before committing to a full performance-based model.

## Install
Create and activate a virtual environment, then:

    pip install -e .

`openseespy` and `matplotlib` install automatically.

## Usage
    python examples/run_pushover.py

Run it from the repository root so `docs/pushover.png` is written in the right place.

## Output
- Pushover curve (base shear vs. roof drift)
- Base shear at the last converged step

## Limitations
- 2D frame only; no torsion, no bidirectional excitation.
- Fiber sections are approximate: no confined-core vs. cover distinction.
- Linear geometric transformation; P-Delta is not captured.
- The pushover runs to a target drift (2.5% by default) and does not capture
  post-peak behavior. "Base shear at the last converged step" is not a true
  capacity. The solver may stop earlier if convergence is lost. This is a
  numerical event and should not be read as structural failure without
  inspecting the curve shape.
- Screening tool only. Not a substitute for a full performance-based model.

## License
MIT