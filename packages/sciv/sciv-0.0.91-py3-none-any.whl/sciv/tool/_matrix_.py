# -*- coding: UTF-8 -*-

import os
import pickle
import shutil
from typing import Union, Literal

import numpy as np
from scipy import sparse
from tqdm import tqdm

from ..file import save_pkl
from .. import util as ul
from ..util import (
    to_dense,
    to_sparse,
    sparse_matrix,
    matrix_data,
    generate_str,
    collection,
    file_method,
    number,
    dense_data
)

__name__: str = "tool_matrix"


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

    ul.log(__name__).info(f"Divide the matrix into {split_number} parts")

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
            ul.log(__name__).error("Inconsistent traits in the input dataset set.")
            raise ValueError("Inconsistent traits in the input dataset set.")

        total += shape[0] if axis == 0 else shape[1]
        shapes.append(shape)

    # format matrix
    matrix_shape = (total if axis == 0 else constant, constant if axis == 0 else total)
    ul.log(__name__).info(f"Merge matrix {matrix_shape} shape")
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


def down_sampling_data(data: Union[matrix_data | collection], sample_number: int = 1000000) -> list:
    """
    down-sampling
    :param data: Data that requires down-sampling;
    :param sample_number: How many samples (values) were down-sampled.
    :return: Data after down-sampling.
    """

    if isinstance(data, collection):

        # Judge data size
        if data.size <= sample_number:
            return list(data)

        index = np.random.choice(range(data.size), sample_number, replace=False)

        return list(np.array(data)[index])

    elif isinstance(data, matrix_data):

        # Judge data size
        if data.shape[0] * data.shape[1] <= sample_number:
            return list(to_dense(data, is_array=True).flatten())

        data = to_dense(data, is_array=True)
        row_count = data.shape[0]
        col_count = data.shape[1]

        if row_count < 0:
            ul.log(__name__).error("The number of rows of data must be greater than zero")
            raise ValueError("The number of rows of data must be greater than zero")

        ul.log(__name__).info(
            f"Kernel density estimation plot down-sampling data from {row_count * col_count} to {sample_number}"
        )

        # get count
        count = row_count * col_count
        iter_number: int = count // sample_number
        iter_sample_number: int = sample_number // iter_number
        iter_sample_number_final: int = sample_number % iter_number

        if iter_sample_number < 1:
            ul.log(__name__).error("The sampling data is too small, increase the `sample_number` parameter value")
            raise ValueError("The sampling data is too small, increase the `sample_number` parameter value")

        ul.log(__name__).info(f"Divide and conquer {iter_number} chunks")

        # Create index container
        return_data: list = []

        for i in range(iter_number + 1):

            if iter_number < 50:
                ul.log(__name__).info(f"Start {i + 1}th chunk, {(i + 1) / iter_number * 100}%")
            elif iter_number >= 50 and i % 50 == 0:
                ul.log(__name__).info(f"Start {i + 1}th chunk, {(i + 1) / iter_number * 100}%")

            # Determine if it is the last cycle
            end_count: int = count if i == iter_number else (i + 1) * sample_number

            if iter_sample_number_final == 0:
                index = np.random.choice(range(i * sample_number, end_count), iter_sample_number, replace=False)
            else:
                per_iter_sample_number: int = iter_sample_number_final if i == iter_number else iter_sample_number
                index = np.random.choice(range(i * sample_number, end_count), per_iter_sample_number, replace=False)

            # Add index
            for j in index:
                # row
                row_index = j // col_count
                # column
                col_index = j % col_count

                if row_index >= row_count:
                    ul.log(__name__).error(f"index ({row_index}) out of range ({row_count})")
                    raise IndexError(f"index ({row_index}) out of range ({row_count})")

                if col_index >= col_count:
                    ul.log(__name__).error(f"index ({col_index}) out of range ({col_count})")
                    raise IndexError(f"index ({col_index}) out of range ({col_count})")

                return_data.append(data[row_index, col_index])

        return return_data
    else:
        ul.log(__name__).error("The input data type is incorrect.")
        raise ValueError("The input data type is incorrect.")


