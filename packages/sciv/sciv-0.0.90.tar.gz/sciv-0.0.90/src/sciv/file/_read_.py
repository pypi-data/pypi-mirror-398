# -*- coding: UTF-8 -*-

import os
import pickle
import warnings
from pathlib import Path
from typing import Tuple, Optional

import h5py
import numpy as np
import pandas as pd
import anndata as ad
from tqdm import tqdm
from anndata import AnnData
from pandas import DataFrame

from .. import util as ul
from ..util import path, to_sparse, list_duplicate_set, collection, project_name, project_version

__name__: str = "file_read"


def read_h5ad(file: path, is_verbose: bool = True) -> AnnData:
    """
    Read AnnData data.
    :param file: file path;
    :param is_verbose: Set true to print log;
    :return: AnnData data.
    """
    if is_verbose:
        ul.log(__name__).info("Reading AnnData file: {}".format(file))

    return ad.read_h5ad(Path(file))


def read_h5(file: path, is_close: bool = False):
    """
    Read AnnData data
    :param file: file path
    :param is_close: file path
    :return: AnnData data
    """
    file = h5py.File(file, 'r')
    keys = file.keys()

    if is_close:
        file.close()

    return keys, file


def read_pkl(file: path, is_verbose: bool = True):
    """
    Read pkl data
    :param file: file path
    :param is_verbose: Set true to print log;
    :return: Python variable data
    """
    if is_verbose:
        ul.log(__name__).info("Reading pkl file: {}".format(file))

    # Recovering variables from files
    with open(str(file), 'rb') as f:
        data = pickle.load(f)

    return data


def handle_file_data_cell(
    file: path,
    clusters: str = "clusters",
    barcode_split_character: str = '-',
    on_barcode_split_character: str = None,
    is_transpose: bool = True,
    cluster_anno_file: path = None
) -> Tuple[DataFrame, DataFrame]:
    """
    Read table file to generate AnnData format data.
    :param file: A table with cell or peak column and column indexes, and the content is the number of fragments;
    :param clusters: The column name for cell clusters or cell types. (In most cases, this column can be ignored.)
        It is worth noting that only the values in this column are judged to determine whether they contain NA values;
        If they do, they are assigned the value `unknown`, and if not, no operation is performed;
    :param barcode_split_character: A barcode separated character symbol. (meta)
    :param on_barcode_split_character: A barcode separated character symbol. (matrix)
    :param is_transpose: Whether transpose is required to read the matrix file, default to True;
    :param cluster_anno_file: The file that adds information about cells must contain the column name `barcodes`;
    :return: Cell annotation data, counts data.
    """

    if file is None:
        ul.log(__name__).error("File cannot be empty")
        raise ValueError("File cannot be empty")

    if on_barcode_split_character is None:
        on_barcode_split_character = barcode_split_character

    data = pd.read_table(file, header=0)
    data = data.T if is_transpose else data
    # format barcodes information
    ul.log(__name__).info("handle cells information")
    cell_annot = pd.DataFrame(data=np.matrix(data.index).T, columns=["barcodes"])
    content_split_size = len(str(list(data.index)[0]).split(barcode_split_character))

    if content_split_size == 1:
        ul.log(__name__).info(f"Barcode does not contain a separator `{barcode_split_character}`")
        cell_annot["barcode"] = cell_annot["barcodes"]
    else:
        cell_annot: DataFrame = cell_annot["barcodes"].astype('str').str.split(barcode_split_character, expand=True)
        cell_annot.columns = ["barcode", "batch_id"]
        cell_annot["barcodes"] = (
            cell_annot["barcode"].astype(str)
            + on_barcode_split_character
            + cell_annot["batch_id"].astype(str)
        )

    # add annotation file
    if cluster_anno_file is not None:
        cell_annot = barcodes_add_anno(cluster_anno_file, cell_annot, clusters=clusters)

    cell_annot.index = cell_annot["barcode"].astype(str)
    return cell_annot, data


