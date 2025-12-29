# -*- coding: UTF-8 -*-

import math
import os
import random
import string
from typing import Tuple, Union, Literal

import numpy as np
import pandas as pd
import torch
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from numpy import asarray
from anndata import AnnData
from pandas import DataFrame
from scipy import sparse

from yzm_file import StaticMethod
from yzm_log import Logger

from .. import util as ul
from ._constant_ import dense_data, sparse_data, sparse_matrix, matrix_data, number, collection, project_name

__name__: str = "util_core"


def file_method(name: str = None) -> StaticMethod:
    name = f"{project_name}_{name}" if name is not None else project_name
    return StaticMethod(log_file=os.path.join(ul.log_file_path, name), is_form_log_file=ul.is_form_log_file)


def log(name: str = None) -> Logger:
    name = f"{project_name}_{name}" if name is not None else project_name
    return Logger(name, log_path=os.path.join(ul.log_file_path, name), is_form_file=ul.is_form_log_file)


def to_dense(sm: matrix_data, is_array: bool = False) -> dense_data:
    """
    Convert sparse matrix to dense matrix
    :param sm: sparse matrix
    :param is_array: True converted to array form, False natural output
    :return: dense matrix
    """

    if sm is None:
        log(__name__).warning("The input matrix (sm parameter) is not feasible")
        return np.asmatrix([])

    if isinstance(sm, sparse_data):
        return np.array(sm.todense()) if is_array else sm.todense()

    dense_sm = sm.todense() if sparse.issparse(sm) else sm
    return np.array(dense_sm) if is_array else dense_sm


def to_sparse(dm: dense_data, way_callback=sparse.csr_matrix, is_matrix: bool = True) -> sparse_matrix:
    """
    Convert dense matrix to sparse matrix
    :param dm: dense matrix
    :param way_callback: How to form sparse matrix
    :param is_matrix: True converted to matrix form, False natural output
    :return: sparse matrix
    """

    if dm is None:
        log(__name__).warning("The input matrix (dm parameter) is not feasible")
        return sparse.coo_matrix([])

    if isinstance(dm, dense_data):
        return way_callback(dm) if is_matrix else dm

    sparse_m = dm if sparse.issparse(dm) else way_callback(dm)
    return way_callback(sparse_m) if is_matrix else sparse_m


def sum_min_max(data: matrix_data, axis: int = 1) -> Tuple[number, number]:
    """
    Obtain the minimum/maximum sum of rows in the matrix
    :param data: matrix data
    :param axis: {0, 1} 1: row, 0: col
    :return: Minimum value of rows, maximum value of rows
    """
    rows, cols = data.shape

    if rows == 0 or cols == 0:
        return 0, 0

    rows_sum = list(np.array(data.sum(axis=axis)).flatten())
    return min(rows_sum), max(rows_sum)


def get_index(position: number, positions_list: list) -> Union[number, Tuple[number, number]]:
    """
    Search for position information. Similar to half search.
        If the position exists in the list, return the index.
        If it does not exist, return the index located between the two indexes
    :param position: position
    :param positions_list: position list
    :return: position index
    """
    # sort
    positions_list.sort()
    # search
    position_size: int = len(positions_list)
    left, right = 0, position_size - 1

    while left <= right:
        mid = (left + right) // 2

        if positions_list[mid] == position:
            return mid
        elif positions_list[mid] > position:
            right = mid - 1
        else:
            left = mid + 1

    return right, left


def list_duplicate_set(data: list) -> list:
    """
    Append numbering to duplicate information
    :param data: input data
    :return: Unique data with constant quantity
    """

    if len(data) == len(set(data)):
        return data

    new_data = []
    range_data = range(len(data))

    is_warn: bool = False

    for i in range_data:

        # judge duplicate
        if data[i] not in new_data:
            new_data.append(data[i])
        else:
            j: int = 2

            while True:

                if not isinstance(data[i], str) and not is_warn:
                    log(__name__).warning("Convert non string types to string types.")
                    is_warn = True

                # format new index
                elem: str = data[i] + "+" + str(j)

                # Add index
                if elem not in new_data:
                    new_data.append(elem)
                    break

                j += 1

    return new_data


def get_sub_data(data: collection, size: int) -> collection:
    # get information
    old_size = len(data)

    if size >= old_size:
        log(__name__).warning("The given size is greater than the original data size")
        return data

    old_data: list = data.copy()
    rate = size / old_size
    # add sub data
    new_data: list = []

    for i in range(size):
        new_data.append(old_data[math.floor(rate * i)])

    return new_data


