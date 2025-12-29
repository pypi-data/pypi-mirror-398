# -*- coding: UTF-8 -*-

import os
import shutil
import warnings
from typing import Optional, Union, List, Literal

import pandas as pd
from pandas import DataFrame
from anndata import AnnData
import numpy as np

from ._scanpy_ import filter_data

from .. import util as ul
from ..file import read_sc_atac, read_h5ad, save_h5ad
from ..util import path, collection, set_inf_value, chrtype, add_cluster_info, generate_str

__name__: str = "preprocessing_snapatac2"


def get_feature_count(raw_count: int, need_features: Optional[Union[int | float]]) -> int:
    return int(raw_count * need_features) if need_features <= 1 else int(need_features)


def _process_sc_atac_(
    fragment_file: path | List[path],
    genome_anno,
    h5ad_file: Optional[path | List[path]] = None,
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    counting_strategy: Literal['fragment', 'insertion', 'paired-insertion'] = 'paired-insertion',
    is_filter_doublets: bool = True,
    need_features: Optional[Union[int | float]] = None
):
    ul.log(__name__).info(f"Read {fragment_file}")

    import snapatac2 as snap

    data = snap.pp.import_data(
        fragment_file,
        chrom_sizes=genome_anno,
        file=h5ad_file,
        min_num_fragments=min_num_fragments,
        sorted_by_barcode=sorted_by_barcode
    )

    if isinstance(fragment_file, path):
        ul.log(__name__).info(f"Read finish, shape: {data.shape}")
    else:
        ul.log(__name__).info(f"Read finish")

    # the standard procedures to add tile matrices, select features, and identify doublets
    snap.metrics.tsse(data, genome_anno)

    if isinstance(fragment_file, path):
        ul.log(__name__).info(f"Shape: {data.shape}")

    ul.log(__name__).info(f"Filter cells through TSSE ({min_tsse})")
    snap.pp.filter_cells(data, min_tsse=min_tsse)

    if isinstance(fragment_file, path):
        ul.log(__name__).info(f"Shape: {data.shape}")

    ul.log(__name__).info(f"Add tile matrix.")
    snap.pp.add_tile_matrix(data, bin_size=bin_size, counting_strategy=counting_strategy)

    if isinstance(fragment_file, path):
        ul.log(__name__).info(f"Shape: {data.shape}")

    # The situation where features have been filtered
    features: Optional[str] = None

    if need_features is not None:
        feature_count: int = get_feature_count(
            data.shape[1] if isinstance(fragment_file, path) else data[0].shape[1], need_features
        )
        ul.log(__name__).info("Select {} features".format(feature_count))
        snap.pp.select_features(data, n_features=feature_count)

        if isinstance(fragment_file, path):
            ul.log(__name__).info(f"Shape: {data.shape}")

        features = "selected"

    if is_filter_doublets:
        ul.log(__name__).info("Identify doublets.")
        snap.pp.scrublet(data, features=features)
        ul.log(__name__).info("Filter doublets.")
        snap.pp.filter_doublets(data)

        if isinstance(fragment_file, path):
            ul.log(__name__).info(f"Shape: {data.shape}")

    _params_: dict = {
        "fragment_file": fragment_file,
        "h5ad_file": h5ad_file if h5ad_file is not None else "",
        "min_num_fragments": min_num_fragments,
        "sorted_by_barcode": sorted_by_barcode,
        "bin_size": bin_size,
        "min_tsse": min_tsse,
        "features": features if features is not None else "",
        "need_features": need_features if need_features is not None else "",
        "is_filter_doublets": is_filter_doublets
    }

    if not isinstance(data, list):
        data.uns["params"] = _params_

    return data, features


