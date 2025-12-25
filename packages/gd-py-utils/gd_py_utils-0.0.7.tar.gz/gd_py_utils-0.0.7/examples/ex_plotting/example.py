import logging
import matplotlib.pyplot as plt
import numpy as np
import gdutils as gd


def main():
    # 1. Inspect Color Cycle
    print("Current color cycle:", gd.get_color_cycle())

    # 2. Use SimplePlot Context Manager
    print("Running SimplePlot demo...")

    # Example A: Standard show
    with gd.SPlot():
        fig, ax = plt.subplots(figsize=(6, 4))
        x = np.linspace(0, 10, 100)
        ax.plot(x, np.sin(x), label="Sin")
        ax.plot(x, np.cos(x), label="Cos")
        ax.set_title("SimplePlot Demo")
        gd.despine(ax=ax, trim=True)
        ax.legend()

    # Example B: Save to file (no show)
    out = gd.fPath(__file__, "out")
    with gd.Container(out) as ct:
        with gd.SPlot(ct / "test_plot.png", show=False):
            fig, ax = plt.subplots()
            gd.despine(fig)
            ax.plot([1, 2, 3], [1, 2, 3])
            fig.tight_layout()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