def split_matrix(data: matrix_data, axis: Literal[0, 1] = 0, chunk_number: int = 1000) -> list:
    # get size
    new_data = to_dense(data, is_array=True)
    rows, cols = new_data.shape

    # get number
    total: int = rows if axis == 0 else cols

    # get split number
    split_number = total // chunk_number

    # Determine whether to divide equally
    tail_number = total % chunk_number
    if tail_number != 0:
        split_number += 1

    log(__name__).info(f"Divide the matrix into {split_number} parts")

    # Add data
    split_data_list = []
    for i in range(split_number):
        # set index
        start_index: int = i * chunk_number
        end_index: int = total if (i + 1) * chunk_number > total else (i + 1) * chunk_number
        split_data = new_data[start_index:end_index, :] if axis == 0 else new_data[:, start_index:end_index]
        split_data_list.append(split_data)

    return split_data_list


def merge_matrix(datas: list, axis: Literal[0, 1] = 0) -> list:
    # get size
    size = len(datas)
    range_size = range(size)

    # get row col
    constant: int = datas[0].shape[1] if axis == 0 else datas[0].shape[0]
    total: int = 0
    shapes: list = []

    # get chunk size
    for i in range_size:
        shape = datas[i].shape
        judge = shape[1] if axis == 0 else shape[0]

        # judge size
        if judge != constant:
            log(__name__).error("Inconsistent traits in the input dataset set.")
            raise ValueError("Inconsistent traits in the input dataset set.")

        total += shape[0] if axis == 0 else shape[1]
        shapes.append(shape)

    # format matrix
    matrix_shape = (total if axis == 0 else constant, constant if axis == 0 else total)
    log(__name__).info(f"Merge matrix {matrix_shape} shape")
    matrix: matrix_data = np.zeros(matrix_shape)

    # merge matrix
    col_record: int = 0
    for i in range_size:
        col_i = datas[i].shape[0] if axis == 0 else datas[i].shape[1]
        if axis == 0:
            matrix[col_record:col_record + col_i, :] = datas[i]
        else:
            matrix[:, col_record:col_record + col_i] = datas[i]
        col_record += col_i

    return matrix


def list_index(data: list) -> Tuple[list, collection]:
    info: list = []

    size: int = len(data)

    types: asarray = np.unique(data)

    for type_ in types:
        type_info: list = []
        for i in range(size):
            if type_ == data[i]:
                type_info.append(i)
        info.append(set(type_info))

    return info, types


def numerical_bisection_step(min_value: float, max_value: float, step_length: float) -> Tuple[collection, int]:
    if min_value > max_value:
        log(__name__).error(f"`min_value` ({min_value}) must be smaller than `max_value` ({max_value}).")
        raise ValueError(f"`min_value` ({min_value}) must be smaller than `max_value` ({max_value}).")

    number_list: list = []

    i = 0
    while min_value <= max_value:
        number_list.append(min_value)
        i += 1
        min_value += step_length

    return number_list, i


def get_real_predict_label(
    df: DataFrame,
    map_cluster: Union[str, collection],
    clusters: str = "clusters",
    value: str = "value"
) -> Tuple[DataFrame, int, list]:
    df_sort: DataFrame = df.sort_values([value], ascending=False)

    # Obtain the type of positive set clustering corresponding to the trait
    cluster_list: list = []
    if isinstance(map_cluster, str):
        cluster_list.append(map_cluster)
    else:
        cluster_list = list(map_cluster)

    # total label size
    total_size = df.shape[0]

    # true label size
    df_sort.insert(0, "true_label", 0)
    df_sort.loc[df_sort[df_sort[clusters].isin(cluster_list)].index, "true_label"] = 1

    # predict label size
    df_cluster = df[df[clusters].isin(cluster_list)].copy()
    df_cluster_size = df_cluster.shape[0]
    predict_label = list(np.ones(df_cluster_size))
    predict_label.extend(np.zeros(total_size - df_cluster_size))
    df_sort.insert(0, "predict_label", 0)
    df_sort.loc[:, "predict_label"] = predict_label
    df_sort["predict_label"] = df_sort["predict_label"].astype(int)

    return df_sort, df_cluster_size, cluster_list