def get_sc_atac(
    fragment_file: path,
    genome_anno,
    h5ad_file: Optional[path] = None,
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    counting_strategy: Literal['fragment', 'insertion', 'paired-insertion'] = 'paired-insertion',
    need_features: Optional[Union[int | float]] = None,
    is_filter_doublets: bool = True
):

    features: Optional[str] = None

    if fragment_file.endswith(".h5ad"):
        h5ad_file = fragment_file

    if h5ad_file is not None and os.path.exists(h5ad_file):
        ul.log(__name__).warning(
            "Suggest using fragments files to scATAC-seq data. (If the reading process is completed through snapATAC2, "
            "this message can be ignored.)"
        )
        adata = read_sc_atac(h5ad_file)
    else:

        _cache_file_path_ = os.path.join(ul.project_cache_path, generate_str())
        _is_cache_ = False

        if h5ad_file is None:
            _is_cache_ = True
            ul.file_method(__name__).makedirs(_cache_file_path_)
            h5ad_file = os.path.join(_cache_file_path_, generate_str() + ".h5ad")

        # import the fragment files and process them
        adata, features = _process_sc_atac_(
            fragment_file=fragment_file,
            genome_anno=genome_anno,
            h5ad_file=h5ad_file,
            min_num_fragments=min_num_fragments,
            sorted_by_barcode=sorted_by_barcode,
            bin_size=bin_size,
            min_tsse=min_tsse,
            counting_strategy=counting_strategy,
            is_filter_doublets=is_filter_doublets,
            need_features=need_features
        )
        adata.close()

        adata = read_sc_atac(h5ad_file)

        if _is_cache_ and os.path.exists(_cache_file_path_):
            shutil.rmtree(_cache_file_path_)

        del _cache_file_path_, _is_cache_

    selected_list = None

    if features is not None:
        selected_list = np.array(list(adata.var["selected"]))

    return adata, selected_list, h5ad_file


