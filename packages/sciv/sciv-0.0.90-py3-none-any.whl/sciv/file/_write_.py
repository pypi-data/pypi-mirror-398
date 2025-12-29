# -*- coding: UTF-8 -*-

import os.path
import pickle
from tqdm import tqdm
from pathlib import Path
from typing import Literal, Optional

import h5py
import pandas as pd
from pandas import DataFrame
from anndata import AnnData

from .. import util as ul
from ..util import path, to_sparse, chrtype, check_adata_get

__name__: str = "file_write"

_Field = Optional[Literal['real', 'complex', 'pattern', 'integer']]


def save_h5ad(data: AnnData, file: path) -> AnnData:
    """
    Save AnnData data
    :param data: data
    :param file: save file
    :return: AnnData file
    """
    ul.log(__name__).info("Saving data to {}".format(file))
    return data.write_h5ad(Path(file), compression='gzip')


def save_h5(data: dict, save_file: path, group_name: str = "matrix") -> None:
    """
    Save H5 data.
    :param data: data
    :param save_file: save file
    :param group_name: group name
    :return: H5 file
    """
    h5_dict = dict(data)

    file = h5py.File(f"{str(save_file)}", 'w')
    grp = file.create_group(group_name)

    for key, value in h5_dict.items():
        grp.create_dataset(key, data=value)

    file.close()


def save_pkl(data, save_file: path, is_verbose: bool = False) -> None:
    """
    Save pkl data.
    :param data: data
    :param save_file: save file
    :param is_verbose: Set true to print log;
    :return: pkl file
    """
    if is_verbose:
        ul.log(__name__).info("Saving data to {}".format(save_file))

    with open(str(save_file), 'wb') as f:
        pickle.dump(data, f) # type: ignore


def to_meta(
    adata: AnnData,
    dir_path: path,
    layer: str = None,
    feature_name: str = "peaks.bed",
    field: _Field = None
) -> None:
    """
    Convert AnnData data into metadata, i.e directory with matrix, bed file, etc.
    :param adata: input AnnData object;
    :param dir_path: Path for generating data;
    :param layer: The layer of data that needs to form meta files;
    :param feature_name: Feature file name;
    :param field: None or _Field;
        Either 'real', 'complex', 'pattern', or 'integer'.
    :return: Directory with matrix, bed file, etc.
    """

    dir_path = str(dir_path)
    ul.file_method(__name__).makedirs(dir_path)

    # Convert dense matrices to sparse matrices
    sparse_matrix = to_sparse(adata.layers[layer] if layer is not None else adata.X)
    # write mtx file
    ul.log(__name__).info(f"Write mtx file")
    import scipy.io as scio
    scio.mmwrite(os.path.join(dir_path, 'matrix.mtx'), sparse_matrix.T, field=field)

    # Cell annotation
    ul.log(__name__).info(f"Write cell annotation")
    cell_info: DataFrame = adata.obs
    cell_info["barcodes"] = adata.obs.index.to_list()
    cell_info.to_csv(
        os.path.join(dir_path, "annotation.txt"),
        index=False,
        sep="\t",
        lineterminator="\n",
        encoding="utf-8"
    )

    # barcodes
    ul.log(__name__).info(f"Write barcodes")
    barcodes = pd.DataFrame(adata.obs.index.to_list(), columns=["index"])
    barcodes.to_csv(
        os.path.join(dir_path, "barcodes.tsv"),
        index=False,
        header=False,
        sep="\t",
        lineterminator="\n",
        encoding="utf-8"
    )

    # feature
    ul.log(__name__).info(f"Write feature")
    feature_info: DataFrame = adata.var
    if feature_name.split(".")[0] == "peaks":
        feature = pd.DataFrame(feature_info.index.to_list(), columns=["index"])
        new_feature = feature["index"].astype(str).str.split("[:-]", expand=True)
        new_feature.to_csv(
            os.path.join(dir_path, feature_name),
            index=False,
            header=False,
            sep="\t",
            lineterminator="\n",
            encoding="utf-8"
        )
    else:
        feature = pd.DataFrame(feature_info.index.to_list(), columns=["index"])
        feature.to_csv(
            os.path.join(dir_path, feature_name),
            index=False,
            header=False,
            sep="\t",
            lineterminator="\n",
            encoding="utf-8"
        )


