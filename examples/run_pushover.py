import os
from seismoscreen import build_frame, run_pushover, plot_pushover

info = build_frame(n_stories=3, n_bays=2)
results = run_pushover(info, target_drift=0.025, n_steps=100)

print(f"Last converged drift: {results['drift'][-1]*100:.2f}%")
print(f"Base shear there:     {results['V_at_target']:.1f} kN")

os.makedirs("docs", exist_ok=True)
plot_pushover(results, save_path="docs/pushover.png", show=True)