def barcodes_add_anno(annotation_file: path, cell_anno: DataFrame, clusters: str = None) -> DataFrame:
    """
    Add user inputted cell information
    :param annotation_file: The file that adds information about cells must contain the column name `barcodes`, the file input by the user.
    :param cell_anno: Read the cell description in the scATAC-seq data generated from the file.
    :param clusters: The column name for cell clusters or cell types. (In most cases, this column can be ignored.)
        It is worth noting that only the values in this column are judged to determine whether they contain NA values.
        If they do, they are assigned the value `unknown`, and if not, no operation is performed.
    :return: Complete cell annotation data
    """
    ul.log(__name__).info("Add annotation file")
    # add annotation file
    cell_annotation_file: DataFrame = pd.read_table(annotation_file, sep="\t", header=0, index_col=None)

    # judge column
    if "barcodes" not in list(cell_annotation_file.columns):
        ul.log(__name__).error("The annotation file must contain a column name with `barcodes`")
        raise ValueError("The annotation file must contain a column name with `barcodes`")

    if "barcodes" not in list(cell_anno.columns):
        ul.log(__name__).error("The `cell_anno` must contain a column name with `barcodes`")
        raise SyntaxError("The `cell_anno` must contain a column name with `barcodes`")

    if len(cell_anno["barcodes"]) > len(set(cell_annotation_file["barcodes"])):
        ul.log(__name__).error("Insufficient number of barcodes in the annotation file.")
        raise SyntaxError("Insufficient number of barcodes in the annotation file.")

    cell_anno = cell_anno.merge(cell_annotation_file, on="barcodes", how="inner")

    if clusters is not None:
        if clusters not in list(cell_annotation_file.columns):
            ul.log(__name__).error(f"The comment file must contain a column name with `{clusters}`, Try changing the `clusters` parameter")
            raise ValueError(f"The comment file must contain a column name with `{clusters}`, Try changing the `clusters` parameter")

        if clusters not in list(cell_anno.columns):
            cell_anno = cell_anno.rename(columns={f"{clusters}_y": clusters})

        # nan set unknown
        if cell_anno[cell_anno[clusters].isna()].shape[0] > 0:
            ul.log(__name__).warning(f"Due to the presence of `NA` in the `{clusters}`, it is forcibly assigned as `unknown`.")
            cell_anno.loc[cell_anno[clusters].isna(), clusters] = "unknown"

    if "barcode" not in list(cell_anno.columns):
        cell_anno = cell_anno.rename(columns={"barcode_x": "barcode"})

    cell_anno.index = cell_anno["barcode"].astype(str)
    return cell_anno


def read_barcodes_file(
    barcodes_file: path,
    clusters: str = None,
    barcode_split_character: str = '-',
    annotation_file: path = None,
) -> DataFrame:
    ul.log(__name__).info("handle cells information")
    # read file
    cell_anno = pd.read_csv(barcodes_file, header=None, index_col=None)
    content_split_size = len(str(cell_anno[0][1]).split(barcode_split_character))

    if content_split_size == 1:
        ul.log(__name__).info(f"Barcode does not contain a separator `{barcode_split_character}`")

    # judge
    if cell_anno.shape[0] != np.unique(cell_anno[0]).size:
        ul.log(__name__).error("Barcodes cannot have duplicate barcodes in the barcodes file")
        raise ValueError("Barcodes cannot have duplicate barcodes in the barcodes file")

    if barcode_split_character is None or content_split_size == 1:
        cell_anno.rename({0: "barcode"}, axis="columns", inplace=True)
        cell_anno["barcodes"] = cell_anno["barcode"].astype(str)
    else:
        __cell_annot__ = pd.read_csv(barcodes_file, sep=barcode_split_character, header=None, index_col=None)

        __is_with__ = True

        # judge
        if len(__cell_annot__.columns) == 1:
            ul.log(__name__).warning("Parameter `barcode_split_character` is `-`, but it is not working, ignore.")
            __is_with__ = False

        if __cell_annot__.shape[0] != np.unique(__cell_annot__[0]).size:
            ul.log(__name__).info("After extracting `batch_id`, there are duplicate barcodes, so `batch_id` is not extracted.")
            __is_with__ = False

        if __is_with__:
            cell_anno = __cell_annot__
            cell_anno.rename({0: "barcode", 1: "batch_id"}, axis="columns", inplace=True)
            cell_anno["barcodes"] = cell_anno["barcode"].astype(str) + "-" + cell_anno["batch_id"].astype(str)
        else:
            cell_anno.rename({0: "barcode"}, axis="columns", inplace=True)
            cell_anno["barcodes"] = cell_anno["barcode"].astype(str)

    # add annotation file
    if annotation_file is not None:
        cell_anno = barcodes_add_anno(annotation_file, cell_anno, clusters=clusters)

    cell_anno.set_index("barcode", inplace=True, drop=False)
    cell_anno.index = cell_anno.index.astype(str)
    return cell_anno


