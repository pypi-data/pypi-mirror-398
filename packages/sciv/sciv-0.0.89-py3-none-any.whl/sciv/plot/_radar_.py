# -*- coding: UTF-8 -*-

import os
from typing import Optional, Union, Tuple, Any

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from pandas import DataFrame

from .. import util as ul
from ..util import path, collection, plot_end, plot_start

__name__: str = "plot_radar"


def radar(
    ax_x: collection,
    ax_y: collection,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    colors: collection = None,
    width: float = 4,
    height: float = 4,
    bottom: float = 0,
    center_text: str = None,
    rotation: float = 25,
    value_top: float = 0.1,
    text_top: float = 1.2,
    is_fixed: bool = False,
    is_angle: bool = True,
    y_limit: Tuple = (-0.5, 1),
    y_axis_scale: Tuple = (0, 1),
    output: path = None,
    show: bool = True,
    **kwargs: Any
):

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    ax_x = list(ax_x)
    ax_y = list(ax_y)

    # Create a circular bar chart
    theta = np.linspace(0, 2 * np.pi, len(ax_x), endpoint=False).tolist()
    ax_y += ax_y[:1]
    theta += theta[:1]

    width = 2 * 2.7 / len(ax_x)

    bars = ax.bar(theta, ax_y, width=width, color=colors, edgecolor='none', alpha=0.8, zorder=3, **kwargs)

    # Add category labels
    ax.set_xticks(theta)
    ax.set_xticklabels([])

    # Set y-axis range
    ax.set_ylim(y_limit[0], y_limit[1])

    # Remove the scale value of the circle
    ax.set_yticks(np.linspace(y_axis_scale[0], y_axis_scale[1], 6))  # Set the y-axis scale position
    ax.set_yticklabels([])  # Do not display scale values
    ax.set_theta_zero_location('N')  # Set polar axis position
    ax.set_theta_direction(-1)  # The angle increases counterclockwise

    # Add numerical labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        angle = np.degrees(theta[i])
        label_position = theta[i]
        ax.text(label_position, height + value_top if not is_fixed else value_top, round(height, 3), ha='center', va='center', color='#1f1f1f', rotation=-angle + rotation if is_angle else rotation)

    # Add radar line
    ax.plot(theta, ax_y, color='gray', linewidth=1, zorder=1)
    # Draw radar map
    ax.fill(theta, ax_y, color='#DDDDDD', alpha=0.1, zorder=2)

    if center_text is not None:
        ax.text(0, y_limit[0], center_text, ha='center', va='center', fontsize=14, color='black', zorder=11)

    # Set the y-axis scale line color to light gray
    ax.tick_params('y', colors='#DDDDDD', grid_alpha=0.6, zorder=8)

    # Set the color of the outermost circle line
    ax.spines['polar'].set_color('#DDDDDD')

    plt.grid(axis='x', linestyle='-', alpha=0.4, zorder=9)

    # Draw peripheral category labels
    for i, label in enumerate(ax_x):
        angle = np.degrees(theta[i])
        ax.text(theta[i], text_top, label, ha='center', va='center', color='#1f1f1f', zorder=20, rotation=-angle + rotation if is_angle else rotation)

    # Adjust the layout to prevent label overlap
    plt.tight_layout()

    plot_end(fig, output, show)


def radar_trait(
    trait_df: DataFrame,
    trait_name: str = "All",
    trait_column_name: str = "id",
    value: str = "rate",
    clusters: str = "clusters",
    color: Union[collection, str] = None,
    clusters_sort: Optional[list] = None,
    width: float = 4,
    height: float = 4,
    rotation: float = 65,
    title: str = None,
    value_top: float = 0.1,
    text_top: float = 1.2,
    is_fixed: bool = False,
    is_angle: bool = True,
    y_limit: Tuple = (-0.5, 1),
    y_axis_scale: Tuple = (0, 1),
    output: path = None,
    show: bool = True,
    **kwargs: Any
):

    def trait_plot(trait_: str, cell_df_: DataFrame) -> None:
        """
        show plot
        :param trait_: trait name
        :param cell_df_:
        :return: None
        """
        ul.log(__name__).info("Plotting bar {}".format(trait_))
        trait_score = cell_df_[cell_df_[trait_column_name] == trait_]

        # Sort
        if clusters_sort is not None:
            trait_score[clusters] = pd.Categorical(trait_score[clusters], categories=clusters_sort, ordered=True)
            trait_score = trait_score.sort_values(by=clusters)
            ax_x = clusters_sort
        else:
            trait_score = trait_score.sort_values([value], ascending=False)
            ax_x = trait_score[clusters].tolist()

        colors = None
        if color is not None:
            if isinstance(color, str):
                if color in trait_score.columns:
                    colors = trait_score[color]
            elif isinstance(color, collection):
                colors = color

        radar(
            ax_x=ax_x,
            ax_y=trait_score[value].tolist(),
            title=f"{title} {trait_}" if title is not None else title,
            colors=colors,
            width=width,
            height=height,
            rotation=rotation,
            value_top=value_top,
            text_top=text_top,
            is_fixed=is_fixed,
            is_angle=is_angle,
            y_limit=y_limit,
            y_axis_scale=y_axis_scale,
            center_text=trait_,
            output=os.path.join(output, f"{trait_}_enrichment_radar.pdf") if output is not None else None,
            show=show,
            **kwargs
        )

    trait_list = list(set(trait_df[trait_column_name]))
    # judge trait
    if trait_name != "All" and trait_name not in trait_list:
        ul.log(__name__).error(
            f"The {trait_name} trait/disease is not in the trait/disease list {trait_list}, "
            f"Suggest modifying the {trait_column_name} parameter information"
        )
        raise ValueError(
            f"The {trait_name} trait/disease is not in the trait/disease list {trait_list}, "
            f"Suggest modifying the {trait_column_name} parameter information"
        )

    # plot
    if trait_name == "All":
        for trait in trait_list:
            trait_plot(trait_=trait, cell_df_=trait_df)
    else:
        trait_plot(trait_name, trait_df)
