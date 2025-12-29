# -*- coding: UTF-8 -*-

from typing import Any

import numpy as np
import seaborn as sns
from pandas import DataFrame

from ..util import path, plot_end, plot_start

__name__: str = "plot_bubble"


def bubble(
    df: DataFrame,
    x: str,
    y: str,
    hue: str = None,
    size: str = None,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    width: float = 2,
    height: float = 2,
    bottom: float = 0,
    output: path = None,
    show: bool = True,
    **kwargs: Any
):

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    if size is not None:
        _size_ = df[size].values
        sizes = (np.array(_size_).min(), np.array(_size_).max())
    else:
        sizes = None

    sns.relplot(
        data=df,
        x=x,
        y=y,
        hue=hue,
        size=size,
        sizes=sizes,
        alpha=.5,
        palette="muted",
        height=6,
        **kwargs
    )

    plot_end(fig, output, show)