def merge_sc_atac(
    files: dict,
    genome_anno,
    merge_key: str = "merge_sc_atac",
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    counting_strategy: Literal['fragment', 'insertion', 'paired-insertion'] = 'paired-insertion',
    max_iter_harmony: int = 20,
    harmony_groupby: Optional[Union[str | list[str]]] = None,
    is_selected: bool = False,
    is_batch: bool = True,
    need_features: Optional[Union[int | float]] = None,
    output_path: Optional[path] = None
) -> AnnData:
    """
    Integrate multiple scATAC-seq data through snapATAC2 (https://kzhang.org/SnapATAC2/tutorials/integration.html)
        Note: Please do not move the generated files during this processing
    :param files: {file_key: file path of scATAC-seq data, ...} scATAC-seq data information that needs to be integrated
    :param genome_anno: Reference genome, commonly known as `snap.genome.hg38` and `snap.genome.hg19`
    :param merge_key: Finally form the file name of H5AD
    :param min_num_fragments: Number of unique fragments threshold used to filter cells
    :param sorted_by_barcode: Is the input fragments file sorted
    :param bin_size: The size of consecutive genomic regions used to record the counts.
    :param min_tsse: Minimum TSS enrichment score required for a cell to pass filtering.
    :param max_iter_harmony: The maximum number of iterations in the `harmony` algorithm.
    :param harmony_groupby: If specified, split the data into groups and perform batch correction on each group separately.
    :param is_selected: If True, based on the feature selection in the `snap.pp.select_features` method, further
        filtering is performed according to the features of each sample.
    :param is_batch: If True, batch correction by sample.
    :param need_features: If `need_features` <=1, it represents the retention of `need_features`% of the overall
        features. Otherwise, it is considered an integer and `need_features` features are filtered.
    :param output_path: Path to generate file
    :return: Integrated scATAC-seq data
    """
    ul.log(__name__).info("Start integrating scATAC-seq data.")

    import snapatac2 as snap

    # Obtain sample information
    filenames: list = list(files.keys())

    if len(filenames) <= 1:
        ul.log(__name__).error("At least two samples are required.")
        raise ValueError("At least two samples are required.")

    # file path
    file_list: list = list(files.values())

    # The situation where features have been filtered
    features: Optional[str] = None

    if str(file_list[0]).endswith(".h5ad"):
        ul.log(__name__).warning(
            "Suggest using fragments files to integrate scATAC-seq data. (If the process of adding tile matrices, "
            "selecting features, and identifying doubles has been completed through snapATAC2, this message can be "
            "ignored.)"
        )
        adata_list: list = [(name, adata) for name, adata in zip(filenames, file_list)]
    else:
        output_filenames: list = [os.path.join(output_path, key + ".h5ad") for key in list(files.keys())]

        # import the fragment files and process them
        adatas, features = _process_sc_atac_(
            fragment_file=file_list,
            genome_anno=genome_anno,
            h5ad_file=output_filenames if output_path is not None else None,
            min_num_fragments=min_num_fragments,
            sorted_by_barcode=sorted_by_barcode,
            bin_size=bin_size,
            min_tsse=min_tsse,
            counting_strategy=counting_strategy,
            need_features=need_features
        )

        adata_list: list = [(name, adata) for name, adata in zip(filenames, adatas)]

        del adatas

    # AnnDataSet
    merge_filename: str = os.path.join(output_path, merge_key + ".h5ad") if output_path is not None else None
    data = snap.AnnDataSet(adatas=adata_list, filename=merge_filename)

    # id unique
    data.obs['barcodes'] = data.obs_names
    unique_cell_ids = [sa + '_' + bc for sa, bc in zip(data.obs['sample'], data.obs_names)]
    data.obs_names = unique_cell_ids

    selected_list: collection = np.array([])

    if need_features is not None:
        snap.pp.select_features(data, n_features=get_feature_count(data.shape[1], need_features))
        selected_list = np.array(list(data.var["selected"]))

    # spectral
    ul.log(__name__).info("Spectral dimensionality reduction.")
    snap.tl.spectral(data, features=features)

    # Batch correction
    if is_batch:
        ul.log(__name__).info("Batch correction.")
        snap.pp.mnc_correct(data, batch="sample")
        snap.pp.harmony(data, batch="sample", groupby=harmony_groupby, max_iter_harmony=max_iter_harmony)

    # close
    data.close()

    # read file
    sc_atac = read_sc_atac(merge_filename)

    # form count matrix
    data_matrix = []
    adata_path_list = list(sc_atac.uns["AnnDataSet"]["file_path"])

    for _adata_path_ in adata_path_list:
        _adata_ = read_h5ad(_adata_path_)
        data_matrix.append(_adata_.X)

        if is_selected and need_features is not None:
            selected_list = np.logical_and(selected_list, np.array(list(_adata_.var["selected"])))

        del _adata_

    from scipy.sparse import vstack

    sc_atac.X = vstack(data_matrix)

    if need_features is not None:
        sc_atac = sc_atac[:, selected_list]

    sc_atac.obs.index = sc_atac.obs.index.astype(str)
    sc_atac.var.index = sc_atac.var.index.astype(str)

    sc_atac.uns["params"] = {
        "files": files,
        "merge_key": merge_key,
        "min_num_fragments": min_num_fragments,
        "sorted_by_barcode": sorted_by_barcode,
        "bin_size": bin_size,
        "min_tsse": min_tsse,
        "max_iter_harmony": max_iter_harmony,
        "harmony_groupby": harmony_groupby,
        "is_selected": is_selected,
        "need_features": need_features,
        "output_path": output_path
    }

    if output_path is not None:
        save_h5ad(sc_atac, os.path.join(output_path, f"{merge_key}_snapATAC2.h5ad"))

    ul.log(__name__).info("End integrating scATAC-seq data.")
    return sc_atac


