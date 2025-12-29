# -*- coding: UTF-8 -*-

import warnings
from typing import Optional, Literal

import numpy as np
from anndata import AnnData
from pandas import DataFrame

from .. import util as ul
from ..file import save_h5ad
from ..tool import lsi, tf_idf
from ..util import add_cluster_info, matrix_data, set_inf_value, collection

__name__: str = "preprocessing_scanpy"

_Method = Optional[Literal['logreg', 't-test', 'wilcoxon', 't-test_overestim_var']]


def filter_data(
    adata: AnnData,
    min_cells: int = 1,
    min_peaks: int = 1,
    min_peaks_counts: int = 1,
    min_cells_counts: int = 1,
    cell_rate: Optional[float] = None,
    peak_rate: Optional[float] = None,
    is_copy: bool = False,
    is_min_cell: bool = True,
    is_min_peak: bool = False
) -> AnnData:
    """
    Filter scATAC-seq data
    :param adata: scATAC-seq data
    :param min_peaks_counts: Minimum number of counts required for a peak to pass filtering
    :param min_cells: Minimum number of cells expressed required for a peak to pass filtering
    :param min_cells_counts: Minimum number of counts required for a cell to pass filtering
    :param min_peaks: Minimum number of peaks expressed required for a cell to pass filtering
    :param cell_rate: Removing the percentage of cell count in total cell count only takes effect when the min_cells
        parameter is None
    :param peak_rate: Removing the percentage of peak count in total peak count only takes effect when the min_peaks
        parameter is None
    :param is_copy: Do you want to deeply copy data
    :param is_min_cell: Whether to screen cells
    :param is_min_peak: Whether to screen peaks
    :return: scATAC-seq data
    """
    import scanpy as sc

    ul.log(__name__).info("Filter scATAC-seq data")

    if adata.shape[0] == 0:
        ul.log(__name__).error("The scATAC data is empty")
        raise ValueError("The scATAC data is empty")

    filter_adata = adata.copy() if is_copy else adata
    cells_count, peaks_count = filter_adata.shape

    if cell_rate is not None:

        if cell_rate <= 0 or cell_rate >= 1:
            ul.log(__name__).error("The parameter of `cell_rate` should be between 0 and 1.")
            raise ValueError("The parameter of `cell_rate` should be between 0 and 1.")

        _min_cells_ = int(filter_adata.shape[0] * cell_rate)

        if _min_cells_ > 1:
            min_cells = _min_cells_

    if peak_rate is not None:

        if peak_rate <= 0 or peak_rate >= 1:
            ul.log(__name__).error("The parameter of `peak_rate` should be between 0 and 1.")
            raise ValueError("The parameter of `peak_rate` should be between 0 and 1.")

        _min_peaks_ = int(filter_adata.shape[1] * peak_rate)

        if _min_peaks_ > 1:
            min_peaks = _min_peaks_

    ul.log(__name__).info(f"min cells: {min_cells}, min peaks: {min_peaks}")
    sc.pp.filter_genes(filter_adata, min_cells=min_cells)
    sc.pp.filter_cells(filter_adata, min_genes=min_peaks)

    # filter peaks and cell
    if is_min_peak:
        sc.pp.filter_genes(filter_adata, min_counts=min_peaks_counts)

    if is_min_cell:
        sc.pp.filter_cells(filter_adata, min_counts=min_cells_counts)
    else:
        sc.pp.filter_cells(filter_adata)

    # judge cells count
    if filter_adata.shape[0] == 0:
        ul.log(__name__).error(
            "After screening, the number of cells was 0. Suggest setting the `is_min_peak` parameter to `False` or "
            "lowering the `cell_rate` and `peak_rate` parameters to try again"
        )
        return filter_adata

    ul.log(__name__).info(
        f"Filtered out cells {cells_count - filter_adata.shape[0]}, "
        f"Filtered out peaks {peaks_count - filter_adata.shape[1]}"
    )
    ul.log(__name__).info(f"Size of filtered scATAC-seq data: {filter_adata.shape}")
    filter_adata.uns["step"] = 0
    return filter_adata


