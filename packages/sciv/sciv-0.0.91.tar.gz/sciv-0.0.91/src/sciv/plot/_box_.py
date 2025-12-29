# -*- coding: UTF-8 -*-

import os
from typing import Tuple, Union, Any

from pandas import DataFrame
import seaborn as sns

from .. import util as ul
from ..util import path, plot_end, plot_start

__name__: str = "plot_box"


def box_base(
    df: DataFrame,
    value: str = "value",
    x_name: str = None,
    y_name: str = "value",
    clusters: str = "clusters",
    palette: Union[Tuple, list] = None,
    width: float = 2,
    height: float = 2,
    bottom: float = 0.3,
    line_width: float = 0.3,
    marker_size: float = 0.2,
    rotation: float = 65,
    orient: str = None,
    title: str = None,
    whis: float = 1.5,
    show_fliers: bool = True,
    is_sort: bool = True,
    order_names: list = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:

    # judge
    df_columns = list(df.columns)

    if value not in df_columns:
        ul.log(__name__).error(f"The `value` ({value}) parameter must be in the `df` parameter data column name ({df_columns})")
        raise ValueError(f"The `value` ({value}) parameter must be in the `df` parameter data column name ({df_columns})")

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    group_columns = [clusters]

    new_df: DataFrame = df.groupby(group_columns, as_index=False)[value].median()

    if "color" in df_columns:
        new_df_color: DataFrame = df.groupby(group_columns, as_index=False)["color"].first()

        new_df = new_df.merge(new_df_color, how="left", on=clusters)

    colors: list = []

    # sort
    if is_sort:
        new_df.sort_values([value], ascending=False, inplace=True)
        y_names: Union[list, None] = list(new_df[clusters])
        if "color" in df_columns:
            colors = new_df["color"]
    else:
        new_df.index = new_df[clusters]
        if order_names is not None:
            y_names: list = order_names
            if "color" in df_columns:
                for i in order_names:
                    for j, c in zip(new_df[clusters], new_df["color"]):
                        if i == j:
                            colors.append(c)
                            break
        else:
            y_names = new_df[clusters]
            if "color" in df_columns:
                colors = new_df["color"]

    # scatter
    ax1 = sns.boxplot(
        data=df,
        x=clusters,
        y=value,
        order=y_names,
        showfliers=show_fliers,
        fliersize=marker_size,
        orient=orient,
        whis=whis,
        flierprops={'marker': 'o', 'markersize': marker_size},
        boxprops={'linestyle': '-', 'linewidth': line_width},
        whiskerprops={'linestyle': '-', 'linewidth': line_width},
        medianprops={'linestyle': '-', 'linewidth': line_width},
        palette=palette if palette is not None else (colors if "color" in df_columns else None),
        **kwargs
    )

    lines = ax1.lines

    for line in lines:
        line.set_linewidth(line_width)

    # set coordinate
    ax.set_xticklabels(labels=y_names, rotation=rotation)
    ax.spines['top'].set_linewidth(line_width)
    ax.spines['bottom'].set_linewidth(line_width)
    ax.spines['left'].set_linewidth(line_width)
    ax.spines['right'].set_linewidth(line_width)

    plot_end(fig, output, show)


def box_trait(
    trait_df: DataFrame,
    trait_name: str = "All",
    trait_column_name: str = "id",
    value: str = "value",
    clusters: str = "clusters",
    x_name: str = None,
    y_name: str = "value",
    palette: Tuple = None,
    orient: str = None,
    width: float = 2,
    height: float = 2,
    line_width: float = 0.1,
    marker_size: float = 0.5,
    bottom: float = 0.3,
    rotation: float = 65,
    whis: float = 1.5,
    show_fliers: bool = True,
    is_sort: bool = True,
    order_names: list = None,
    title: str = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:

    data: DataFrame = trait_df.copy()

    def trait_plot(trait_: str, atac_cell_df_: DataFrame) -> None:
        """
        show plot
        :param trait_: trait name
        :param atac_cell_df_:
        :return: None
        """
        ul.log(__name__).info("Plotting box {}".format(trait_))
        # get gene score
        trait_score = atac_cell_df_[atac_cell_df_[trait_column_name] == trait_]
        # Sort gene scores from small to large
        box_base(
            df=trait_score,
            value=value,
            x_name=x_name,
            y_name=y_name,
            width=width,
            palette=palette,
            height=height,
            bottom=bottom,
            rotation=rotation,
            is_sort=is_sort,
            whis=whis,
            order_names=order_names,
            line_width=line_width,
            show_fliers=show_fliers,
            marker_size=marker_size,
            orient=orient,
            clusters=clusters,
            title=f"{title} {trait_}" if title is not None else title,
            output=os.path.join(output, f"cell_{trait_}_score_box.pdf") if output is not None else None,
            show=show,
            **kwargs
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