def get_gene_expression(
    fragment_file: path,
    genome_anno,
    h5ad_file: Optional[path] = None,
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    need_features: Optional[Union[int | float]] = None,
    min_cells: int = 5,
    is_filter_doublets: bool = True,
    gene_save_file: Optional[path] = None
) -> AnnData:

    import snapatac2 as snap

    # import the fragment files and process them
    adata, selected_list, h5ad_file = get_sc_atac(
        fragment_file=fragment_file,
        genome_anno=genome_anno,
        h5ad_file=h5ad_file,
        min_num_fragments=min_num_fragments,
        sorted_by_barcode=sorted_by_barcode,
        bin_size=bin_size,
        min_tsse=min_tsse,
        is_filter_doublets=is_filter_doublets,
        need_features=need_features
    )

    # Create the cell by gene activity matrix
    ul.log(__name__).info("Obtain gene expression matrix.")
    selected_adata = adata[:, selected_list] if selected_list is not None else adata
    filter_data(selected_adata)
    gene_matrix = snap.pp.make_gene_matrix(selected_adata, genome_anno)
    ul.log(__name__).info(f"Shape: {selected_adata.shape}")

    import scanpy as sc

    # normalize
    ul.log(__name__).info(f"Filter genes. shape: {gene_matrix.shape}")
    sc.pp.filter_genes(gene_matrix, min_cells=min_cells)
    ul.log(__name__).info(f"Gene matrix shape: {gene_matrix.shape}")

    ul.log(__name__).info(f"Normalize, log1p and magic.")
    sc.pp.normalize_total(gene_matrix)
    sc.pp.log1p(gene_matrix)
    sc.external.pp.magic(gene_matrix, solver="approximate")

    save_h5ad(adata, h5ad_file)

    gene_matrix.uns["params"] = {
        "fragment_file": fragment_file,
        "h5ad_file": h5ad_file,
        "min_num_fragments": min_num_fragments,
        "sorted_by_barcode": sorted_by_barcode,
        "bin_size": bin_size,
        "min_tsse": min_tsse,
        "need_features": need_features,
        "is_filter_doublets": is_filter_doublets,
        "gene_save_file": gene_save_file
    }

    if gene_save_file is not None:
        save_h5ad(gene_matrix, gene_save_file)

    return gene_matrix


def get_peak_matrix(
    fragment_file: path,
    genome_anno,
    cluster: str,
    cell_anno: Optional[DataFrame] = None,
    h5ad_file: Optional[path] = None,
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    need_features: Optional[Union[int | float]] = None,
    is_filter_doublets: bool = True,
    peak_matrix_save_file: Optional[path] = None
):

    import snapatac2 as snap

    # import the fragment files and process them
    adata, selected_list, h5ad_file = get_sc_atac(
        fragment_file=fragment_file,
        genome_anno=genome_anno,
        h5ad_file=h5ad_file,
        min_num_fragments=min_num_fragments,
        sorted_by_barcode=sorted_by_barcode,
        bin_size=bin_size,
        min_tsse=min_tsse,
        is_filter_doublets=is_filter_doublets,
        need_features=need_features
    )

    # add cell annotation information
    adata.obs = add_cluster_info(adata.obs, cell_anno, cluster)

    if cluster not in adata.obs.columns:
        ul.log(__name__).error(f"`{cluster}` is not in `adata.obs.columns`.")
        raise ValueError(f"`{cluster}` is not in `adata.obs.columns` ({adata.obs.columns}).")

    selected_adata = adata[:, selected_list] if selected_list is not None else adata
    filter_data(selected_adata)

    ul.log(__name__).info(f"Peak calling at the `{cluster}`-level.")
    try:
        snap.tl.macs3(selected_adata, groupby=cluster)
    except Exception as e:
        ul.log(__name__).error(f"The `cluster`({cluster}) is likely to have `NaN` values, please check.")
        raise RuntimeError(f"The `cluster`({cluster}) is likely to have `NaN` values, please check.\n {e}")

    ul.log(__name__).info("Obtain a unified, non-overlapping, and fixed-width peak list.")
    peaks = snap.tl.merge_peaks(selected_adata.uns['macs3'], genome_anno)

    ul.log(__name__).info("Create a cell by peak matrix.")
    peak_mat = snap.pp.make_peak_matrix(selected_adata, use_rep=peaks['Peaks'])

    peak_mat.uns["params"] = {
        "fragment_file": fragment_file,
        "cluster": cluster,
        "h5ad_file": h5ad_file,
        "min_num_fragments": min_num_fragments,
        "sorted_by_barcode": sorted_by_barcode,
        "bin_size": bin_size,
        "min_tsse": min_tsse,
        "need_features": need_features,
        "is_filter_doublets": is_filter_doublets,
        "peak_matrix_save_file": peak_matrix_save_file
    }

    if peak_matrix_save_file is not None:
        save_h5ad(peak_mat, peak_matrix_save_file)

    return adata, selected_adata, h5ad_file, peaks, peak_mat


