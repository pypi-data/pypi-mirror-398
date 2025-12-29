# -*- coding: UTF-8 -*-

from typing import Literal, Any

import numpy as np
from anndata import AnnData
import seaborn as sns
from tqdm import tqdm

from .. import util as ul
from ..tool import down_sampling_data
from ..util import path, check_adata_get, plot_end, plot_start

__name__: str = "plot_kde"


def kde(
    adata: AnnData,
    layer: str = None,
    x_name: str = None,
    y_name: str = None,
    title: str = None,
    width: float = 4,
    height: float = 2,
    bottom: float = 0.3,
    axis: Literal[-1, 0, 1] = -1,
    sample_number: int = 1000000,
    is_legend: bool = True,
    output: path = None,
    show: bool = True,
    **kwargs: Any
) -> None:
    ul.log(__name__).info("Start plotting the Kernel density estimation chart")

    fig, ax = plot_start(title, x_name, y_name, width, height, bottom, output, show)

    data = check_adata_get(adata, layer=layer, is_dense=True, is_matrix=False)

    sns.set_theme(style="whitegrid")

    # Random sampling
    if axis == -1:
        matrix = down_sampling_data(data.X, sample_number)
        sns.kdeplot(matrix, shade=True, fill=True)
    elif axis == 0:
        col_number = data.shape[1]
        if data.shape[0] * data.shape[1] > sample_number:
            row_number: int = sample_number // col_number

            for i in tqdm(range(col_number)):
                _vector_ = down_sampling_data(data.X[:, i], row_number)
                sns.kdeplot(np.array(_vector_).flatten(), shade=True, fill=True, **kwargs)
        else:
            for i in tqdm(range(col_number)):
                sns.kdeplot(np.array(data.X[:, i]).flatten(), shade=True, fill=True, **kwargs)

        if is_legend:
            ax.legend(list(adata.var.index))

    elif axis == 1:
        row_number = data.shape[0]
        if data.shape[0] * data.shape[1] > sample_number:
            col_number: int = sample_number // row_number

            for i in tqdm(range(row_number)):
                _vector_ = down_sampling_data(data.X[i, :], col_number)
                sns.kdeplot(np.array(_vector_).flatten(), shade=True, fill=True, **kwargs)
        else:
            for i in tqdm(range(row_number)):
                sns.kdeplot(np.array(data.X[i, :]).flatten(), shade=True, fill=True, **kwargs)

        if is_legend:
            ax.legend(list(adata.obs.index))

    plot_end(fig, output, show)