def matrix_dot_block_storage(
    data1: matrix_data,
    data2: matrix_data,
    block_size: int = 10000,
    is_return_sparse: bool = False,
    data: matrix_data = None
) -> matrix_data:
    """
    Perform Cartesian product of two matrices through block storage method.
    :param data1: Matrix 1
    :param data2: Matrix 2
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed.
    :param is_return_sparse: Whether to return sparse matrix
    :param data: Return the placeholder variables of the result matrix.
        If there is value, it will reduce the consumption of memory space.
    :return: Cartesian product result
    """

    n, m = data1.shape
    p, q = data2.shape

    if m != p:
        ul.log(__name__).error(f"Need to meet the principle of matrix multiplication. ({m} != {p})")
        raise ValueError(f"Need to meet the principle of matrix multiplication. ({m} != {p})")

    if block_size <= 0 or n <= block_size and m <= block_size and q <= block_size:
        return to_sparse(np.dot(data1, data2)) if is_return_sparse else np.dot(data1, data2)

    n_range = range(0, n, block_size)
    q_range = range(0, q, block_size)
    m_range = range(0, m, block_size)

    _cache_path_ = os.path.join(ul.project_cache_path, generate_str(50))
    file_method(__name__).makedirs(_cache_path_)

    # Store block data
    ul.log(__name__).info("[matrix_dot_block_storage]: Store block data...")
    total_steps = len(n_range) * len(q_range) * len(m_range)
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for j in q_range:
                for k in m_range:
                    i_max = min(i + block_size, n)
                    j_max = min(j + block_size, q)
                    k_max = min(k + block_size, m)

                    _matrix_ = np.dot(data1[i:i_max, k:k_max], data2[k:k_max, j:j_max]).astype(np.float32)
                    save_pkl(_matrix_, os.path.join(_cache_path_, str(i) + str(j) + str(k) + ".pkl"))
                    del _matrix_

                    pbar.update(1)

    del data1, data2

    if data is None or data.shape != (n, q):
        data = sparse.lil_matrix((n, q)).astype(np.float32) if is_return_sparse else np.zeros((n, q)).astype(np.float32)

    # Read data
    ul.log(__name__).info("[matrix_dot_block_storage]: Read block data...")
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for j in q_range:
                for k in m_range:
                    i_max = min(i + block_size, n)
                    j_max = min(j + block_size, q)

                    with open(os.path.join(_cache_path_, str(i) + str(j) + str(k) + ".pkl"), 'rb') as f:
                        _matrix_ = pickle.load(f)
                        data[i:i_max, j:j_max] += _matrix_
                        del _matrix_

                    pbar.update(1)

    shutil.rmtree(_cache_path_)

    return data.tocsr() if is_return_sparse else data