def _process_info_to_adata_(
    adata: AnnData,
    selected_adata: AnnData,
    cluster: str,
    info_data: DataFrame,
    obs_info: DataFrame,
    h5ad_file: str
) -> AnnData:
    obs_unique = list(obs_info.index)
    obs_unique_dict: dict = dict(zip(obs_unique, range(len(obs_unique))))
    # var
    cluster_info: DataFrame = selected_adata.obs.groupby(cluster, as_index=False).size()
    cluster_info.index = cluster_info[cluster].astype(str)
    cluster_info.rename_axis("index", inplace=True)
    cluster_info.sort_values([cluster], inplace=True)
    cluster_list: list = list(cluster_info.index)

    shape = (len(obs_unique), len(cluster_list))
    ul.log(__name__).info(f"Create data, shape {shape}")
    log2_fold_change_matrix = np.zeros(shape)
    p_value_matrix = np.zeros(shape)
    adjusted_p_value_matrix = np.zeros(shape)

    # Add value
    for _id_, log2_fold_change, p_value, adjusted_p_value, _cluster_ in zip(
        info_data["id"],
        info_data["log2_fold_change"],
        info_data["p_value"],
        info_data["adjusted_p_value"],
        info_data[cluster]
    ):
        log2_fold_change_matrix[obs_unique_dict[_id_], cluster_list.index(_cluster_)] = log2_fold_change
        p_value_matrix[obs_unique_dict[_id_], cluster_list.index(_cluster_)] = p_value
        adjusted_p_value_matrix[obs_unique_dict[_id_], cluster_list.index(_cluster_)] = adjusted_p_value

    # solve -Inf/Inf value
    set_inf_value(log2_fold_change_matrix)
    set_inf_value(p_value_matrix)
    set_inf_value(adjusted_p_value_matrix)

    adjusted_p_value_matrix[adjusted_p_value_matrix == 0] = np.min(adjusted_p_value_matrix[adjusted_p_value_matrix != 0])

    # create
    info_adata: AnnData = AnnData(p_value_matrix, obs=obs_info, var=cluster_info)
    info_adata.layers["log2_fold_change"] = log2_fold_change_matrix
    info_adata.layers["adjusted_p_value"] = adjusted_p_value_matrix

    save_h5ad(adata, h5ad_file)

    return info_adata


