# -*- coding: UTF-8 -*-

from typing import Optional, Union, Tuple, Any

import pandas as pd
from anndata import AnnData
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from PyComplexHeatmap import HeatmapAnnotation, anno_simple, ClusterMapPlotter, anno_label, anno_barplot
from matplotlib.colors import ListedColormap
from pandas import DataFrame
import seaborn as sns

from .. import util as ul
from ..util import path, type_20_colors, type_50_colors, plot_end, plot_start

__name__: str = "plot_heat_map"


def heatmap_annotation(
    adata: AnnData,
    layer: Optional[str] = None,
    width: float = 4,
    height: float = 4,
    title: Optional[str] = None,
    label: str = "value",
    row_name: Optional[str] = None,
    col_name: Optional[str] = None,
    row_names: Optional[str] = None,
    col_names: Optional[str] = None,
    row_anno_label: bool = False,
    col_anno_label: bool = False,
    row_anno_text: bool = False,
    col_anno_text: bool = False,
    row_legend: bool = False,
    col_legend: bool = False,
    row_show_names: bool = False,
    col_show_names: bool = False,
    row_cluster: bool = False,
    col_cluster: bool = False,
    cluster_method: str = "average",
    cluster_metric: str = "correlation",
    row_names_side: str = "left",
    col_names_side: str = "bottom",
    bottom: float = 0.01,
    label_size: float = 9,
    fontsize: float = 9,
    level_bar_height: float = None,
    anno_specific_labels: list = None,
    x_label_rotation: float = 245,
    y_label_rotation: float = 0,
    row_color_start_index: int = 0,
    col_color_start_index: int = 10,
    row_split: Union[int, pd.Series] = None,
    col_split: Union[int, pd.Series] = None,
    row_split_order: Union[list, str] = None,
    col_split_order: Union[list, str] = None,
    row_split_gap: float = 0.5,
    col_split_gap: float = 0.2,
    frac: float = 0.2,
    relpos: Tuple = (0, 1),
    anno_label_height: Optional[float] = None,
    selected_anno_label_height: float = 2.5,
    category_height: Optional[float] = 2.5,
    x_name: Optional[str] = None,
    y_name: Optional[str] = None,
    row_score_name: str = "association_score",
    cmap: str = "Oranges",
    is_sort: bool = True,
    show: bool = True,
    output: path = None,
    **kwargs
) -> None:
    """
    Generate a heatmap with row and column annotations.
    :param row_score_name:
    :param category_height:
    :param selected_anno_label_height:
    :param anno_label_height:
    :param frac:
    :param relpos:
    :param level_bar_height:
    :param anno_specific_labels:
    :param adata: input data;
    :param layer: Layer for processing data;
    :param width: The width of the file or image;
    :param height: The height of the file or image;
    :param title: Title of the image;
    :param label: Explanation (title) of the heatmap display value icon in the figure;
    :param row_name: Information on row annotations in the figure;
    :param col_name: Information on column annotations in the figure;
    :param row_names: The information of the row in the picture;
    :param col_names: The information of the column in the figure;
    :param row_anno_label: Whether to display the label of row comments;
    :param col_anno_label: Whether to display the label of column comments;
    :param row_anno_text: Whether to display row comment information in row comments;
    :param col_anno_text: Whether to display column comment information in column comments;
    :param row_legend: Whether to display the category description of the row in the row comments;
    :param col_legend: Whether to display the category description of the column in the column comments;
    :param row_show_names: If set to `true`, display the name of each element in the row;
    :param col_show_names: If set to `true`, display the name of each element in the column;
    :param row_cluster: Set to `true`, perform row clustering;
    :param col_cluster: Set to `true`, perform column clustering;
    :param cluster_method: If `row_cluster` or `col_cluster` is true, the clustering method will be used;
    :param cluster_metric: If `row_cluster` or `col_cluster` is true, the clustering method will be used;
    :param row_names_side: Direction of row names display. Effective when `row_names_side` is `true`;
    :param col_names_side: Direction of column names display. Effective when `col_show_names` is `true`;
    :param bottom: The gap at the bottom in the picture.
    :param label_size: The size of the font for row or column names. Effective when `row_names_side` or `col_show_names` is `true`;
    :param fontsize: The size of the row or column title. Effective when `x_name` or `y_name` not is `None`;
    :param x_label_rotation: The degree of rotation for row names. Effective when `row_names_side` is `true`;
    :param y_label_rotation: The degree of rotation for column names. Effective when `col_show_names` is `true`;
    :param row_color_start_index: Row annotation specifies the starting index of different colors;
    :param col_color_start_index: Column annotation specifies the starting index of different colors;
    :param row_split_order: list or str
        a list to specify the order of row_split, could also be 'cluster_between_groups', if cluster_between_groups was specified,
        hierarchical clustering will be performed on the mean values for each groups and pass the clustered order to row_split_order.
        For example,see https://dingwb.github.io/PyComplexHeatmap/build/html/notebooks/advanced_usage.html#Cluster-between-groups
    :param col_split_order: list or str
        a list to specify the order of col_split, could also be 'cluster_between_groups', if cluster_between_groups was specified,
        hierarchical clustering will be performed on the mean values for each groups and pass the clustered order to row_split_order.
    :param row_split_gap: default are 0.5 and 0.2 mm for row and col.
    :param col_split_gap: default are 0.5 and 0.2 mm for row and col.
    :param row_split: int or pd.Series or pd.DataFrame
        number of cluster for hierarchical clustering or pd.Series or pd.DataFrame, used to split rows or rows into subplots.
    :param col_split: int or pd.Series or pd.DataFrame
        int or pd.Series or pd.DataFrame, used to split rows or columns into subplots.
    :param x_name: Title of row name;
    :param y_name: Title of column name;
    :param cmap: Display color themes for heat maps;
    :param is_sort: If set to true, when displaying the heatmap, the row and column names are sorted and displayed;
    :param show: If true, display the image;
    :param output: Output file for image saving;
    :return: Display of image or saved file.
    """

    ul.log(__name__).info("Start plotting the heatmap")
    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    data = adata.copy()

    # judge layers
    if layer is not None:

        if layer not in list(data.layers):
            ul.log(__name__).error("The value of the `layer` parameter must be one of the keys in `adata.layers`.")
            raise ValueError(f"The `{layer}` parameter needs to include in `adata.layers`")

        data.X = data.layers[layer]

    if is_sort:
        data = data[data.obs.sort_values(row_name).index, data.var.sort_values(col_name).index]

    # DataFrame
    df: DataFrame = data.to_df()

    row_anno: DataFrame = data.obs.copy()

    col_anno: DataFrame = data.var.copy()

    if row_names is not None:
        df.index = data.obs[row_names].astype(str)
        row_anno.index = data.obs[row_names].astype(str)

    if col_names is not None:
        df.columns = data.var[col_names].astype(str)
        col_anno.index = data.var[col_names].astype(str)

    if row_name is not None:
        row_colors = type_20_colors[row_color_start_index:] if len(
            list(set(row_anno[row_name]))) + row_color_start_index <= 20 else type_50_colors[row_color_start_index:]
    else:
        row_colors = "cmap50"

    if col_name is not None:
        col_colors = type_20_colors[col_color_start_index:] if len(
            list(set(col_anno[col_name]))) + col_color_start_index <= 20 else type_50_colors[col_color_start_index:]
    else:
        col_colors = "cmap50"

    df_rows = None
    if anno_specific_labels is not None:
        df_rows = df.apply(lambda x: x.name if x.name in anno_specific_labels else None, axis=1)
        df_rows.name = "Selected"

    # noinspection PyTypeChecker
    row_ha = HeatmapAnnotation(
        label=anno_label(
            row_anno[row_name], cmap=ListedColormap(row_colors), merge=True, height=anno_label_height
        ) if row_anno_label else None,
        RowCategory=anno_simple(
            row_anno[row_name],
            cmap=ListedColormap(row_colors),
            height=category_height,
            legend=row_legend,
            add_text=row_anno_text,
            text_kws=dict(color="black", rotation=0, fontsize=label_size),
        ) if row_name is not None else None,
        axis=0,
        verbose=0,
        legend_gap=5,
        hgap=0.5,
        label_kws=dict(color="black", rotation=90, horizontalalignment="left")
    )

    # noinspection PyTypeChecker
    row_ha_right = HeatmapAnnotation(
        AssociationScore=anno_barplot(row_anno[[row_score_name]], legend=True, height=level_bar_height,
                                      **dict(edgecolor='none')) if row_score_name in row_anno.columns else None,
        selected=anno_label(df_rows, relpos=relpos, frac=frac,
                            height=selected_anno_label_height) if anno_specific_labels is not None else None,
        axis=0,
        verbose=0,
        legend_gap=5,
        hgap=0.5,
        label_kws=dict(color="black", rotation=90, horizontalalignment="left")
    )

    col_ha_args = {"rotation": 90}
    # noinspection PyTypeChecker
    col_ha = HeatmapAnnotation(
        label=anno_label(
            col_anno[col_name], cmap=ListedColormap(col_colors), merge=True, height=anno_label_height, **col_ha_args
        ) if col_anno_label else None,
        ColCategory=anno_simple(
            col_anno[col_name],
            cmap=ListedColormap(col_colors),
            height=category_height,
            add_text=col_anno_text,
            legend=col_legend,
            text_kws={'fontsize': label_size}
        ) if col_name is not None else None,
        axis=1,
        verbose=0,
        legend_gap=5,
        hgap=0.5,
        label_side='left',
        label_kws=dict(color="black", rotation=0, horizontalalignment="right")
    )

    """
    It is worth noting here that, `row_cluster_metric="correlation"`, When the default parameter 
    `row_cluster_metric` in method `ClusterMapPlotter` is passed into method `distance.pdist`, 
    that is `metric='correlation'`, and this method derives from this 
    `https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.spatial.distance.pdist.html`,
    it can be inferred that there is a division formula in one step, which may result in the possibility of `NA`.
    
    For example, in this scATAC-seq data, if there are two or more traits without any intersection, 
    the denominator will appear as zero.
    
    Therefore, use the `"median"` value for parameter `row_cluster_method`
    Therefore, use the `"euclidean"` value for parameter `row_cluster_metric`
    """

    ClusterMapPlotter(
        data=df,
        top_annotation=col_ha if col_name is not None else None,
        left_annotation=row_ha if row_name is not None else None,
        right_annotation=row_ha_right if anno_specific_labels is not None or row_score_name in row_anno.columns else None,
        label=label,
        row_cluster_method=cluster_method,
        row_cluster_metric=cluster_metric,
        col_cluster_method=cluster_method,
        col_cluster_metric=cluster_metric,
        show_rownames=row_show_names,
        show_colnames=col_show_names,
        row_names_side=row_names_side,
        col_names_side=col_names_side,
        col_split=col_split,
        row_split=row_split,
        row_split_order=row_split_order,
        col_split_order=col_split_order,
        col_split_gap=col_split_gap,
        row_split_gap=row_split_gap,
        xticklabels_kws=dict(labelrotation=x_label_rotation, labelcolor='black', labelsize=label_size),
        yticklabels_kws=dict(labelrotation=y_label_rotation, labelcolor='black', labelsize=label_size),
        cmap=cmap,
        tree_kws={'row_cmap': 'Dark2'},
        xlabel=x_name,
        ylabel=y_name,
        xlabel_kws=dict(color='black', fontsize=fontsize),
        ylabel_kws=dict(color='black', fontsize=fontsize),
        col_cluster=col_cluster,
        row_cluster=row_cluster,
        col_dendrogram=col_cluster,
        row_dendrogram=row_cluster,
        **kwargs
    )

    plot_end(fig, output, show)