def get_difference_genes(
    adata: AnnData,
    cluster: str,
    method: _Method = "wilcoxon",
    cell_anno: Optional[DataFrame] = None,
    diff_genes_file: Optional[str] = None
) -> AnnData:

    import scanpy as sc

    # add cell annotation information
    adata.obs = add_cluster_info(adata.obs, cell_anno, cluster)

    if "log1p" not in adata.uns_keys():
        ul.log(__name__).info("The `log1p` not detected in `adata.uns_keys`, `log1p` operation needs to be performed.")
        raise ValueError("The `log1p` not detected in `adata.uns_keys`, `log1p` operation needs to be performed.")

    if "base" not in adata.uns["log1p"].keys():
        adata.uns["log1p"].update({"base": None})

    # gene
    ul.log(__name__).info("Rank genes for characterizing groups.")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sc.tl.rank_genes_groups(adata=adata, groupby=cluster, method=method, use_raw=False)

    # get difference genes for each `cluster`
    diff_genes = adata.uns['rank_genes_groups']['names']

    # gene names
    gene_list: list = list(adata.var.index)
    gene_list.sort()
    gene_dict: dict = dict(zip(gene_list, range(len(gene_list))))

    # obs
    cluster_info: DataFrame = adata.obs.copy().groupby([cluster], as_index=False).size()
    cluster_info.index = cluster_info[cluster].astype(str)

    cluster_list: list = cluster_info.index.tolist()
    cluster_list.sort()

    _shape_ = (adata.shape[1], cluster_info.shape[0])
    diff_genes_score_matrix: matrix_data = np.zeros(_shape_)
    diff_genes_p_value_matrix: matrix_data = np.zeros(_shape_)
    diff_genes_adjusted_p_value_matrix: matrix_data = np.zeros(_shape_)
    diff_genes_log2_fold_change_matrix: matrix_data = np.zeros(_shape_)
    del _shape_

    # cluster
    for _cluster_ in cluster_list:
        ul.log(__name__).info(f"Obtaining differentially expressed genes for `cluster` ({_cluster_}).")
        # obtain cluster difference gene data
        _cluster_data_: DataFrame = sc.get.rank_genes_groups_df(adata, group=_cluster_)
        _cluster_index_: int = cluster_list.index(_cluster_)

        # Add data value
        for _gene_name_, _score_, _p_value_, _adjusted_p_value_, _log2_fold_change_ in zip(
            _cluster_data_["names"],
            _cluster_data_["scores"],
            _cluster_data_["pvals"],
            _cluster_data_["pvals_adj"],
            _cluster_data_["logfoldchanges"]
        ):
            _gene_index_: int = gene_dict[_gene_name_]
            diff_genes_score_matrix[_gene_index_, _cluster_index_] = 0 if np.isnan(_score_) else _score_
            diff_genes_p_value_matrix[_gene_index_, _cluster_index_] = 1 if np.isnan(_p_value_) else _p_value_
            diff_genes_adjusted_p_value_matrix[_gene_index_, _cluster_index_] = 1 if np.isnan(_adjusted_p_value_) else _adjusted_p_value_
            diff_genes_log2_fold_change_matrix[_gene_index_, _cluster_index_] = 0 if np.isnan(_log2_fold_change_) else _log2_fold_change_

        del _cluster_data_, _cluster_index_

    set_inf_value(diff_genes_score_matrix)
    set_inf_value(diff_genes_p_value_matrix)
    set_inf_value(diff_genes_adjusted_p_value_matrix)
    set_inf_value(diff_genes_log2_fold_change_matrix)

    diff_genes_p_value_matrix[diff_genes_p_value_matrix == 0] = np.min(diff_genes_p_value_matrix[diff_genes_p_value_matrix != 0])
    diff_genes_adjusted_p_value_matrix[diff_genes_adjusted_p_value_matrix == 0] = np.min(diff_genes_adjusted_p_value_matrix[diff_genes_adjusted_p_value_matrix != 0])

    # create
    diff_genes_adata: AnnData = AnnData(diff_genes_score_matrix, obs=adata.var, var=cluster_info)
    diff_genes_adata.layers["p_value"] = diff_genes_p_value_matrix
    diff_genes_adata.layers["adjusted_p_value"] = diff_genes_adjusted_p_value_matrix
    diff_genes_adata.layers["log2_fold_change"] = diff_genes_log2_fold_change_matrix

    # Add diff_genes
    diff_genes_adata.uns["diff_genes"] = diff_genes

    if diff_genes_file is not None:
        save_h5ad(diff_genes_adata, diff_genes_file)

    return diff_genes_adata


