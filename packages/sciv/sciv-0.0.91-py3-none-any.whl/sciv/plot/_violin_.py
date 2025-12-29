# -*- coding: UTF-8 -*-

import os
from typing import Tuple, Union, Literal, Any

from pandas import DataFrame
import seaborn as sns

from .. import util as ul
from ..util import path, plot_end, plot_start

__name__: str = "plot_violin"

_Kind = Literal["strip", "swarm", "box", "violin", "boxen", "point", "bar", "count"]


def violin_base(
    df: DataFrame,
    value: str = "value",
    x_name: str = None,
    y_name: str = "value",
    kind: _Kind = "violin",
    clusters: str = "clusters",
    palette: Union[Tuple, list] = None,
    hue: str = None,
    width: float = 2,
    height: float = 2,
    bottom: float = 0.3,
    rotation: float = 65,
    line_width: float = 0.5,
    title: str = None,
    split: bool = True,
    is_sort: bool = True,
    order_names: list = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    # judge
    df_columns = list(df.columns)

    if value not in df_columns:
        ul.log(__name__).error(
            f"The `value` ({value}) parameter must be in the `df` parameter data column name ({df_columns})")
        raise ValueError(
            f"The `value` ({value}) parameter must be in the `df` parameter data column name ({df_columns})")

    if hue is not None and hue not in df_columns:
        ul.log(__name__).error(
            f"The `hue` ({hue}) parameter must be in the `df` parameter data column name ({df_columns})")
        raise ValueError(f"The `hue` ({hue}) parameter must be in the `df` parameter data column name ({df_columns})")

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
            colors = list(new_df["color"])
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
            y_names = list(new_df[clusters])
            if "color" in df_columns:
                colors = list(new_df["color"])

    # scatter
    g = sns.catplot(
        data=df,
        x=clusters,
        y=value,
        kind=kind,
        hue=hue,
        order=y_names,
        split=split,
        linewidth=line_width,
        palette=palette if palette is not None else (colors if "color" in df_columns else None),
        **kwargs
    )

    # set coordinate
    for ax in g.axes.flat:
        ax.spines['top'].set_linewidth(line_width)
        ax.spines['right'].set_linewidth(line_width)
        ax.spines['bottom'].set_linewidth(line_width)
        ax.spines['left'].set_linewidth(line_width)
        # Set the rotation angle of the x-axis labels
        ax.tick_params(axis='x', rotation=rotation)

    plot_end(fig, output, show)


def violin_trait(
    trait_df: DataFrame,
    trait_name: Union[str, list] = "All",
    trait_column_name: str = "id",
    value: str = "value",
    clusters: str = "clusters",
    kind: _Kind = "violin",
    x_name: str = None,
    y_name: str = "value",
    palette: Tuple = None,
    width: float = 2,
    height: float = 2,
    rotation: float = 65,
    line_width: float = 0.1,
    bottom: float = 0.3,
    split: bool = True,
    is_sort: bool = True,
    order_names: list = None,
    title: str = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:

    data: DataFrame = trait_df.copy()

    def trait_plot(trait_: Union[str, list], atac_cell_df_: DataFrame) -> None:
        """
        show plot
        :param trait_: trait name
        :param atac_cell_df_:
        :return: None
        """
        ul.log(__name__).info("Plotting box {}".format(", ".join(trait_)))
        # get gene score
        _filename_: str = trait_ if isinstance(trait_, str) else "_".join(trait_)
        trait_score = atac_cell_df_[
            atac_cell_df_[trait_column_name] == trait_ if isinstance(trait_, str) else atac_cell_df_[
                trait_column_name].isin(trait_)]
        # Sort gene scores from small to large
        violin_base(
            df=trait_score,
            value=value,
            x_name=x_name,
            y_name=y_name,
            width=width,
            palette=palette,
            height=height,
            bottom=bottom,
            split=split,
            is_sort=is_sort,
            rotation=rotation,
            order_names=order_names,
            kind=kind,
            hue=trait_column_name,
            line_width=line_width,
            clusters=clusters,
            title=f"{title} {_filename_}" if title is not None else title,
            output=os.path.join(output, f"cell_{_filename_}_score_cat_{kind}.pdf") if output is not None else None,
            show=show,
            **kwargs
        )

    # noinspection DuplicatedCode
    trait_list = list(set(data[trait_column_name]))
    # judge trait
    if trait_name != "All":
        if isinstance(trait_name, str) and trait_name not in trait_list:
            ul.log(__name__).error(f"The {trait_name} trait/disease is not in the trait/disease list {trait_list}.")
            raise ValueError(f"The {trait_name} trait/disease is not in the trait/disease list {trait_list}.")
        else:
            for tn in trait_name:
                if tn not in trait_list:
                    ul.log(__name__).error(f"The {tn} trait/disease is not in the trait/disease list {trait_list}.")
                    raise ValueError(f"The {tn} trait/disease is not in the trait/disease list {trait_list}.")

    # plot
    if trait_name == "All":
        for trait in trait_list:
            trait_plot(trait, trait_df)
    else:
        trait_plot(trait_name, trait_df)
