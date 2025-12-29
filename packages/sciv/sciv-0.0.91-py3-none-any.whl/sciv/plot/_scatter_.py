# -*- coding: UTF-8 -*-

import os.path
from typing import Union, Tuple, Optional, Any

import matplotlib
import numpy as np
from anndata import AnnData
from matplotlib import pyplot as plt
from pandas import DataFrame
import seaborn as sns

from .. import util as ul
from ..util import path, collection, type_50_colors, type_20_colors, chrtype, type_set_colors, plot_end, plot_start

__name__: str = "plot_pie"

matplotlib.set_loglevel("error")


def scatter_base(
    df: DataFrame,
    x: str,
    y: str,
    hue: str = None,
    hue_order: list = None,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    bar_label: str = None,
    cmap: str = "Oranges",
    width: float = 2,
    height: float = 2,
    right: float = 0.9,
    bottom: float = 0,
    text_fontsize: float = 7,
    legend_fontsize: float = 7,
    start_color_index: int = 0,
    color_step_size: int = 0,
    type_colors: collection = None,
    edge_color: str = None,
    size: Union[float, collection] = 1.0,
    legend: dict = None,
    number: bool = False,
    is_text: bool = False,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    # scatter
    if number:
        norm = plt.Normalize(df[hue].min(), df[hue].max())
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, label=bar_label)
        sns.scatterplot(
            data=df,
            x=x,
            y=y,
            palette=cmap,
            hue=hue,
            s=size,
            legend=False,
            edgecolor=edge_color,
            **kwargs
        )
    else:
        __hue_order__ = list(np.sort(list(set(df[hue]))))

        if type_colors is None:
            type_colors = type_20_colors if len(__hue_order__) <= 20 else type_50_colors

        colors = {}

        if legend is not None:
            df.loc[:, "__hue__"] = df[hue].copy()

        i = 0
        for elem in __hue_order__:
            if legend is not None:
                df.loc[df[df["__hue__"] == elem].index, "__hue__"] = legend[elem]
                colors.update(
                    {legend[elem]: type_colors[start_color_index + i * color_step_size + __hue_order__.index(elem)]})
            else:
                colors.update(
                    {
                        elem: type_colors[start_color_index + i * color_step_size + __hue_order__.index(elem)]
                    }
                )
            i += 1

        if legend is not None:
            if hue_order is None:
                hue_order = list(np.sort(list(set(df["__hue__"]))))
        else:
            if hue_order is None:
                hue_order = __hue_order__

        sns.scatterplot(
            data=df,
            x=x,
            y=y,
            edgecolor=edge_color,
            palette=colors,
            hue="__hue__" if legend is not None else hue,
            hue_order=hue_order,
            s=size,
            **kwargs
        )

        if is_text:

            df_anno = df[[hue, x, y]].groupby(hue, as_index=False).mean()

            for txt, i, j in zip(df_anno[hue], df_anno[x], df_anno[y]):
                plt.annotate(
                    txt,
                    xy=(i, j),
                    xytext=(-10, 0),
                    textcoords="offset points",
                    bbox=dict(
                        boxstyle="round,pad=0.2",
                        fc="white",
                        ec="k",
                        lw=1,
                        alpha=0.8
                    ),
                    fontsize=text_fontsize
                )

        ax.legend(
            loc="center left",
            bbox_to_anchor=(right, 0.5),
            bbox_transform=fig.transFigure,
            fontsize=legend_fontsize
        )

    # Remove scales and labels on the coordinate axis
    ax.set_xticks([])
    ax.set_yticks([])

    # Remove the bounding box of the coordinate axis
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plot_end(fig, output, show)


