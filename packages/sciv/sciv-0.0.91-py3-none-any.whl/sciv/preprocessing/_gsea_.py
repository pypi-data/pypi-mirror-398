# -*- coding: UTF-8 -*-

import warnings
from typing import Optional, Union, Literal

import numpy as np
import pandas as pd
from tqdm import tqdm
from anndata import AnnData
from pandas import DataFrame

from .. import util as ul
from ..util import check_adata_get, to_dense

__name__: str = "preprocessing_gsea"

_Datasets = Optional[Literal['Human', 'Mouse', 'Yeast', 'Fly', 'Fish', 'Worm']]


def gsea_enrichr(
    gene_list: list[str],
    gene_sets: Union[list[str], set] = (
        "GO_Biological_Process_2023",
        "GO_Cellular_Component_2023",
        "GO_Molecular_Function_2023",
        "GWAS_Catalog_2023",
        "KEGG_2016"
    ),
    organism: _Datasets = "human",
    is_verbose: bool = True,
    output_dir: Optional[str] = None
) -> DataFrame:

    import gseapy as gp

    # noinspection PyTypeChecker
    names = gp.get_library_name(organism)

    if not set(gene_sets).issubset(set(names)):
        ul.log(__name__).error(f"The set of the {gene_sets} needs to include `gp.get_library_name(organism)`")
        raise ValueError(f"The set of the {gene_sets} needs to include `gp.get_library_name(organism)`")

    if output_dir is not None:
        ul.file_method(__name__).makedirs(output_dir)

    if is_verbose:
        ul.log(__name__).info("GSEA enrichr.")

    # noinspection PyTypeChecker
    gsea = gp.enrichr(gene_list=gene_list, gene_sets=list(gene_sets), organism=organism, outdir=output_dir)
    return gsea.results


def get_gene_enrichment(
    adata: AnnData,
    top_number: int = 50,
    threshold: float = 0.01,
    layer: Optional[str] = None,
    is_order_or_lt: bool = True,
    is_top: bool = True,
    gene_sets: Union[list[str], set] = (
        "GO_Biological_Process_2023",
        "GO_Cellular_Component_2023",
        "GO_Molecular_Function_2023",
        "GWAS_Catalog_2023",
        "KEGG_2016"
    ),
    organism: _Datasets = "human",
    output_dir: Optional[str] = None,
) -> DataFrame:
    ul.log(__name__).info("Gene enrichment analysis.")
    # get data
    new_adata = check_adata_get(adata, layer=layer)

    enrichr_data_list = []

    cluster_list: list[str] = list(new_adata.var.index)
    gene_list: list = list(new_adata.obs_names)

    if is_top and len(gene_list) < top_number:
        ul.log(__name__).warning(f"The number of parameters `top_number` ({top_number}) is greater than the number of genes ({len(gene_list)}).")
        top_number = len(gene_list)

    # Add data
    for cluster in tqdm(cluster_list):

        # get index
        _values_ = to_dense(new_adata[:, cluster].X, is_array=True).flatten()

        if is_top:
            _index_ = np.argsort(_values_)[0:top_number] if is_order_or_lt else np.argsort(_values_)[-top_number:]
            _cluster_gene_list_: list[str] = list(np.array(gene_list)[_index_])
        else:
            _index_ = _values_ <= threshold if is_order_or_lt else _values_ >= threshold
            _cluster_gene_list_: list[str] = list(np.array(gene_list)[_index_])

        if len(_cluster_gene_list_) == 0:
            ul.log(__name__).warning(f"The gene list for cluster {cluster} is empty.")
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            enrichr_data: DataFrame = gsea_enrichr(
                gene_list=_cluster_gene_list_,
                gene_sets=gene_sets,
                organism=organism,
                is_verbose=False,
                output_dir=output_dir
            )

        enrichr_data["cluster"] = cluster
        enrichr_data_list.append(enrichr_data)

        del _values_, _index_, _cluster_gene_list_

    data = pd.concat(enrichr_data_list, axis=0)

    return data
