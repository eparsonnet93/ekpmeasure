import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

__all__ = ('add_legend_element')


def add_legend_element(ax, label, color, **kwargs):
    """
    Add element to legend for matplotlib.axis. For **kwargs see matplotlib.lines.line2D (https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html)

    args:
        ax (matplotlib.axis): Axis to add legend element.
        label (str or int or float): Label for legend element.
        color (str or color): Color for legend element.

    returns:
        (matplotlib.axis): Axis with updated legend

    """

    #get legend:
    legend = ax.get_legend()
    if type(legend) == type(None):
        elements = []
    else:
        #get elements (patches and lines)
        lines = legend.get_lines()
        patches = legend.get_patches()
        if len(patches) != 0:
            raise ValueError('only lines are supported in add_legend_element. Existing legend contains Patches as well.')

        #todo, update to include patches.
        elements = lines

    elements.append(Line2D([0], [0], label=label, color = color, **kwargs))

    ax.legend(handles = elements)
    return ax