def scatter_atac(
    adata: AnnData,
    columns: Tuple[str, str] = ("UMAP1", "UMAP2"),
    clusters: str = "clusters",
    hue_order: list = None,
    width: float = 2,
    height: float = 2,
    x_name: str = None,
    y_name: str = None,
    start_color_index: int = 0,
    color_step_size: int = 0,
    type_colors: collection = None,
    edge_color: str = None,
    size: float = 1.0,
    text_fontsize: float = 7,
    legend_fontsize: float = 7,
    is_text: bool = False,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    # DataFrame
    df: DataFrame = adata.obs.copy()
    df[clusters] = df[clusters].astype(str)
    # scatter
    scatter_base(
        df,
        x=columns[0],
        y=columns[1],
        hue=clusters,
        width=width,
        height=height,
        size=size,
        x_name=x_name,
        y_name=y_name,
        hue_order=hue_order,
        start_color_index=start_color_index,
        color_step_size=color_step_size,
        type_colors=type_colors,
        edge_color=edge_color,
        is_text=is_text,
        text_fontsize=text_fontsize,
        legend_fontsize=legend_fontsize,
        output=output,
        show=show,
        right=0.75,
        **kwargs
    )


def scatter_trait(
    trait_adata: AnnData,
    title: str = None,
    bar_label: str = None,
    trait_name: str = "All",
    layers: Union[None, collection] = None,
    columns: Tuple[str, str] = ("UMAP1", "UMAP2"),
    cmap: str = "viridis",
    width: float = 2,
    height: float = 2,
    right: float = 0.9,
    x_name: str = None,
    y_name: str = None,
    number: bool = True,
    edge_color: str = None,
    size: Union[float, collection] = 1.0,
    text_fontsize: float = 7,
    legend_fontsize: float = 7,
    start_color_index: int = 0,
    color_step_size: int = 0,
    type_colors: collection = None,
    is_text: bool = False,
    legend: dict = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    data: AnnData = trait_adata.copy()

    # judge layers
    trait_adata_layers = list(data.layers)

    if layers is not None and len(layers) != 0:
        for layer in layers:
            if layer not in trait_adata_layers:
                ul.log(__name__).error("The `layers` parameter needs to include in `trait_adata.layers`")
                raise ValueError("The `layers` parameter needs to include in `trait_adata.layers`")

    def trait_plot(trait_: str, atac_cell_df_: DataFrame, layer_: str = None, new_data_: AnnData = None) -> None:
        """
        show plot
        :param trait_: trait name
        :param atac_cell_df_:
        :param layer_: layer
        :param new_data_:
        :return: None
        """
        ul.log(__name__).info(f"Plotting scatter {trait_}")
        # get gene score
        trait_score = new_data_[:, trait_].to_df()
        trait_score = trait_score.rename_axis("__barcode__")
        trait_score.reset_index(inplace=True)
        atac_cell_df_ = atac_cell_df_.rename_axis("__barcode__")
        atac_cell_df_.reset_index(inplace=True)
        # trait_score.rename_axis("index")
        df = atac_cell_df_.merge(trait_score, on="__barcode__", how="left")
        # Sort gene scores from small to large
        df.sort_values([trait_], inplace=True)
        scatter_base(
            df,
            x=columns[0],
            y=columns[1],
            hue=trait_,
            title=f"{title} {trait_}" if title is not None else title,
            bar_label=bar_label,
            legend=legend,
            cmap=cmap,
            width=width,
            height=height,
            right=right,
            number=number,
            size=size,
            x_name=x_name,
            y_name=y_name,
            type_colors=type_colors,
            text_fontsize=text_fontsize,
            legend_fontsize=legend_fontsize,
            start_color_index=start_color_index,
            color_step_size=color_step_size,
            edge_color=edge_color,
            is_text=is_text,
            output=os.path.join(
                output, f"cell_{trait_}_score_{layer_}.pdf" if layer_ is not None else f"cell_{trait_}_score.pdf"
            ) if output is not None else None,
            show=show,
            **kwargs
        )

    def handle_plot(layer_: str = None):
        # DataFrame
        atac_cell_df: DataFrame = data.obs.copy()
        atac_cell_df.rename_axis("index", inplace=True)
        trait_list: list = list(data.var_names)

        # judge trait
        if trait_name != "All" and trait_name not in trait_list:
            ul.log(__name__).error(
                f"The {trait_name} trait/disease is not in the trait/disease list (trait_adata.var_names)")
            raise ValueError(f"The {trait_name} trait/disease is not in the trait/disease list (trait_adata.var_names)")

        new_data: AnnData = AnnData(data.layers[layer], var=data.var, obs=data.obs) if layer_ is not None else data

        # plot
        if trait_name == "All":
            for trait in trait_list:
                trait_plot(trait, atac_cell_df, layer_, new_data)
        else:
            trait_plot(trait_name, atac_cell_df, layer_, new_data)

    if layers is None or len(layers) == 0:
        handle_plot()
    else:
        for layer in layers:
            ul.log(__name__).info(f"Start {layer}")
            handle_plot(layer)


def volcano_base(
    df: DataFrame,
    x: str = "Log2(Fold change)",
    y: str = "-Log10(P value)",
    hue: str = "type",
    size: int = 3,
    palette: Optional[list] = None,
    width: float = 2,
    height: float = 2,
    bottom: float = 0,
    y_min: float = 0,
    axh_value: float = -np.log10(1e-3),
    axv_left_value: float = -1,
    axv_right_value: float = 1,
    title: str = None,
    x_name: Optional[str] = None,
    y_name: Optional[str] = None,
    output: path = None,
    show: bool = True,
    **kwargs: Any
):
    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    if palette is None:
        palette = ["#01c5c4", "#686d76", "#ff414d"]

    sns.set_theme(style="ticks")
    sns.set_palette(sns.color_palette(palette))
    sns.scatterplot(data=df, x=x, y=y, hue=hue, s=size, ax=ax, **kwargs)
    ax.set_ylim(y_min, max(df[y]) * 1.1)

    plt.axhline(axh_value, color='grey', linestyle='--')
    plt.axvline(axv_left_value, color='grey', linestyle='--')
    plt.axvline(axv_right_value, color='grey', linestyle='--')

    plot_end(fig, output, show)


def manhattan_causal_variant(
    df: DataFrame,
    y: str = "pp",
    chr_name: str = "chr",
    label: str = "rsId",
    size: int = 30,
    labels: Optional[list] = None,
    colors: Optional[list] = None,
    width: float = 8,
    height: float = 2,
    bottom: float = 0,
    title: str = None,
    is_sort: bool = True,
    line_width: float = 0.5,
    y_round: int = 3,
    x_name: Optional[str] = "Chromosome",
    y_name: Optional[str] = "pp",
    y_limit: Tuple[float, float] = (0, 1),
    output: path = None,
    show: bool = True,
    **kwargs: Any
):

    df[chr_name] = df[chr_name].astype(chrtype)

    if is_sort:
        df = df.sort_values(chr_name)

    df['ind'] = range(len(df))
    df_grouped = df.groupby(chr_name)

    if colors is None:
        colors = type_20_colors.copy()
        colors.extend(type_set_colors)

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    x_labels = []
    x_labels_pos = []
    # Track the last index to draw lines between chromosomes
    last_ind = 0

    chr_unique = df[chr_name].unique()

    for num, (name, group) in enumerate(df_grouped):

        if name not in chr_unique:
            continue

        group.plot(kind='scatter', x='ind', y=y, color=colors[num], s=size, ax=ax)
        x_labels.append(name)
        x_labels_pos.append((group['ind'].iloc[-1] - (group['ind'].iloc[-1] - group['ind'].iloc[0]) / 2))

        # Draw a vertical line between chromosomes
        if num > 0:
            # Skip the first chromosome
            ax.axvline(x=last_ind + 0.5, color='gray', linestyle='--', linewidth=line_width, **kwargs)

        # Label specific mutations
        if labels is not None:
            for index, row in group.iterrows():
                if row[label] in labels:
                    ax.text(row['ind'], row[y], row[label], ha='left', va='bottom')
                    ax.text(row['ind'], row[y], f"{y}={round(row[y], y_round)}", ha='left', va='top')

        last_ind = group['ind'].iloc[-1]

    # add grid
    ax.grid(axis="y", linestyle="--", linewidth=line_width, color="gray")
    ax.set_xticks(x_labels_pos)
    ax.set_xticklabels(x_labels)

    # Hide the borders above and to the right
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_xlim([0, len(df)])
    ax.set_ylim(y_limit)

    plot_end(fig, output, show)


def pseudo_time_score(
    df: DataFrame,
    x: str,
    y: str,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    width: float = 2,
    height: float = 1.2,
    bottom: float = 0,
    alpha: float = 0.65,
    line_width: float = 1.5,
    step_length: int = 5,
    polyorder: int = 1,
    size: Union[float, collection] = 1.0,
    output: path = None,
    show: bool = True,
    **kwargs: Any
):
    from scipy.signal import savgol_filter

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    pseudo_times = df[x].values
    scores = df[y].values

    x_len = len(pseudo_times)

    colors = plt.cm.viridis(np.linspace(0, 1, x_len))

    ax.scatter(
        pseudo_times,
        scores,
        c=colors,
        alpha=alpha,
        s=size,
        **kwargs
    )

    smoothed_scores = savgol_filter(scores, window_length=int(x_len / step_length), polyorder=polyorder)

    ax.plot(pseudo_times, smoothed_scores, color='black', linewidth=line_width)

    plt.tight_layout()

    plot_end(fig, output, show)