def heatmap(
    adata: AnnData,
    layer: str = None,
    title: Optional[str] = None,
    width: float = 4,
    height: float = 4,
    bottom: float = 0,
    annot: bool = False,
    square: bool = True,
    is_cluster: bool = False,
    cmap: str = "Oranges",
    line_widths: float = 1,
    fmt: str = ".2f",
    rotation: float = 65,
    x_name: str = None,
    y_name: str = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    data = adata.copy()

    # judge layers
    if layer is not None:

        if layer not in list(data.layers):
            ul.log(__name__).error("The value of the `layer` parameter must be one of the keys in `adata.layers`.")
            raise ValueError("The value of the `layer` parameter must be one of the keys in `adata.layers`.")

        data.X = data.layers[layer]

    # DataFrame
    ul.log(__name__).info(f"to DataFrame")
    df: DataFrame = data.to_df()
    # seaborn
    heat_map: Axes = sns.clustermap(data=df, square=square, annot=annot, cmap=cmap, fmt=fmt, **kwargs) \
        if is_cluster else \
        sns.heatmap(data=df, square=square, annot=annot, cmap=cmap, linewidths=line_widths, fmt=fmt, **kwargs)

    if not is_cluster:
        plt.setp(heat_map.get_xticklabels(), rotation=rotation, ha="right", rotation_mode="anchor")
    else:
        # noinspection PyUnresolvedReferences
        plt.setp(heat_map.ax_heatmap.get_xticklabels(), rotation=rotation)

    plot_end(fig, output, show)