def _read_info_by_metadata_(
    base_path: path,
    feature_file_name: str,
    is_transpose: bool = True,
    clusters: str = None,
    barcode_split_character: str = '-',
    annotation_file: path = None,
) -> AnnData:
    """
    Read metadata outputted by 10x Genomics software.
    :param base_path: Path to directory with matrix, bed file, etc. (It can be obtained through cell-ranger)
    :param feature_file_name: feature file name;
    :param is_transpose: Whether transpose is required to read the matrix file, default to True;
    :param clusters: The column name for cell clusters or cell types. (In most cases, this column can be ignored.)
        It is worth noting that only the values in this column are judged to determine whether they contain NA values;
        If they do, they are assigned the value `unknown`, and if not, no operation is performed;
    :param barcode_split_character: A barcode separated character symbol. (meta)
    :param annotation_file: The file that adds information about cells must contain the column name `barcodes`;
    :return: sequence data
    """
    # read features file
    ul.log(__name__).info("handle features information")
    coords = pd.read_table(os.path.join(base_path, feature_file_name), header=None, index_col=None)
    coords.rename({0: "chr", 1: "start", 2: "end"}, axis="columns", inplace=True)
    coords.set_index(
        coords.chr.astype(str) + ":" + coords.start.astype(str) + "-" + coords.end.astype(str),
        inplace=True
    )
    coords.index = coords.index.astype(str)

    # read barcodes file
    cell_annot = read_barcodes_file(
        os.path.join(base_path, "barcodes.tsv"),
        clusters=clusters,
        barcode_split_character=barcode_split_character,
        annotation_file=annotation_file
    )

    from scipy.io import mmread

    # read matrix file
    ul.log(__name__).info("read `matrix.mtx` file")
    data = mmread(os.path.join(base_path, "matrix.mtx")).transpose() if is_transpose else \
        mmread(os.path.join(base_path, "matrix.mtx"))

    return AnnData(data.tocsr(), var=coords, obs=cell_annot)


def _process_peaks_(
    data: collection,
    peak_split_character: Tuple = (":", "-")
) -> Tuple[DataFrame, list, list, list]:
    """
    Processing peak set.
    :param data: Input peak set;
    :param peak_split_character: The connection symbol between chromosome, start and end;
    :return: Peak information, chromosome list, start position list, end position list.
    """
    # format peaks information
    ul.log(__name__).info("handle peaks information")
    features = pd.DataFrame(columns=["chr", "start", "end"])
    chr_list: list = []
    start_list: list = []
    end_list: list = []

    if peak_split_character[0] == peak_split_character[1]:
        character_ = peak_split_character[0]

        for col in list(data):
            col: str
            split: list = col.split(character_)
            chr_list.append(split[0])
            start_list.append(int(split[1]))
            end_list.append(int(split[2]))
    else:

        for col in list(data):
            col: str
            split: list = col.split(peak_split_character[0])
            chr_list.append(split[0])
            split2: list = split[1].split(peak_split_character[1])
            start_list.append(int(split2[0]))
            end_list.append(int(split2[1]))

    features["chr"] = chr_list
    features["start"] = start_list
    features["end"] = end_list
    features.set_index(
        features.chr.astype(str) + ":" + features.start.astype(str) + "-" + features.end.astype(str),
        inplace=True
    )
    features.index = features.index.astype(str)

    return features, chr_list, start_list, end_list


