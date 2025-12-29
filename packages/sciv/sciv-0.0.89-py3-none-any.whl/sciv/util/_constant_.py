# -*- coding: UTF-8 -*-

import os
from typing import Union, Tuple, Literal
from pathlib import Path

import matplotlib
from numpy import ndarray, matrix
from pandas import CategoricalDtype
from matplotlib import rcParams, colormaps
from matplotlib.colors import ListedColormap
from PyComplexHeatmap import colors

from scipy.sparse import (
    coo_matrix,
    csr_matrix,
    csc_matrix,
    dok_matrix,
    lil_matrix,
    bsr_matrix,
    dia_matrix,
    spmatrix,
    coo_array,
    csr_array,
    csc_array,
    dok_array,
    lil_array,
    bsr_array,
    dia_array,
    sparray
)

project_version = "0.0.1"
project_name = "SCIV"

user_path = os.path.expanduser("~")
project_cache_path: str = os.path.join(user_path, ".cache", project_name)

is_form_log_file: bool = False
log_file_path: str = os.path.join(project_cache_path, "log")

matplotlib.set_loglevel("error")

path = Union[str, Path]
number = Union[int, float]
collection = Union[list, set, Tuple, ndarray]

sparse_array = Union[coo_array, csr_array, csc_array, dok_array, lil_array, bsr_array, dia_array, sparray]
sparse_matrix = Union[coo_matrix, csr_matrix, csc_matrix, dok_matrix, lil_matrix, bsr_matrix, dia_matrix, spmatrix]

sparse_data = Union[sparse_array, sparse_matrix]
dense_data = Union[ndarray, matrix, list]

matrix_data = Union[sparse_data, dense_data]

enrichment_optional = Literal['golden', 'half', 'e', 'pi', 'none']
difference_peak_optional = Literal['emp_effect', 'bayes_factor', 'emp_prob1', 'all']

plot_rc_config = {
    "font.family": 'Arial',
    "axes.labelsize": 7,
    "font.size": 7,
    "legend.fontsize": 7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False
}
rcParams.update(plot_rc_config)

colors.define_cmap()
type_50_colors = colormaps.get("cmap50").colors.copy()
plot_cmap_50 = ListedColormap(type_50_colors)

type_20_colors = list(colormaps.get("tab20").colors).copy()
plot_cmap_20 = ListedColormap(type_20_colors)

type_set_colors = [
    "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#f4d037",
    "#e5c494", "#f2f0a7", "#9a60b4", "#c16772", "#c1c167", "#b3b3b3",
    "#4b0082", "#cd853f", "#008080", "#808000", "#ff00ff", "#2f4f4f",
    "#d3b48b", "#8b4513", "#7fff00", "#ff69b4", "#66cdaa", "#a52a2a",
    "#daa520"
]
plot_cmap_set = ListedColormap(type_set_colors)

plot_color_types: dict = {
    "20": type_20_colors,
    "50": type_50_colors,
    "set": type_set_colors
}

chrtype = CategoricalDtype(
    [
        "chr1",
        "chr2",
        "chr3",
        "chr4",
        "chr5",
        "chr6",
        "chr7",
        "chr8",
        "chr9",
        "chr10",
        "chr11",
        "chr12",
        "chr13",
        "chr14",
        "chr15",
        "chr16",
        "chr17",
        "chr18",
        "chr19",
        "chr20",
        "chr21",
        "chr22",
        "chrX",
        "chrY"
    ],
    ordered=True
)