def paga_trajectory(
    adata: AnnData,
    layer: Optional[str] = None,
    latent: str = "X_pca",
    groups: str = "louvain",
    position: Optional[collection] = None,
    lsi_components: int = 50,
    root_cluster: Optional[str] = None,
    n_neighbors: int = 15,
    resolution: float = 1.0,
    is_denoise: bool = True,
) -> None:
    import scanpy as sc

    if position is not None:

        if len(position) != 2:
            ul.log(__name__).error("The `position` parameter must contain two elements, for example: `(UMAP1, UMAP2)`.")
            raise ValueError("The `position` parameter must contain two elements, for example: `(UMAP1, UMAP2)`.")

        if position[0] not in adata.obs.columns or position[1] not in adata.obs.columns:
            ul.log(__name__).error("The value in the `position` parameter must be one of the column names in `adata.obs`.")
            raise ValueError("The value in the `position` parameter must be one of the column names in `adata.obs`.")

    fixed_name: str = "X_pca"

    is_run: bool = latent not in adata.obsm

    status: int = 0

    if is_run:

        if layer is None:
            counts = adata.X
        else:

            if layer not in adata.layers:
                ul.log(__name__).error("The value of the `layer` parameter must be one of the keys in `adata.layers`.")
                raise ValueError("The value of the `layer` parameter must be one of the keys in `adata.layers`.")

            counts = adata.layers[layer]

        tf_idf_matrix = tf_idf(counts)
        del counts

        lsi_matrix = lsi(tf_idf_matrix, n_components=lsi_components)
        adata.obsm['X_pca'] = lsi_matrix
        del tf_idf_matrix, lsi_matrix

        status = 1

    else:

        if latent != fixed_name:
            adata.obsm['X_pca'] = adata.obsm[latent]
            status = 2

    ul.log(__name__).info("Compute a neighborhood graph of observations.")
    sc.pp.neighbors(adata, n_neighbors=n_neighbors)

    if is_denoise:
        ul.log(__name__).info("Run denoising")
        sc.tl.diffmap(adata)
        sc.pp.neighbors(adata, n_neighbors=n_neighbors, use_rep="X_diffmap")

    if groups not in adata.obs.columns:

        if groups == "louvain":
            ul.log(__name__).info("Run louvain")
            sc.tl.louvain(adata, resolution=resolution)
        else:
            ul.log(__name__).error("The value of the `groups` parameter is 'louvain' or needs to be included in `adata.obs.columns`.")
            raise ValueError("The value of the `groups` parameter is 'louvain' or needs to be included in `adata.obs.columns`.")

    ul.log(__name__).info("Run PAGA")
    sc.tl.paga(adata, groups=groups)

    sc.pl.paga(adata, show=False)
    sc.tl.draw_graph(adata, init_pos="paga")

    if position is not None:
        adata.obsm['X_draw_graph_fr_old'] = adata.obsm['X_draw_graph_fr']
        adata.obsm['X_draw_graph_fr'] = adata.obs[list(position)].values

    if root_cluster is not None:
        adata.uns["iroot"] = np.flatnonzero(adata.obs[groups] == root_cluster)[0]
        sc.tl.dpt(adata)

    if status == 1:
        adata.obsm['lsi'] = adata.obsm.pop('X_pca')
    elif status == 2:
        adata.obsm.pop('X_pca')
    else:
        pass
