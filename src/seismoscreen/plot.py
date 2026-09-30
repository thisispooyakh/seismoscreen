# src/seismoscreen/plot.py
"""
Pushover curve plotting.
"""

import matplotlib.pyplot as plt


def plot_pushover(results, save_path=None, show=True):
    """
    Plot base shear vs. roof drift with the yield point marked.
    """
    drift = [d * 100 for d in results["drift"]]  # to %
    V = results["base_shear"]
    dy, Vy = results["ref_point"]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(drift, V, "b-", lw=2, label="Pushover")

    ax.set_xlabel("Roof drift (%)")
    ax.set_ylabel("Base shear (kN)")
    ax.set_title(f"Pushover to {results['target_drift']*100:.1f}% roof drift")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()

    return fig, ax