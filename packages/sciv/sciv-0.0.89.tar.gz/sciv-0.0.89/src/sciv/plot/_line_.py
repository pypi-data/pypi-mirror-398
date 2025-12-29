# -*- coding: UTF-8 -*-

from typing import Optional, Tuple, Union, Any

from pandas import DataFrame
from anndata import AnnData
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from .. import util as ul
from ..preprocessing import adata_map_df
from ..util import path, plot_color_types, collection, plot_end, plot_start

__name__: str = "plot_line"


def stability_line(
    data: Union[AnnData, DataFrame],
    x: str,
    y: str,
    layer: Optional[str] = None,
    width: float = 2,
    height: float = 2,
    bottom: float = 0,
    title: Optional[str] = None,
    x_name: Optional[str] = None,
    y_name: Optional[str] = None,
    label: Optional[str] = None,
    legend: Optional[str] = None,
    legend_list: list = None,
    start_color_index: int = 0,
    color_step_size: int = 0,
    color_type: str = "set",
    colors: list = None,
    line_width: float = 1.5,
    x_name_rotation: float = 65,
    x_ticks: Optional[Union[int, collection]] = None,
    y_limit: Tuple[float, float] = (0, 1),
    output: Optional[path] = None,
    is_str: bool = True,
    show: bool = True,
    **kwargs: Any
) -> None:

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    new_data = data.copy()

    if isinstance(new_data, AnnData):

        if legend_list is not None:

            index_list = []
            label_list = list(new_data.var[label])

            for lab in range(len(label_list)):
                if legend_list.count(label_list[lab]) > 0:
                    index_list.append(lab)

            if legend_list is not None:
                new_data = new_data[:, index_list]

        # judge layers
        if layer is not None:

            if layer not in list(new_data.layers):
                ul.log(__name__).error("The value of the `layer` parameter must be one of the keys in `adata.layers`.")
                raise ValueError("The value of the `layer` parameter must be one of the keys in `adata.layers`.")

            new_data.X = new_data.layers[layer]

        # DataFrame
        ul.log(__name__).info(f"to DataFrame")
        df: DataFrame = adata_map_df(new_data, column="value")

    elif isinstance(new_data, DataFrame):

        if legend_list is not None:
            df: DataFrame = new_data[new_data[label].isin(legend_list)].copy()
        else:
            df: DataFrame = new_data.copy()

    else:
        ul.log(__name__).error(f"The `data` parameter only support `AnnData` and `DataFrame` class types.")
        raise ValueError(f"The `data` parameter only support `AnnData` and `DataFrame` class types.")

    if legend is None:
        legend = "category"

    df[legend] = df[label].copy()
    new_data_columns = list(df.columns)

    hue_types = list(set(df[legend]))

    # noinspection DuplicatedCode
    if colors is not None:
        palette = colors
    else:
        if "color" in new_data_columns:
            palette = df["color"]
        else:
            palette = []

            for i in range(len(hue_types)):
                palette.append(plot_color_types[color_type][start_color_index + i * color_step_size + i])

    # sns.set_theme(style="whitegrid")
    ax.set(ylim=y_limit)
    sns.despine()

    if is_str:
        df[x] = df[x].astype(str)

    chart = sns.lineplot(data=df, ax=ax, x=x, y=y, hue=legend, palette=palette, linewidth=line_width, **kwargs)

    if is_str:
        locator = mdates.DayLocator(interval=1)
        chart.xaxis.set_major_locator(locator)

        ax.set_xticklabels(ax.get_xticklabels(), rotation=x_name_rotation)
    else:
        plt.xticks(x_ticks, rotation=x_name_rotation)

    plot_end(fig, output, show)
