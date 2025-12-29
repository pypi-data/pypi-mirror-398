# -*- coding: UTF-8 -*-

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.gridspec import GridSpec
from pandas import DataFrame

from .. import util as ul
from ..util import path, type_50_colors, type_20_colors, plot_end

__name__: str = "plot_barcode"


def barcode_base(
    df: DataFrame,
    cluster_list: list,
    sort_column: str = "value",
    column: str = "clusters",
    width: float = 1,
    height: float = 3,
    trait_column_name: str = "id",
    title: str = None,
    cmap: str = "Oranges",
    bar_label: str = "TRS",
    is_ticks: bool = True,
    colors: list = None,
    ground_true: list = None,
    output: path = None,
    show: bool = True
):
    # sort
    df_sort = df.sort_values([trait_column_name, sort_column], ascending=False)

    # set index
    class_list = list(set(df_sort[column]))
    id_list = list(set(df_sort[trait_column_name]))
    df_sort["class_index"] = np.zeros(df_sort.shape[0])

    if colors is None:
        colors = type_20_colors if len(class_list) <= 20 else type_50_colors

    for i in class_list:

        if ground_true is not None:
            ground_true: list
            df_sort.loc[df_sort[df_sort[column] == i].index, ["class_index"]] = ground_true.count(i)
        else:
            df_sort.loc[df_sort[df_sort[column] == i].index, ["class_index"]] = cluster_list.index(i)

    class_index = np.array(df_sort["class_index"])

    # figure
    fig = plt.figure(figsize=(width, height))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.99, bottom=0.01)

    plt.axis("off")

    if title is not None:
        plt.title(title)

    gs = GridSpec(20, 20)
    ax1 = fig.add_subplot(gs[:17, 11:14] if is_ticks else gs[:18, 11:14])
    ax2 = fig.add_subplot(gs[:17, :8] if is_ticks else gs[:18, :8])

    # span the whole figure
    ax1.set_axis_off()
    ax1.imshow(
        np.array(class_index).reshape(int(df_sort.shape[0] / len(id_list)), -1),
        cmap=ListedColormap(colors),
        aspect='auto',
        interpolation='nearest'
    )
    # ax1.tick_params(axis='x', rotation=90)

    ax2.set_axis_off()
    im2 = ax2.imshow(
        np.array(df_sort[sort_column]).reshape(int(df_sort.shape[0] / len(id_list)), -1),
        cmap=cmap,
        aspect='auto',
        interpolation='nearest'
    )

    # [left, bottom, width, height]
    cax = fig.add_axes([0.12, 0.09, 0.5, 0.04] if is_ticks else [0.1, 0.04, 0.5, 0.04])
    color_bar = plt.colorbar(im2, ax=ax2, cax=cax, label=bar_label, orientation='horizontal')
    color_bar.set_label(bar_label)

    ticks = np.linspace(round(df_sort[sort_column].min(), 2), round(df_sort[sort_column].max() - 0.05, 2), 3)
    color_bar.set_ticks(ticks if is_ticks else [])

    plot_end(fig, output, show)


def barcode_trait(
    trait_df: DataFrame,
    trait_name: str = "All",
    trait_column_name: str = "id",
    sort_column: str = "value",
    clusters: str = "clusters",
    cmap: str = "viridis",
    width: float = 1,
    height: float = 3,
    is_ticks: bool = True,
    colors: list = None,
    ground_true: list = None,
    title: str = None,
    output: path = None,
    show: bool = True
):
    data: DataFrame = trait_df.copy()
    cluster_list = list(set(trait_df[clusters]))

    def trait_plot(trait_: str, atac_cell_df_: DataFrame) -> None:
        """
        show plot
        :param trait_: trait name
        :param atac_cell_df_:
        :return: None
        """
        ul.log(__name__).info("Plotting barcode {}".format(trait_))
        # get gene score
        trait_score = atac_cell_df_[atac_cell_df_[trait_column_name] == trait_]
        # Sort gene scores from small to large
        barcode_base(
            df=trait_score,
            cluster_list=cluster_list,
            sort_column=sort_column,
            trait_column_name=trait_column_name,
            column=clusters,
            width=width,
            height=height,
            is_ticks=is_ticks,
            colors=colors,
            cmap=cmap,
            ground_true=ground_true,
            title=f"{title} {trait_}" if title is not None else title,
            output=os.path.join(output, f"cell_{trait_}_score_rank.pdf") if output is not None else None,
            show=show
        )

    # noinspection DuplicatedCode
    trait_list = list(set(data[trait_column_name]))
    # judge trait
    if trait_name != "All" and trait_name not in trait_list:
        ul.log(__name__).error(f"The {trait_name} trait/disease is not in the trait/disease list {trait_list}.")
        raise ValueError(f"The {trait_name} trait/disease is not in the trait/disease list {trait_list}.")

    # plot
    if trait_name == "All":
        for trait in trait_list:
            trait_plot(trait, trait_df)
    else:
        trait_plot(trait_name, trait_df)