def collect_datasets(dsets: dict, group: h5py.Group):
    for k, v in group.items():
        if isinstance(v, h5py.Dataset):
            dsets[k] = v[()]
        else:
            collect_datasets(dsets, v)


def read_v3_10x_h5(filename: path) -> AnnData:
    """
    Read hdf5 file from Cell Ranger v3 or later versions.
    :param filename: H5 file
    :return: scATAC-seq data
    """
    ul.log(__name__).info('Start read hdf5 file')
    with h5py.File(str(filename), 'r') as f:
        try:
            dsets = {}
            collect_datasets(dsets, f["matrix"])

            from scipy.sparse import csr_matrix

            m, n = dsets['shape']
            data = dsets['data']
            if dsets['data'].dtype == np.dtype('int32'):
                data = dsets['data'].view('float32')
                data[:] = dsets['data']
            matrix = csr_matrix(
                (data, dsets['indices'], dsets['indptr']),
                shape=(n, m),
            )
            adata = AnnData(
                matrix,
                obs=dict(obs_names=dsets['barcodes'].astype(str)),
                var=dict(
                    var_names=dsets['name'].astype(str),
                    peak_ids=dsets['id'].astype(str),
                    feature_types=dsets['feature_type'].astype(str),
                    genome=dsets['genome'].astype(str),
                ),
            )
            return adata
        except KeyError:
            raise Exception('File is missing one or more required datasets.')


def read_sc_atac_10x_h5(
    file: path,
    clusters: str = None,
    barcode_split_character: str = '-',
    annotation_file: path = None,
    peak_split_character: Tuple = (":", "-")
) -> AnnData:
    """
    Read hdf5 file from Cell Ranger v3 or later versions.
    :param file: A comprehensive h5ad file. (It can be obtained through cell-ranger)
    :param clusters: The column name for cell clusters or cell types. (In most cases, this column can be ignored.)
        It is worth noting that only the values in this column are judged to determine whether they contain NA values.
        If they do, they are assigned the value `unknown`, and if not, no operation is performed.
    :param barcode_split_character: A barcode separated character symbol (meta)
    :param annotation_file: The file that adds information about cells must contain the column name `barcodes`
    :param peak_split_character: A peak separated character symbol
    :returns: scATAC-seq data
    """
    ul.log(__name__).info("Reading scATAC-seq 10x data")
    sc_atac: AnnData = read_v3_10x_h5(file)
    # cell information
    cells = sc_atac.obs.copy()
    barcodes = list(cells.index)
    cells["barcodes"] = barcodes

    # Add bath
    if len(str(barcodes[0]).split(barcode_split_character)) == 2:
        barcode_list: list = []
        batch_id_list: list = []

        for barcode in barcodes:
            barcode: str
            barcode_list.append(barcode.split(barcode_split_character)[0])
            batch_id_list.append(barcode.split(barcode_split_character)[1])

        cells["barcode"] = barcode_list
        cells["batch_id"] = batch_id_list
    else:
        cells["barcode"] = barcodes

    # add annotation file
    if annotation_file is not None:
        cells = barcodes_add_anno(annotation_file, cells, clusters=clusters)

    sc_atac.obs = cells

    # peak information
    peaks: DataFrame = sc_atac.var.copy()
    # format peaks information
    _, chr_list, start_list, end_list = _process_peaks_(peaks.index, peak_split_character)
    peaks["chr"] = chr_list
    peaks["start"] = start_list
    peaks["end"] = end_list
    sc_atac.var = peaks

    return sc_atac