def matrix_multiply_block_storage(
    data1: matrix_data,
    data2: matrix_data,
    block_size: int = 10000,
    data: matrix_data = None
) -> matrix_data:
    """
    Perform Hadamard product of two matrices through block storage method.
    :param data1: Matrix 1
    :param data2: Matrix 2
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed.
    :param data: Return the placeholder variables of the result matrix.
        If there is value, it will reduce the consumption of memory space.
    :return: Hadamard product result
    """
    n, m = data1.shape
    n1, m1 = data2.shape

    if n != n1 or m != m1:
        ul.log(__name__).error(
            f"Need to satisfy the multiplication principle of Hadamard products in matrices. ({(n, m)} != {n1, m1})"
        )
        raise ValueError(
            f"Need to satisfy the multiplication principle of Hadamard products in matrices. ({(n, m)} != {n1, m1})"
        )

    if block_size <= 0 or n <= block_size and m <= block_size:
        return np.multiply(data1, data2)

    n_range = range(0, n, block_size)
    m_range = range(0, m, block_size)

    _cache_path_ = os.path.join(ul.project_cache_path, generate_str(50))
    file_method(__name__).makedirs(_cache_path_)

    # Store block data
    ul.log(__name__).info("[matrix_multiply_block_storage]: Store block data...")
    total_steps = len(n_range) * len(m_range)
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for k in m_range:
                i_max = min(i + block_size, n)
                k_max = min(k + block_size, m)

                _matrix_ = np.multiply(data1[i:i_max, k:k_max], data2[i:i_max, k:k_max])
                save_pkl(_matrix_, os.path.join(_cache_path_, str(i) + str(k) + ".pkl"))
                del _matrix_

                pbar.update(1)

    del data1, data2

    if data is None or data.shape != (n, m):
        data = np.zeros((n, m))

    # Read data
    ul.log(__name__).info("[matrix_multiply_block_storage]: Read block data...")
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for k in m_range:
                i_max = min(i + block_size, n)
                k_max = min(k + block_size, m)

                with open(os.path.join(_cache_path_, str(i) + str(k) + ".pkl"), 'rb') as f:
                    _matrix_ = pickle.load(f)
                    data[i:i_max, k:k_max] += _matrix_
                    del _matrix_

                pbar.update(1)

    shutil.rmtree(_cache_path_)

    return data


def matrix_operation_memory_efficient(
    data1: matrix_data,
    data2: Union[matrix_data, number],
    chunk_size: int = 10000,
    default: float = 1e+8,
    operation: Literal['+', '-', '*', '/'] = '*'
) -> sparse_matrix:
    """
    Perform element-wise addition, subtraction, multiplication, and division on two sparse matrices by blocks, supporting memory-efficient processing.
    :param data1: Sparse matrix 1
    :param data2: Sparse matrix 2
    :param chunk_size: The size of the segmentation stored in block wise element-wise operation.
        If the value is less than or equal to zero, no block operation will be performed.
    :param default: 1e+8
    :param operation: Element-wise operation type, optional '+', '-', '*', '/'
    :return: Result sparse matrix (CSR format)
    """
    n, m = data1.shape

    if isinstance(data2, matrix_data):

        n1, m1 = data2.shape

        # Element-wise operations follow below
        if n != n1 or m != m1:
            ul.log(__name__).error(f"Need to satisfy the element-wise operation principle in matrices. ({(n, m)} != {n1, m1})")
            raise ValueError(f"Need to satisfy the element-wise operation principle in matrices. ({(n, m)} != {n1, m1})")
    else:

        if operation == "/" and data2 == 0:

            if default == 0:
                ul.log(__name__).error(f"The denominator (`data2`) cannot be zero.")
                raise ValueError(f"The denominator (`data2`) cannot be zero.")

            ul.log(__name__).warning(f"The denominator (`data2`) cannot be zero, it defaults to the `default` parameter value.")
            data2 = default

    if chunk_size <= 0:

        if operation == '+':

            if isinstance(data1, matrix_data):
                data2 = to_dense(data2) if isinstance(data1, dense_data) else to_sparse(data2)
                return data1 + data2
            else:
                data1.data = data1.data + data2
                return data1

        elif operation == '-':

            if isinstance(data1, matrix_data):
                data2 = to_dense(data2) if isinstance(data1, dense_data) else to_sparse(data2)
                return data1 - data2
            else:
                data1.data = data1.data - data2
                return data1

        elif operation == '*':

            if isinstance(data1, matrix_data):
                data2 = to_dense(data2) if isinstance(data1, dense_data) else to_sparse(data2)
                return data1.multiply(data2)
            else:
                data1.data = data1.data * data2
                return data1

        elif operation == '/':

            if isinstance(data1, matrix_data):
                data1 = to_dense(data1)
                data2 = to_dense(data2)
                data2[data2 == 0] = default
                return (data1 / data2) if isinstance(data1, dense_data) else to_sparse(data1 / data2)
            else:
                data1.data = data1.data / data2
                return data1

        else:
            ul.log(__name__).error(f"Unsupported operation: {operation}")
            raise ValueError(f"Unsupported operation: {operation}")

    if isinstance(data1, matrix_data):
        data2 = to_dense(data2) if isinstance(data1, dense_data) else to_sparse(data2)

    result = sparse.lil_matrix(data1.shape).astype(np.float32)

    for i in tqdm(range(0, data1.shape[0], chunk_size)):
        i_end = min(i + chunk_size, data1.shape[0])

        chunk1 = data1[i:i_end, :]

        if isinstance(data2, matrix_data):
            chunk2 = data2[i:i_end, :]
        else:
            chunk2 = data2

        if operation == '+':
            result_chunk = chunk1 + chunk2
        elif operation == '-':
            result_chunk = chunk1 - chunk2
        elif operation == '*':
            result_chunk = chunk1.multiply(chunk2)
        elif operation == '/':
            # Sparse matrix division: convert to dense, perform element-wise division, then convert back to sparse
            dense_chunk1 = chunk1 if isinstance(chunk1, dense_data) else chunk1.todense()

            if isinstance(data2, matrix_data):
                dense_chunk2 = chunk2 if isinstance(chunk2, dense_data) else chunk2.todense()
                dense_chunk2[dense_chunk2 == 0] = default
            else:
                dense_chunk2 = data2

            result_chunk = dense_chunk1 / dense_chunk2
            result_chunk = sparse.csr_matrix(result_chunk)
        else:
            ul.log(__name__).error(f"Unsupported operation: {operation}")
            raise ValueError(f"Unsupported operation: {operation}")

        result[i:i_end, :] = result_chunk

    return result.tocsr()


