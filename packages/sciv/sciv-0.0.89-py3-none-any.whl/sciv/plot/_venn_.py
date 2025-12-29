# -*- coding: UTF-8 -*-

from typing import Any

from matplotlib_venn import venn3, venn3_circles, venn2, venn2_circles

from .. import util as ul
from ..util import path, collection, type_set_colors, plot_end, plot_start

__name__: str = "plot_venn"


def three_venn(
    set1: collection,
    set2: collection,
    set3: collection,
    name1: str = "Set1",
    name2: str = "Set2",
    name3: str = "Set3",
    width: float = 2,
    height: float = 2,
    bottom: float = 0,
    colors: list = None,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    if colors is None:
        colors = type_set_colors[:3]

    if len(colors) < 3:
        ul.log(__name__).info(f"The value of colors requires three elements.")
        raise ValueError(f"The value of colors requires three elements.")
    elif len(colors) > 3:
        colors = colors[:3]

    set1 = set(set1)
    set2 = set(set2)
    set3 = set(set3)

    subsets = (set1, set2, set3)

    venn3(subsets=subsets, set_labels=(name1, name2, name3), ax=ax, set_colors=colors, **kwargs)

    # noinspection PyTypeChecker
    venn3_circles(subsets=subsets, linestyle='dashed', linewidth=1, color="grey", ax=ax)

    ax.legend(loc='upper right')

    ax.axis('off')

    plot_end(fig, output, show)


def two_venn(
    set1: collection,
    set2: collection,
    name1: str = "Set1",
    name2: str = "Set2",
    width: float = 2,
    height: float = 2,
    bottom: float = 0,
    colors: list = None,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    if colors is None:
        colors = type_set_colors[:2]

    if len(colors) < 2:
        ul.log(__name__).info(f"The value of colors requires three elements.")
        raise ValueError(f"The value of colors requires three elements.")
    elif len(colors) > 2:
        colors = colors[:2]

    set1 = set(set1)
    set2 = set(set2)

    venn2((set1, set2), set_labels=(name1, name2), ax=ax, set_colors=colors, **kwargs)

    # noinspection PyTypeChecker
    venn2_circles(subsets=(set1, set2), linestyle='dashed', linewidth=1, color="grey", ax=ax)

    ax.legend(loc='upper right')

    ax.axis('off')

    plot_end(fig, output, show)