def get_tf_data(
    fragment_file: path,
    genome_anno,
    cluster: str,
    cell_anno: Optional[DataFrame] = None,
    h5ad_file: Optional[path] = None,
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    need_features: Optional[Union[int | float]] = None,
    p_value: float = 0.01,
    is_filter_doublets: bool = True,
    peak_matrix_save_file: Optional[path] = None,
    tf_save_file: Optional[path] = None
) -> AnnData:

    import snapatac2 as snap

    # import the fragment files and process them
    adata, selected_adata, h5ad_file, peaks, peak_mat = get_peak_matrix(
        fragment_file=fragment_file,
        genome_anno=genome_anno,
        cluster=cluster,
        cell_anno=cell_anno,
        h5ad_file=h5ad_file,
        min_num_fragments=min_num_fragments,
        sorted_by_barcode=sorted_by_barcode,
        bin_size=bin_size,
        min_tsse=min_tsse,
        is_filter_doublets=is_filter_doublets,
        need_features=need_features,
        peak_matrix_save_file=peak_matrix_save_file
    )

    ul.log(__name__).info("Finding marker regions.")
    marker_peaks = snap.tl.marker_regions(peak_mat, groupby=cluster, pvalue=p_value)

    if len(marker_peaks.keys()) == 0 and p_value < 0.05:
        p_value = 0.05
        ul.log(__name__).warning(f"Due to the absence of marker regions, the `p_value` value is automatically changed to `0.05`.")
        marker_peaks = snap.tl.marker_regions(peak_mat, groupby=cluster, pvalue=p_value)

    if len(marker_peaks.keys()) == 0:
        ul.log(__name__).error(f"No marker regions for `p_value` = {p_value}, you can try to increase the `p_value`.")
        raise ValueError(f"No marker regions for `p_value` = {p_value}, you can try to increase the `p_value`.")

    ul.log(__name__).info("Motif enrichment.")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        motifs = snap.tl.motif_enrichment(
            motifs=snap.datasets.cis_bp(unique=True),
            regions=marker_peaks,
            genome_fasta=genome_anno,
        )

    have_cluster_list: list = list(motifs.keys())
    ul.log(__name__).info(f"Merge motif result for `{have_cluster_list}`")

    motif_list: list = []
    columns: list = ['id', 'name', 'family', 'log2_fold_change', 'p_value', 'adjusted_p_value']

    # Add motif
    for cell_type in have_cluster_list:
        motif_data: DataFrame = pd.DataFrame(motifs[cell_type], columns=columns)
        motif_data[cluster] = cell_type
        motif_list.append(motif_data)

    # obtain all motif data
    tf_data: DataFrame = pd.concat(motif_list, axis=0)
    tf_data.drop(columns=["family"], inplace=True)

    # obs
    tf_info: DataFrame = tf_data[["id", "name"]].drop_duplicates()
    tf_info.index = tf_info["id"].astype(str)
    tf_info.rename_axis("index", inplace=True)
    tf_info.sort_values(["name", "id"], inplace=True)

    tf_adata = _process_info_to_adata_(
        adata=adata,
        selected_adata=selected_adata,
        cluster=cluster,
        info_data=tf_data,
        obs_info=tf_info,
        h5ad_file=h5ad_file
    )

    tf_adata.uns["params"] = {
        "fragment_file": fragment_file,
        "cluster": cluster,
        "h5ad_file": h5ad_file,
        "min_num_fragments": min_num_fragments,
        "sorted_by_barcode": sorted_by_barcode,
        "bin_size": bin_size,
        "min_tsse": min_tsse,
        "need_features": need_features,
        "p_value": p_value,
        "is_filter_doublets": is_filter_doublets,
        "peak_matrix_save_file": peak_matrix_save_file,
        "tf_save_file": tf_save_file
    }

    if tf_save_file is not None:
        save_h5ad(tf_adata, tf_save_file)

    return tf_adata