def vector_multiply_block_storage(
    data1: collection,
    data2: collection,
    block_size: int = 10000,
    data: matrix_data = None
) -> matrix_data:
    """
    Two vectors are broadcast in rows and columns respectively and multiplied by Hadamard product
    :param data1: Vector 1
    :param data2: Vector 2
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed.
    :param data: Return the placeholder variables of the result matrix.
        If there is value, it will reduce the consumption of memory space.
    :return: Matrix
    """

    vector1 = to_dense(data1, is_array=True).flatten()[:, np.newaxis]
    vector2 = to_dense(data2, is_array=True).flatten()

    del data1, data2

    n, _ = vector1.shape
    q = vector2.shape[0]

    if block_size <= 0 or n <= block_size and q <= block_size:
        return vector1 * vector2

    n_range = range(0, n, block_size)
    q_range = range(0, q, block_size)

    # block data
    ul.log(__name__).info("[vector_multiply_block_storage]: Block calculation...")

    if data is None or data.shape != (n, q):
        data = np.zeros((n, q))

    total_steps = len(n_range) * len(q_range)
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for j in q_range:
                i_max = min(i + block_size, n)
                j_max = min(j + block_size, q)

                data[i:i_max, j:j_max] += (vector1[i:i_max, :] * vector2[j:j_max]).astype(np.float32)

                pbar.update(1)

    del vector1, vector2

    return data