def read_sc_atac(
    resource: path = None,
    is_transpose: bool = True,
    barcode_split_character: str = '-',
    on_barcode_split_character: str = None,
    annotation_file: path = None,
    clusters: str = None,
    peak_split_character: Tuple = (":", "-")
) -> AnnData:
    """
    Return scATAC-seq data in AnnData format.
    :param resource:
        1. Path to directory with matrix, bed file, etc. (It can be obtained through cell-ranger)
        2. H5 file obtained through cell-ranger.
        3. A comprehensive h5ad file.
        4. A table with cell or peak column and column indexes, and the content is the number of fragments;
    :param is_transpose: Whether transpose is required to read the matrix file, default to True;
    :param barcode_split_character: A barcode separated character symbol. (meta)
    :param on_barcode_split_character: A barcode separated character symbol. (matrix)
    :param annotation_file: The file that adds information about cells must contain the column name `barcodes`;
    :param clusters: The column name for cell clusters or cell types. (In most cases, this column can be ignored.)
        It is worth noting that only the values in this column are judged to determine whether they contain NA values;
        If they do, they are assigned the value `unknown`, and if not, no operation is performed;
    :param peak_split_character: A peak separated character symbol;
    :return: scATAC-seq data.
    """
    ul.log(__name__).info("Read scATAC-seq data")

    is_metadata: bool = os.path.isdir(str(resource))

    if is_metadata:

        sc_atac: AnnData = _read_info_by_metadata_(
            base_path=resource,
            feature_file_name="peaks.bed",
            is_transpose=is_transpose,
            clusters=clusters,
            barcode_split_character=barcode_split_character,
            annotation_file=annotation_file
        )

    else:

        if str(resource).endswith(".h5"):
            sc_atac: AnnData = read_sc_atac_10x_h5(
                file=resource,
                barcode_split_character=barcode_split_character,
                peak_split_character=peak_split_character
            )

            # add annotation file
            if annotation_file is not None:
                cell_annot = sc_atac.obs.copy()
                cell_annot = barcodes_add_anno(annotation_file, cell_annot, clusters=clusters)
                sc_atac.obs = cell_annot

        elif str(resource).endswith(".h5ad"):
            sc_atac: AnnData = read_h5ad(file=resource)

            peak_col: list = list(sc_atac.var.columns)
            barcode_col: list = list(sc_atac.obs.columns)

            if "chr" not in peak_col or "start" not in peak_col or "end" not in peak_col:
                _, chr_list, start_list, end_list = _process_peaks_(list(sc_atac.var_names), peak_split_character)

                if len(peak_split_character) != 2:
                    ul.log(__name__).error(
                        "The peak feature is used to obtain the segmentation character of `chr` `start` `end`, "
                        "which requires two characters. The first character is used to segment `chr` and `start`, "
                        "and the second character is used to segment `start` and `end`"
                    )
                    raise ValueError(
                        "The peak feature is used to obtain the segmentation character of `chr` `start` `end`, "
                        "which requires two characters. The first character is used to segment `chr` and `start`, "
                        "and the second character is used to segment `start` and `end`"
                    )

                sc_atac.var["chr"] = chr_list
                sc_atac.var["start"] = start_list
                sc_atac.var["end"] = end_list

            if "barcode" not in barcode_col and "barcodes" in barcode_col:
                sc_atac.obs["barcode"] = sc_atac.obs["barcodes"]
            elif "barcode" in barcode_col and "barcodes" not in barcode_col:
                sc_atac.obs["barcodes"] = sc_atac.obs["barcode"]
            elif "barcode" not in barcode_col and "barcodes" not in barcode_col:
                sc_atac.obs["barcode"] = sc_atac.obs_names
                sc_atac.obs["barcodes"] = sc_atac.obs_names

            # add annotation file
            if annotation_file is not None:
                cell_annot = sc_atac.obs.copy()
                cell_annot = barcodes_add_anno(annotation_file, cell_annot, clusters=clusters)
                sc_atac.obs = cell_annot

        else:
            if len(peak_split_character) != 2:
                ul.log(__name__).error(
                    "The peak feature is used to obtain the segmentation character of `chr` `start` `end`, "
                    "which requires two characters. The first character is used to segment `chr` and `start`, "
                    "and the second character is used to segment `start` and `end`"
                )
                raise ValueError(
                    "The peak feature is used to obtain the segmentation character of `chr` `start` `end`, "
                    "which requires two characters. The first character is used to segment `chr` and `start`, "
                    "and the second character is used to segment `start` and `end`"
                )

            cell_annot, data = handle_file_data_cell(
                file=resource,
                clusters=clusters,
                barcode_split_character=barcode_split_character,
                on_barcode_split_character=on_barcode_split_character,
                is_transpose=is_transpose,
                cluster_anno_file=annotation_file
            )

            # format peaks information
            features, _, _, _ = _process_peaks_(data.columns, peak_split_character)
            sc_atac = AnnData(to_sparse(data.values), var=features, obs=cell_annot)

    # Add project
    sc_atac.uns["project_name"] = project_name
    sc_atac.uns["project_version"] = project_version
    # save params information
    sc_atac.uns["params"] = {
        "resource": resource,
        "is_transpose": is_transpose,
        "clusters": clusters,
        "barcode_split_character": barcode_split_character,
        "on_barcode_split_character": on_barcode_split_character,
        "annotation_file": annotation_file,
        "peak_split_character": {
            "chr_start_split_symbal": peak_split_character[0],
            "start_end_split_symbal": peak_split_character[1]
        },
        "is_metadata": is_metadata
    }

    return sc_atac