def strings_map_numbers(str_list: list, start: int = 0) -> list:
    # Create an empty dictionary to store the mapping of strings to numerical values
    mapping = {}

    # Traverse the list and assign a unique numerical value to each string
    for i, item in enumerate(set(str_list), start=start):  # 使用set去除重复项，并从1开始编号
        mapping[item] = i

    # Use list derivation to convert strings to corresponding numerical values
    numeric_list = [mapping[item] for item in str_list]

    return numeric_list


def generate_str(length: int = 10) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def set_inf_value(matrix: matrix_data) -> None:
    # solve -Inf/Inf value
    matrix_inf = np.logical_and(np.isinf(matrix), matrix > 0)
    matrix__inf = np.logical_and(np.isinf(matrix), matrix < 0)

    # set inf
    if np.any(matrix_inf):
        matrix[matrix_inf] = np.max(matrix[~matrix_inf]) * 2

    # set -inf
    if np.any(matrix__inf):
        matrix[matrix__inf] = np.min(matrix[~matrix__inf]) / 2


def check_adata_get(adata: AnnData, layer: str = None, is_dense: bool = True, is_matrix: bool = False) -> AnnData:
    # judge input data
    if adata.shape[0] == 0:
        log(__name__).warning("Input data is empty")
        raise ValueError("Input data is empty")

    # get data
    data: AnnData = adata.copy()

    # judge layers
    if layer is not None:
        if layer not in list(data.layers):
            log(__name__).error("The value of the `layer` parameter must be one of the keys in `adata.layers`.")
            raise ValueError("The value of the `layer` parameter must be one of the keys in `adata.layers`.")

        data.X = to_dense(data.layers[layer], is_array=True) if is_dense \
            else to_sparse(data.layers[layer], is_matrix=is_matrix)
    else:
        data.X = to_dense(data.X, is_array=True) if is_dense else to_sparse(data.X, is_matrix=is_matrix)

    return data


def add_cluster_info(data: DataFrame, data_ref: DataFrame, cluster: str) -> DataFrame:
    new_data: DataFrame = data.copy()
    if data_ref is not None and cluster not in new_data.columns:

        new_data: DataFrame = pd.merge(new_data, data_ref, how="left", left_index=True, right_index=True)

        if "barcode_x" in new_data.columns:
            new_data["barcode"] = new_data["barcode_x"]
            new_data.drop("barcode_x", axis=1, inplace=True)

            if "barcode_y" in new_data.columns:
                new_data.drop("barcode_y", axis=1, inplace=True)

        if "barcodes_x" in new_data.columns:
            new_data["barcodes"] = new_data["barcodes_x"]
            new_data.drop("barcodes_x", axis=1, inplace=True)

            if "barcodes_y" in new_data.columns:
                new_data.drop("barcodes_y", axis=1, inplace=True)

    if cluster not in new_data.columns:
        log(__name__).error(f"`{cluster}` is not in `adata.obs.columns`.")
        raise ValueError(f"`{cluster}` is not in `columns` ({new_data.columns}).")

    return new_data


def check_gpu_availability(verbose: bool = True) -> bool:
    available = torch.cuda.is_available()

    if verbose:

        if available:
            log(__name__).info("GPU is available.")
            log(__name__).info(f"Number of GPUs: {torch.cuda.device_count()}")
            log(__name__).info(f"GPU Name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
        else:
            log(__name__).info("GPU is not available.")

    return available


def plot_start(
    title: str = None,
    x_name: str = None,
    y_name: str = None,
    width: float = 2,
    height: float = 2,
    bottom: float = 0,
    output: str = None,
    show: bool = True
):
    if output is None and not show:
        ul.log(__name__).error(f"At least one of the `output` and `show` parameters is required")
        raise ValueError(f"At least one of the `output` and `show` parameters is required")

    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(bottom=bottom)

    if title is not None:
        plt.title(title)

    if x_name is not None:
        plt.xlabel(x_name, rotation=0)

    if y_name is not None:
        plt.xlabel(y_name, rotation=90)

    return fig, ax


def plot_end(fig, output: str, show: bool, dpi: float = 300):
    if output is not None:

        if output.endswith(".pdf"):

            with PdfPages(output) as pdf:
                pdf.savefig(fig)

        elif output.endswith(".png") or output.endswith(".jpg"):
            plt.savefig(output, dpi=dpi)
        else:
            plt.savefig(f"{output}.png", dpi=dpi)

    if show:
        plt.show()

    plt.close()


def generate_hex_colors(num_colors):
    colors = []

    while len(colors) < num_colors:
        color = "#{:02X}{:02X}{:02X}".format(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        colors.append(color)

    return colors