def get_difference_peaks(
    fragment_file: path,
    genome_anno,
    cluster: str,
    cell_anno: Optional[DataFrame] = None,
    h5ad_file: Optional[path] = None,
    min_num_fragments: int = 200,
    sorted_by_barcode: bool = False,
    bin_size: int = 500,
    min_tsse: float = 5.0,
    need_features: Optional[Union[int | float]] = None,
    is_filter_doublets: bool = True,
    min_log_fc: float = 0.25,
    min_pct: float = 0.05,
    peak_matrix_save_file: Optional[path] = None,
    diff_peaks_save_file: Optional[path] = None
) -> AnnData:

    import snapatac2 as snap

    # import the fragment files and process them
    adata, selected_adata, h5ad_file, peaks, peak_mat = get_peak_matrix(
        fragment_file=fragment_file,
        genome_anno=genome_anno,
        cluster=cluster,
        cell_anno=cell_anno,
        h5ad_file=h5ad_file,
        min_num_fragments=min_num_fragments,
        sorted_by_barcode=sorted_by_barcode,
        bin_size=bin_size,
        min_tsse=min_tsse,
        is_filter_doublets=is_filter_doublets,
        need_features=need_features,
        peak_matrix_save_file=peak_matrix_save_file
    )
    adata_cell_anno: DataFrame = selected_adata.obs.copy()
    cluster_list: list = list(set(adata_cell_anno[cluster]))
    cluster_list.sort()
    cluster_str: str = ", ".join(cluster_list)

    # Container for storing differential peaks
    diff_peaks_list: list = []

    # feature name, log2(fold_change), p-value, adjusted p-value
    columns: list = ["id", "log2_fold_change", "p_value", "adjusted_p_value"]

    for _cluster_ in cluster_list:
        ul.log(__name__).info(f"Processing {cluster}: {_cluster_}/({cluster_str}).")
        _cluster_list_ = cluster_list.copy()
        _cluster_list_.remove(_cluster_)

        # cell barcodes
        cell_group1 = adata_cell_anno[adata_cell_anno[cluster] == _cluster_].index
        cell_group2 = adata_cell_anno[adata_cell_anno[cluster].isin(_cluster_list_)].index

        ul.log(__name__).info(f"Processing {cluster}: {_cluster_} difference peaks.")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _diff_peaks_ = snap.tl.diff_test(
                peak_mat,
                cell_group1=cell_group1,
                cell_group2=cell_group2,
                min_log_fc=min_log_fc,
                min_pct=min_pct
            )

        # process result
        _diff_peaks_data_ = pd.DataFrame(_diff_peaks_, columns=columns)
        _diff_peaks_data_["log2_fold_change"] = _diff_peaks_data_["log2_fold_change"].astype(np.float64)
        _diff_peaks_data_["p_value"] = _diff_peaks_data_["p_value"].astype(np.float64)
        _diff_peaks_data_["adjusted_p_value"] = _diff_peaks_data_["adjusted_p_value"].astype(np.float64)
        _diff_peaks_data_.insert(0, cluster, _cluster_)
        _diff_peaks_data_.index = _diff_peaks_data_[cluster].astype(str) + "_" + _diff_peaks_data_["id"].astype(str)

        # Add result
        diff_peaks_list.append(_diff_peaks_data_)

        del _cluster_list_, _diff_peaks_, _diff_peaks_data_

    # get difference peaks data
    diff_peaks_data: DataFrame = pd.concat(diff_peaks_list, axis=0)

    # obs
    peaks_info: DataFrame = diff_peaks_data["id"].drop_duplicates().str.split(":|-", expand=True)
    peaks_info.columns = ["chr", "start", "end"]
    peaks_info = peaks_info[peaks_info["chr"].isin(list(chrtype.categories))]
    peaks_info["chr"] = peaks_info["chr"].astype(chrtype)
    peaks_info.index = (
        peaks_info["chr"].astype(str) + ":" + peaks_info["start"].astype(str) + "-" + peaks_info["end"].astype(str)
    )
    peaks_info.sort_values(["chr", "start", "end"], inplace=True)

    diff_peaks_adata = _process_info_to_adata_(
        adata=adata,
        selected_adata=selected_adata,
        cluster=cluster,
        info_data=diff_peaks_data,
        obs_info=peaks_info,
        h5ad_file=h5ad_file
    )

    diff_peaks_adata.uns["params"] = {
        "fragment_file": fragment_file,
        "cluster": cluster,
        "h5ad_file": h5ad_file,
        "min_num_fragments": min_num_fragments,
        "sorted_by_barcode": sorted_by_barcode,
        "bin_size": bin_size,
        "min_tsse": min_tsse,
        "need_features": need_features,
        "is_filter_doublets": is_filter_doublets,
        "min_log_fc": min_log_fc,
        "min_pct": min_pct,
        "peak_matrix_save_file": min_pct,
        "diff_peaks_save_file": diff_peaks_save_file
    }

    if diff_peaks_save_file is not None:
        save_h5ad(diff_peaks_adata, diff_peaks_save_file)

    return diff_peaks_adata
