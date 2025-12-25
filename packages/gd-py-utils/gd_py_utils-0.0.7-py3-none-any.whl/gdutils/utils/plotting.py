import inspect
from typing import List, Optional, Union, Dict, Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def get_color_cycle() -> List[str]:
    """Return the list of colors in the current matplotlib color cycle

    Parameters
    ----------
    None

    Returns
    -------
    colors : list
        List of matplotlib colors in the current cycle, or dark gray if
        the current color cycle is empty.
    """
    cycler = mpl.rcParams["axes.prop_cycle"]
    return cycler.by_key()["color"] if "color" in cycler.keys else [".15"]


def despine(
    fig: Optional[mpl.figure.Figure] = None,
    ax: Optional[mpl.axes.Axes] = None,
    top: bool = True,
    right: bool = True,
    left: bool = False,
    bottom: bool = False,
    offset: Optional[Union[int, Dict[str, int]]] = None,
    trim: bool = False,
) -> None:
    """Remove the top and right spines from plot(s).

    fig : matplotlib figure, optional
        Figure to despine all axes of, defaults to the current figure.
    ax : matplotlib axes, optional
        Specific axes object to despine. Ignored if fig is provided.
    top, right, left, bottom : boolean, optional
        If True, remove that spine.
    offset : int or dict, optional
        Absolute distance, in points, spines should be moved away
        from the axes (negative values move spines inward). A single value
        applies to all spines; a dict can be used to set offset values per
        side.
    trim : bool, optional
        If True, limit spines to the smallest and largest major tick
        on each non-despined axis.

    Returns
    -------
    None

    """
    # Get references to the axes we want
    axes = None
    if fig is None and ax is None:
        axes = plt.gcf().axes
    elif fig is not None:
        axes = fig.axes
    elif ax is not None:
        axes = [ax]

    for ax_i in axes:
        for side in ["top", "right", "left", "bottom"]:
            # Toggle the spine objects
            is_visible = not locals()[side]
            ax_i.spines[side].set_visible(is_visible)
            if offset is not None and is_visible:
                try:
                    val = offset.get(side, 0)
                except AttributeError:
                    val = offset
                ax_i.spines[side].set_position(("outward", val))

        # Potentially move the ticks
        if left and not right:
            maj_on = any(t.tick1line.get_visible() for t in ax_i.yaxis.majorTicks)
            min_on = any(t.tick1line.get_visible() for t in ax_i.yaxis.minorTicks)
            ax_i.yaxis.set_ticks_position("right")
            for t in ax_i.yaxis.majorTicks:
                t.tick2line.set_visible(maj_on)
            for t in ax_i.yaxis.minorTicks:
                t.tick2line.set_visible(min_on)

        if bottom and not top:
            maj_on = any(t.tick1line.get_visible() for t in ax_i.xaxis.majorTicks)
            min_on = any(t.tick1line.get_visible() for t in ax_i.xaxis.minorTicks)
            ax_i.xaxis.set_ticks_position("top")
            for t in ax_i.xaxis.majorTicks:
                t.tick2line.set_visible(maj_on)
            for t in ax_i.xaxis.minorTicks:
                t.tick2line.set_visible(min_on)

        if trim:
            # clip off the parts of the spines that extend past major ticks
            xticks = np.asarray(ax_i.get_xticks())
            if xticks.size:
                firsttick = np.compress(xticks >= min(ax_i.get_xlim()), xticks)[0]
                lasttick = np.compress(xticks <= max(ax_i.get_xlim()), xticks)[-1]
                ax_i.spines["bottom"].set_bounds(firsttick, lasttick)
                ax_i.spines["top"].set_bounds(firsttick, lasttick)
                newticks = xticks.compress(xticks <= lasttick)
                newticks = newticks.compress(newticks >= firsttick)
                ax_i.set_xticks(newticks)

            yticks = np.asarray(ax_i.get_yticks())
            if yticks.size:
                firsttick = np.compress(yticks >= min(ax_i.get_ylim()), yticks)[0]
                lasttick = np.compress(yticks <= max(ax_i.get_ylim()), yticks)[-1]
                ax_i.spines["left"].set_bounds(firsttick, lasttick)
                ax_i.spines["right"].set_bounds(firsttick, lasttick)
                newticks = yticks.compress(yticks <= lasttick)
                newticks = newticks.compress(newticks >= firsttick)
                ax_i.set_yticks(newticks)