def read_variants(
    base_path: Optional[path] = None,
    files: Optional[collection] = None,
    labels: Optional[dict] = None,
    column_map: Optional[dict] = None,
    repeat_symbol: str = "_#"
) -> Tuple[dict, DataFrame]:
    """
    Read variant file set
    :param base_path: Path for storing mutation trait data;
        The file must contain the following names `{chr, position, rsId, pp}`, where ID represents the representative of the trait name;
    :param files: Collection of mutation trait data;
    :param labels: Classification labels for each trait or disease;
    :param column_map: The mapping of column names facilitates mapping the corresponding column names in the mutation file to the specified column name information,
        i.e. `{0: "chr", 1: "position", 2: "rsId", 3: "pp"}`;
    :param repeat_symbol: If you encounter two names with the same abbreviation, you can add a symbol and numerical value to one of the abbreviations.
    :return: Data on traits or diseases
        1. PP data for each trait or disease。
        2. Annotated information on traits or diseases。
    """
    ul.log(__name__).info("Read variants file information")
    variant_columns: list = ["chr", "position", "rsId", "pp"]
    need_variant_columns: list = variant_columns.copy()
    variant_columns.append("id")

    results: dict = {}
    filenames: dict = {}

    # get files
    file_size: int = 0

    if files is not None:
        file_size: int = len(list(files))

    if base_path is None and file_size == 0:
        ul.log(__name__).error("At least one of the `resource` and `files` parameters has a parameter")
        raise ValueError("At least one of the `resource` and `files` parameters has a parameter")

    new_files = []

    if isinstance(base_path, path):
        new_files = ul.file_method(__name__).get_files_path(base_path)

    if file_size > 0:
        new_files.extend(files)

    key_list: list = []

    # read file
    for variant_file in tqdm(new_files):

        key, _ = os.path.splitext(os.path.basename(variant_file))

        if column_map is not None:

            keys = list(column_map.keys())

            if isinstance(keys[0], str):
                variant = pd.read_table(variant_file, header=0, index_col=None)
            elif isinstance(keys[0], int):
                variant = pd.read_table(variant_file, header=None, index_col=None)
            else:
                raise ValueError(
                    "The `keys` in `column_map` only support `None`, `str` type, and `int` type. "
                    "When it is None or `str` type, it will be read with a header, and when it is `int` type, "
                    "it will be read without a header."
                )

            variant.rename(columns=column_map, inplace=True)
        else:
            variant = pd.read_table(variant_file, header=0, index_col=None)

        columns = variant.columns

        if not set(need_variant_columns).issubset(set(columns)):
            ul.log(__name__).error(f"The column name of the {variant_file} file needs to include {need_variant_columns}")
            raise ValueError(f"The column name of the {variant_file} file needs to include {need_variant_columns}")

        if variant.shape[0] == 0:
            ul.log(__name__).warning(f"The content of file {variant_file} is empty")
            continue

        # judge
        if key not in key_list:
            key_list.append(key)
            variant["id"] = key
        else:
            _label_: str = key.split(repeat_symbol)[-1]
            _number_: int = 2

            if _label_.isnumeric():
                _number_: int = int(_label_)
                _number_ += 1

            old_key: str = key
            key += f"{repeat_symbol}{str(_number_)}"
            ul.log(__name__).warning(f"The `{old_key}` already exists in the previous file, set this key to `{key}`")
            variant["id"] = key

        results.update({key: variant[variant_columns]})
        filenames.update({key: variant_file})

    ul.log(__name__).info("Read variants file finish")
    ul.log(__name__).info("handle variants file")
    # concat files
    results_info = pd.concat(list(results.values()), axis=0)
    results_info.reset_index()

    # format trait information
    pp_sum: DataFrame = results_info.groupby("id", as_index=False)["pp"].sum()
    pp_sum.columns = ["id", "pp_sum"]
    pp_mean = results_info.groupby("id", as_index=False)["pp"].mean()
    pp_mean.columns = ["id", "pp_mean"]
    pp_size = results_info.groupby("id", as_index=False)["rsId"].size()
    pp_size.columns = ["id", "count"]

    merge_info = pp_sum.merge(pp_mean, on="id", how="inner")
    trait_info: DataFrame = merge_info.merge(pp_size, on="id", how="inner")
    trait_info.index = trait_info["id"].astype(str)

    # Add filename
    trait_info["filename"] = filenames

    # format variant data
    variant_data_dict: dict = {}

    ul.log(__name__).info("Create multiple trait-variants data")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        for key in tqdm(trait_info.index):
            variant_content: DataFrame = results[key]
            # format variant information
            variant_content["variant_id"] = (
                variant_content["chr"].astype(str)
                + ":" + variant_content["position"].astype(str)
                + ":" + variant_content["rsId"].astype(str)
            )
            variant_info = variant_content[["variant_id", "chr", "position", "rsId"]]
            variant_info_index = list(variant_info["variant_id"].astype(str))
            # set index
            variant_content["variant_id_index"] = list_duplicate_set(variant_info_index)
            variant_info.index = variant_content["variant_id_index"]
            # format trait-variant data
            variant_list: list = list(variant_content["variant_id_index"])
            trait_name = list(variant_content["id"])[0]
            trait: DataFrame = trait_info[trait_info["id"] == trait_name]

            # format dict
            variant_dict: dict = dict(zip(variant_list, range(len(variant_list))))

            shape = (len(variant_list), 1)

            matrix = np.zeros(shape)

            for variant_id_index, pp in zip(variant_content["variant_id_index"], variant_content["pp"]):
                matrix[variant_dict[variant_id_index], 0] = pp

            # format AnnData
            variant_adata = AnnData(to_sparse(matrix), var=trait, obs=variant_info)
            variant_data_dict.update({trait_name: variant_adata})

    if labels is not None:
        trait_info["labels"] = labels
    else:
        trait_info["labels"] = trait_info["id"]

    return variant_data_dict, trait_info