def to_fragments(
    adata: AnnData,
    fragments: str,
    layer: str = None,
    is_sort: bool = True,
    is_gz: bool = True,
    is_keep: bool = False
) -> None:
    """
    Convert AnnData format data into fragments format file.
    :param adata: input data;
    :param fragments: output file name;
    :param layer: The layer of data that needs to form fragments file;
    :param is_sort: If set to true, the output will be sorting of chromatin;
    :param is_gz: Whether to compress the formed file to gz;
        Compress fragments file using method `pysam.tabix_compress`.
    :param is_keep: Set to true, The `fragments.tsv` file will not be retained after compression;
        When is_gz is true, it takes effect.
    :return: fragments format file;
    """

    output_path = os.path.dirname(fragments)
    ul.file_method(__name__).makedirs(output_path)

    data = check_adata_get(adata=adata, layer=layer, is_dense=False, is_matrix=False).T

    # get group information
    data_obs: DataFrame = data.obs.copy()
    data_var: DataFrame = data.var.copy()

    if "chr" not in data_obs.columns or "start" not in data_obs.columns or "end" not in data_obs.columns:
        ul.log(__name__).error("`chr` or `start`or  `end` not in obs column")
        raise ValueError("`chr` or `start` or `end` not in obs column")

    if "barcodes" not in data_var.columns:
        ul.log(__name__).error(f"`barcodes` not in obs column")
        raise ValueError(f"`barcodes` not in obs column")

    if is_sort:
        ul.log(__name__).info("Sort chromatin")
        data_obs["chr"] = data_obs["chr"].astype(chrtype)
        data_obs.sort_values(["chr", "start"], inplace=True)
        source_row_size = data_obs.shape[0]
        data_obs.dropna(subset=['chr'])

        if source_row_size > data_obs.shape[0]:
            chrs_str = ",".join(list(chrtype.categories))
            ul.log(__name__).warning(f"The chromatin with `chr` not in `{chrs_str}` has been deleted here.")

        data = data[data_obs.index, :]

    matrix = to_sparse(data.X, is_matrix=False)

    row_size, col_size = data.shape
    row_range, col_range = range(row_size), range(col_size)

    # Convert to dictionary
    barcodes_dict: dict = dict(zip(list(col_range), data_var.index))
    peaks_dict: dict = dict(zip(list(row_range), zip(data_obs["chr"], data_obs["start"], data_obs["end"])))

    nonzero = matrix.nonzero()
    nonzero_size = nonzero[0].size
    ul.log(__name__).info(f"Get size {row_size, col_size} ===> nonzero size: {nonzero_size}")

    ul.log(__name__).info(f"Generate the `fragments` file {fragments}.")
    with open(fragments, mode="w", encoding="utf-8", newline="\n") as f:

        f.write(f"# output_file = {fragments}\n")
        f.write(f"# layer = {layer}\n")
        f.write(f"# features: {row_size}, barcodes: {col_size}, nonzero: {nonzero_size}\n")

        for row, col in tqdm(zip(nonzero[0], nonzero[1])):

            # info
            peaks = peaks_dict[row]
            barcodes = barcodes_dict[col]
            f.write(f"{peaks[0]}\t{peaks[1]}\t{peaks[2]}\t{barcodes}\t{matrix[row, col]}\n")

    if is_gz:
        is_success: bool = True

        try:
            ul.log(__name__).info(f"Generate the `fragments` file {fragments}.gz.")
            import pysam
            pysam.tabix_compress(fragments, f"{fragments}.gz", force=True)
        except Exception as e:
            is_success: bool = False
            ul.log(__name__).error(f"Compression of {fragments} file failed. \n {e}")

        if is_success and not is_keep:
            os.remove(fragments)