def move_legend(obj: Any, loc: Union[str, int], **kwargs: Any) -> None:
    """
    Recreate a plot's legend at a new location.

    The name is a slight misnomer. Matplotlib legends do not expose public
    control over their position parameters. So this function creates a new legend,
    copying over the data from the original object, which is then removed.

    Parameters
    ----------
    obj : the object with the plot
        This argument can be either a seaborn or matplotlib object:

        - :class:`seaborn.FacetGrid` or :class:`seaborn.PairGrid`
        - :class:`matplotlib.axes.Axes` or :class:`matplotlib.figure.Figure`

    loc : str or int
        Location argument, as in :meth:`matplotlib.axes.Axes.legend`.

    kwargs
        Other keyword arguments are passed to :meth:`matplotlib.axes.Axes.legend`.

    Examples
    --------

    .. include:: ../docstrings/move_legend.rst

    """
    # This is a somewhat hackish solution that will hopefully be obviated by
    # upstream improvements to matplotlib legends that make them easier to
    # modify after creation.

    # Locate the legend object and a method to recreate the legend
    if isinstance(obj, mpl.axes.Axes):
        old_legend = obj.legend_
        legend_func = obj.legend
    elif isinstance(obj, mpl.figure.Figure):
        if obj.legends:
            old_legend = obj.legends[-1]
        else:
            old_legend = None
        legend_func = obj.legend
    else:
        err = "`obj` must be a seaborn Grid or matplotlib Axes or Figure instance."
        raise TypeError(err)

    if old_legend is None:
        err = f"{obj} has no legend attached."
        raise ValueError(err)

    # Extract the components of the legend we need to reuse
    handles = old_legend.legend_handles

    labels = [t.get_text() for t in old_legend.get_texts()]

    # Extract legend properties that can be passed to the recreation method
    # (Vexingly, these don't all round-trip)
    legend_kws = inspect.signature(mpl.legend.Legend).parameters
    props = {k: v for k, v in old_legend.properties().items() if k in legend_kws}

    # Delegate default bbox_to_anchor rules to matplotlib
    props.pop("bbox_to_anchor", None)

    # Try to propagate the existing title and font properties; respect new ones too
    title = props.pop("title")
    if "title" in kwargs:
        title.set_text(kwargs.pop("title"))
    title_kwargs = {k: v for k, v in kwargs.items() if k.startswith("title_")}
    for key, val in title_kwargs.items():
        title.set(**{key[6:]: val})
        kwargs.pop(key)

    # Try to respect the frame visibility
    kwargs.setdefault("frameon", old_legend.legendPatch.get_visible())

    # Remove the old legend and create the new one
    props.update(kwargs)
    old_legend.remove()
    new_legend = legend_func(handles, labels, loc=loc, **props)
    new_legend.set_title(title.get_text(), title.get_fontproperties())


class SimplePlot:
    """
    Cleanly plot a figure with matplotlib.pyplot
    fig, ax = plt.subplots()

        with gd.SPlot():
            fig, ax = plt.subplots()
            gd.despine(fig)
            ax.plot()
            fig.tight_layout()

    """

    def __init__(
        self,
        fname: Optional[str] = None,
        show: bool = True,
        save: Optional[bool] = None,
    ):
        """
        :param fname: figure filename
        :param show: if `plt.show` must be called
        :param save: if `fig.savefig` must be called
        """
        self._fname = fname
        self._save = fname is not None if save is None else save
        self._show = show

    def __enter__(self) -> "SimplePlot":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Get the current figure, save/show it if specified and finally close the figure properly
        """
        # If an exception occurred, don't try to save/show the plot, just cleanup
        if exc_type is not None:
            plt.close(plt.gcf())
            return

        fig = plt.gcf()

        if self._fname is not None and self._save:
            fig.savefig(self._fname, bbox_inches="tight")

        if self._show:
            plt.show()

        plt.close(fig)

    def save(self, fname: str) -> None:
        """Give a filename to save the figure"""
        self._fname = fname
        self._save = True