def matrix_division_block_storage(
    matrix: matrix_data,
    value: Union[float, int, collection, matrix_data],
    block_size: int = 10000,
    data: matrix_data = None
) -> matrix_data:
    """
    Dividing a matrix by another value, vector, or matrix.
    :param matrix: Matrix
    :param value: Value, vector, or matrix
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed.
    :param data: Return the placeholder variables of the result matrix.
        If there is value, it will reduce the consumption of memory space.
    :return: Matrix
    """

    n, m = matrix.shape

    is_status: int = -1

    if isinstance(value, collection):
        value = to_dense(value, is_array=True)
        q = value.shape[0]

        if q != n and q != m:
            ul.log(__name__).error(f"Inconsistent dimensions cannot be divided. {(n, m)} != {q}")
            raise ValueError(f"Inconsistent dimensions cannot be divided. {(n, m)} != {q}")

        is_status = 1 if n == q else 0
    elif isinstance(value, matrix_data):
        is_status = 2

    if block_size <= 0 or n <= block_size and m <= block_size:
        return matrix / value

    n_range = range(0, n, block_size)
    m_range = range(0, m, block_size)

    _cache_path_ = os.path.join(ul.project_cache_path, generate_str(50))
    file_method(__name__).makedirs(_cache_path_)

    # Store block data
    ul.log(__name__).info("[matrix_division_block_storage]: Store block data...")
    total_steps = len(n_range) * len(m_range)
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for k in m_range:
                i_max = min(i + block_size, n)
                k_max = min(k + block_size, m)

                if is_status == -1:
                    _matrix_ = matrix[i:i_max, k:k_max] / value
                elif is_status == 0:
                    _matrix_ = matrix[i:i_max, k:k_max] / value[k:k_max]
                elif is_status == 1:
                    _matrix_ = matrix[i:i_max, k:k_max] / value[i:i_max]
                elif is_status == 2:
                    _matrix_ = matrix[i:i_max, k:k_max] / value[i:i_max, k:k_max]
                else:
                    raise RuntimeError("nothingness")

                save_pkl(_matrix_, os.path.join(_cache_path_, str(i) + str(k) + ".pkl"))
                del _matrix_

                pbar.update(1)

    del matrix, value

    if data is None or data.shape != (n, m):
        data = np.zeros((n, m))

    # Read data
    ul.log(__name__).info("[matrix_division_block_storage]: Read block data...")
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for k in m_range:
                i_max = min(i + block_size, n)
                k_max = min(k + block_size, m)

                with open(os.path.join(_cache_path_, str(i) + str(k) + ".pkl"), 'rb') as f:
                    _matrix_ = pickle.load(f)
                    data[i:i_max, k:k_max] += _matrix_
                    del _matrix_

                pbar.update(1)

    shutil.rmtree(_cache_path_)

    return data


def matrix_callback_block_storage(
    matrix: matrix_data,
    callback,
    block_size: int = 10000,
    data: matrix_data = None
) -> matrix_data:
    """
    Dividing a matrix by another value, vector, or matrix.
    :param matrix: Matrix
    :param callback: callback function
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed.
    :param data: Return the placeholder variables of the result matrix.
        If there is value, it will reduce the consumption of memory space.
    :return: Matrix
    """

    n, m = matrix.shape

    n_range = range(0, n, block_size)
    m_range = range(0, m, block_size)

    if block_size <= 0 or n <= block_size and m <= block_size:
        return callback(matrix)

    _cache_path_ = os.path.join(ul.project_cache_path, generate_str(50))
    file_method(__name__).makedirs(_cache_path_)

    # Store block data
    ul.log(__name__).info("[matrix_callback_block_storage]: Store block data...")
    total_steps = len(n_range) * len(m_range)
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for k in m_range:
                i_max = min(i + block_size, n)
                k_max = min(k + block_size, m)

                _matrix_ = callback(matrix[i:i_max, k:k_max])

                save_pkl(_matrix_, os.path.join(_cache_path_, str(i) + str(k) + ".pkl"))
                del _matrix_

                pbar.update(1)

    del matrix

    if data is None or data.shape != (n, m):
        data = np.zeros((n, m))

    # Read data
    ul.log(__name__).info("[matrix_callback_block_storage]: Read block data...")
    with tqdm(total=total_steps) as pbar:
        for i in n_range:
            for k in m_range:
                i_max = min(i + block_size, n)
                k_max = min(k + block_size, m)

                with open(os.path.join(_cache_path_, str(i) + str(k) + ".pkl"), 'rb') as f:
                    _matrix_ = pickle.load(f)
                    data[i:i_max, k:k_max] += _matrix_
                    del _matrix_

                pbar.update(1)

    shutil.rmtree(_cache_path_)

    return data
