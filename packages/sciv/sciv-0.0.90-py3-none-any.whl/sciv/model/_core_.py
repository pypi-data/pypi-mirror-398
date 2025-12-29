# -*- coding: UTF-8 -*-

import os.path
import shutil
import time
from typing import Optional, Union, Literal, Tuple

import numpy as np

import anndata as ad
import pandas as pd
from tqdm import tqdm
from anndata import AnnData
from pandas import DataFrame

from .. import util as ul
from ..tool import RandomWalk, overlap_sum, obtain_cell_cell_network, calculate_init_score_weight

from ..file import save_h5ad, save_pkl, read_h5ad, read_pkl
from ..preprocessing import filter_data, poisson_vi
from ..util import path, enrichment_optional, to_dense, collection, to_sparse, difference_peak_optional

__name__: str = "model_core"


def _run_random_walk_(random_walk: RandomWalk, is_ablation: bool, is_simple: bool) -> AnnData:
    if not random_walk.is_run_core:
        random_walk.run_core()

    if not random_walk.is_run_enrichment:
        random_walk.run_enrichment()

    if is_ablation and not is_simple:
        if not random_walk.is_benchmark:
            random_walk.run_benchmark()

        if not random_walk.is_run_ablation_ncw:
            random_walk.run_ablation_ncw()

        if not random_walk.is_run_ablation_nsw:
            random_walk.run_ablation_nsw()

        if not random_walk.is_run_ablation_ncsw:
            random_walk.run_ablation_ncsw()

        if not random_walk.is_run_ablation_m_knn:
            random_walk.run_ablation_m_knn()

        if not random_walk.is_run_en_ablation_ncw:
            random_walk.run_en_ablation_ncw()

        if not random_walk.is_run_en_ablation_nsw:
            random_walk.run_en_ablation_nsw()

        if not random_walk.is_run_en_ablation_ncsw:
            random_walk.run_en_ablation_ncsw()

        if not random_walk.is_run_en_ablation_m_knn:
            random_walk.run_en_ablation_m_knn()

    return random_walk.trs_adata


def _check_and_run_two_step_(
    adata: AnnData,
    cell_rate: Optional[float] = None,
    peak_rate: Optional[float] = None,
    max_epochs: int = 500,
    lr: float = 1e-4,
    batch_size: int = 128,
    eps: float = 1e-08,
    early_stopping: bool = True,
    early_stopping_patience: int = 50,
    batch_key: Optional[str] = None,
    resolution: float = 0.5,
    k: int = 30,
    or_k: int = 1,
    weight: float = 0.1,
    laplacian_gamma: Optional[float] = None,
    epsilon: float = 1e-05,
    gamma: float = 0.05,
    enrichment_gamma: float = 0.05,
    p: int = 2,
    n_jobs: int = -1,
    min_seed_cell_rate: float = 0.01,
    max_seed_cell_rate: float = 0.05,
    credible_threshold: float = 0,
    diff_peak_value: difference_peak_optional = 'emp_effect',
    enrichment_threshold: Union[enrichment_optional, float] = 'golden',
    is_ablation: bool = False,
    model_dir: Optional[path] = None,
    save_path: Optional[path] = None,
    is_simple: bool = True,
    is_save_random_walk_model: bool = False,
    is_file_exist_loading: bool = False,
    filename_dict: Optional[dict] = None,
    single_chunk_size: int = 500,
    block_size: int = -1
) -> Tuple[dict, dict, str, bool, str, str, str, str, AnnData, AnnData, AnnData]:

    if adata.shape[0] == 0:
        ul.log(__name__).error("The scATAC-seq data is empty.")
        raise ValueError("The scATAC-seq data is empty.")

    peak_columns: list = list(adata.var.columns)

    if "chr" not in peak_columns or "start" not in peak_columns or "end" not in peak_columns:
        ul.log(__name__).error(
            f"The peaks information {peak_columns} in data `adata` must include three columns: "
            f"`chr`, `start` and `end`. (It is recommended to use the `fl.read_sc_atac` method.)"
        )
        raise ValueError(
            f"The peaks information {peak_columns} in data `adata` must include three columns: "
            f"`chr`, `start` and `end`. (It is recommended to use the `fl.read_sc_atac` method.)"
        )

    if batch_key is not None and batch_key not in adata.obs.columns:
        ul.log(__name__).error(f"The cells information {adata.obs.columns} in data `adata` must include the {batch_key} column.")
        raise ValueError(f"The cells information {adata.obs.columns} in data `adata` must include the {batch_key} column.")

    if cell_rate is not None:

        if cell_rate <= 0 or cell_rate >= 1:
            ul.log(__name__).error("The parameter of `cell_rate` should be between 0 and 1.")
            raise ValueError("The parameter of `cell_rate` should be between 0 and 1.")

    if peak_rate is not None:

        if peak_rate <= 0 or peak_rate >= 1:
            ul.log(__name__).error("The parameter of `peak_rate` should be between 0 and 1.")
            raise ValueError("The parameter of `peak_rate` should be between 0 and 1.")

    if single_chunk_size <= 0:
        ul.log(__name__).error("The parameter `single_chunk_size` must be greater than zero.")
        raise ValueError("The parameter `single_chunk_size` must be greater than zero.")

    if resolution <= 0:
        ul.log(__name__).error("The parameter `resolution` must be greater than zero.")
        raise ValueError("The parameter `resolution` must be greater than zero.")

    if k <= 0:
        ul.log(__name__).error("The `k` parameter must be a natural number greater than 0.")
        raise ValueError("The `k` parameter must be a natural number greater than 0.")

    if or_k <= 0:
        ul.log(__name__).error("The `or_k` parameter must be a natural number greater than 0.")
        raise ValueError("The `or_k` parameter must be a natural number greater than 0.")

    if k < or_k:
        ul.log(__name__).warning(
            "The parameter value of `or_k` is greater than the parameter value of `k`, "
            "which is highly likely to result in poor performance."
        )

    if weight < 0 or weight > 1:
        ul.log(__name__).error("The parameter of `weight` should be between 0 and 1.")
        raise ValueError("The parameter of `weight` should be between 0 and 1.")

    if gamma < 0 or gamma > 1:
        ul.log(__name__).error("The parameter of `gamma` should be between 0 and 1.")
        raise ValueError("The parameter of `gamma` should be between 0 and 1.")

    if enrichment_gamma < 0 or enrichment_gamma > 1:
        ul.log(__name__).error("The parameter of `enrichment_gamma` should be between 0 and 1.")
        raise ValueError("The parameter of `enrichment_gamma` should be between 0 and 1.")

    if min_seed_cell_rate < 0 or min_seed_cell_rate > 1:
        ul.log(__name__).error("The parameter of `min_seed_cell_rate` should be between 0 and 1.")
        raise ValueError("The parameter of `min_seed_cell_rate` should be between 0 and 1.")

    if max_seed_cell_rate < 0 or max_seed_cell_rate > 1:
        ul.log(__name__).error("The parameter of `max_seed_cell_rate` should be between 0 and 1.")
        raise ValueError("The parameter of `max_seed_cell_rate` should be between 0 and 1.")

    if epsilon > 0.1:
        ul.log(__name__).warning(
            f"Excessive value of parameter `epsilon`=({epsilon}) can lead to "
            f"incorrect iteration and poor enrichment effect."
        )
    elif epsilon <= 0:
        ul.log(__name__).error("The parameter of `epsilon` must be greater than zero.")
        raise ValueError("The parameter of `epsilon` must be greater than zero.")

    if p <= 0:
        ul.log(__name__).error("The `p` parameter must be a natural number greater than 0.")
        raise ValueError("The `p` parameter must be a natural number greater than 0.")
    elif p > 3:
        ul.log(__name__).warning("Suggested value for `p` is 1 or 2.")

    if isinstance(enrichment_threshold, float):

        if enrichment_threshold <= 0 or enrichment_threshold >= np.log1p(1):
            ul.log(__name__).warning("The `enrichment_threshold` parameter is not set within the range of (0, log1p(1)), this parameter will become invalid.")
            ul.log(__name__).warning("It is recommended to set the `enrichment_threshold` parameter to the 'golden' value.")

    elif enrichment_threshold not in ["golden", "half", "e", "pi", "none"]:
        raise ValueError(
            f"Invalid enrichment settings. The string type in the `enrichment_threshold` parameter only supports the following parameter "
            f"'golden', 'half', 'e', 'pi', 'none',  Alternatively, input a floating-point type value within the range of (0, log1p(1))"
        )

    if diff_peak_value not in ['emp_effect', 'bayes_factor', 'emp_prob1', 'all']:
        ul.log(__name__).error("The `diff_peak_value` parameter only supports one of the {'emp_effect', 'bayes_factor', 'emp_prob1', 'all'} values.")
        raise ValueError("The `diff_peak_value` parameter only supports one of the {'emp_effect', 'bayes_factor', 'emp_prob1', 'all'} values.")

    # get cache path
    cache_path = str(ul.project_cache_path)
    ul.file_method(__name__).makedirs(cache_path)

    # Assign a name to the formed document
    cache_path_dict: dict = {
        "atac_overlap": os.path.join(cache_path, "atac_overlap"),
        "init_score": os.path.join(cache_path, "init_score"),
        "random_walk": os.path.join(cache_path, "random_walk"),
        "trs": os.path.join(cache_path, "trs")
    }

    # parameter information
    params: dict = {
        "cell_rate": cell_rate,
        "peak_rate": peak_rate,
        "single_chunk_size": single_chunk_size,
        "max_epochs": int(max_epochs),
        "lr": lr,
        "batch_size": batch_size,
        "eps": eps,
        "early_stopping": early_stopping,
        "early_stopping_patience": early_stopping_patience,
        "batch_key": batch_key,
        "resolution": resolution,
        "k": k,
        "or_k": or_k,
        "weight": weight,
        "laplacian_gamma": laplacian_gamma,
        "epsilon": epsilon,
        "gamma": gamma,
        "enrichment_gamma": enrichment_gamma,
        "p": p,
        "n_jobs": n_jobs,
        "min_seed_cell_rate": min_seed_cell_rate,
        "max_seed_cell_rate": max_seed_cell_rate,
        "credible_threshold": credible_threshold,
        "enrichment_threshold": enrichment_threshold,
        "diff_peak_value": diff_peak_value,
        "is_ablation": is_ablation,
        "model_dir": str(model_dir),
        "save_path": str(save_path),
        "cache_path": str(cache_path),
        "is_simple": is_simple,
        "is_save_random_walk_model": is_save_random_walk_model,
        "is_file_exist_loading": is_file_exist_loading,
        "filename_dict": filename_dict,
        "block_size": block_size
    }

    """
    Save information
    """

    if save_path is not None:
        save_path = str(save_path)
        ul.file_method(__name__).makedirs(save_path)
    else:
        is_file_exist_loading = False

    if filename_dict is None:
        filename_dict = {
            "sc_atac": "sc_atac.h5ad",
            "da_peaks": "da_peaks.h5ad",
            "atac_overlap": "atac_overlap.h5ad",
            "init_score": "init_score.h5ad",
            "cc_data": "cc_data.h5ad",
            "random_walk": "random_walk.h5ad",
            "trs": "trs.h5ad"
        }

    # Assign a name to the formed document
    adata_save_file = os.path.join(save_path, "sc_atac.h5ad" if "sc_atac" not in filename_dict else str(filename_dict["sc_atac"])) if save_path is not None else None
    da_peaks_save_file = os.path.join(save_path, "da_peaks.h5ad" if "da_peaks" not in filename_dict else str(filename_dict["da_peaks"])) if save_path is not None else None
    atac_overlap_save_file = os.path.join(save_path, "atac_overlap.h5ad" if "atac_overlap" not in filename_dict else str(filename_dict["atac_overlap"])) if save_path is not None else None
    init_score_save_file = os.path.join(save_path, "init_score.h5ad" if "init_score" not in filename_dict else str(filename_dict["init_score"])) if save_path is not None else None
    cc_data_save_file = os.path.join(save_path, "cc_data.h5ad" if "cc_data" not in filename_dict else str(filename_dict["cc_data"])) if save_path is not None else None
    random_walk_save_file = os.path.join(save_path, "random_walk.pkl" if "random_walk" not in filename_dict else str(filename_dict["random_walk"])) if save_path is not None else None
    trs_save_file = os.path.join(save_path, "trs.h5ad" if "trs" not in filename_dict else str(filename_dict["trs"])) if save_path is not None else None

    """
    1. Filter scATAC-seq data, PoissonVI
    """

    adata_is_read: bool = False
    da_peaks_is_read: bool = False

    if is_file_exist_loading:
        if os.path.exists(adata_save_file):
            adata = read_h5ad(adata_save_file)
            adata_is_read = True

            if "step" not in adata.uns.keys():
                filter_data(adata, cell_rate=cell_rate, peak_rate=peak_rate)
                adata_is_read = False
        else:
            filter_data(adata, cell_rate=cell_rate, peak_rate=peak_rate)

        if os.path.exists(da_peaks_save_file) and adata.uns["step"] == 1:
            da_peaks = read_h5ad(da_peaks_save_file)
            da_peaks_is_read = True
        else:
            # PoissonVI
            da_peaks = poisson_vi(
                adata,
                max_epochs=max_epochs,
                lr=lr,
                batch_size=batch_size,
                eps=eps,
                early_stopping=early_stopping,
                early_stopping_patience=early_stopping_patience,
                batch_key=batch_key,
                resolution=resolution,
                model_dir=model_dir
            )

    else:
        filter_data(adata, cell_rate=cell_rate, peak_rate=peak_rate)
        da_peaks = poisson_vi(
            adata,
            max_epochs=max_epochs,
            lr=lr,
            batch_size=batch_size,
            eps=eps,
            early_stopping=early_stopping,
            early_stopping_patience=early_stopping_patience,
            batch_key=batch_key,
            resolution=resolution,
            model_dir=model_dir
        )

    if save_path is not None:
        if not adata_is_read:
            save_h5ad(adata, file=adata_save_file)

        if not da_peaks_is_read:
            save_h5ad(da_peaks, file=da_peaks_save_file)

    """
    2. Calculate cell-cell correlation. Building a network between cells.
    """

    cc_data_is_read: bool = is_file_exist_loading and os.path.exists(cc_data_save_file)

    if cc_data_is_read:
        cc_data: AnnData = read_h5ad(cc_data_save_file)
    else:
        # cell-cell network
        cc_data = obtain_cell_cell_network(adata=adata, k=k, or_k=or_k, weight=weight, gamma=laplacian_gamma, is_simple=is_simple)

    if save_path is not None and not cc_data_is_read:
        save_h5ad(cc_data, file=cc_data_save_file)

    return (
        cache_path_dict, params, save_path, is_file_exist_loading,
        atac_overlap_save_file, init_score_save_file, random_walk_save_file, trs_save_file,
        adata, da_peaks, cc_data
    )


def core(
    adata: AnnData,
    variants: dict,
    trait_info: DataFrame,
    cell_rate: Optional[float] = None,
    peak_rate: Optional[float] = None,
    max_epochs: int = 500,
    lr: float = 1e-4,
    batch_size: int = 128,
    eps: float = 1e-08,
    early_stopping: bool = True,
    early_stopping_patience: int = 50,
    batch_key: Optional[str] = None,
    resolution: float = 0.5,
    k: int = 30,
    or_k: int = 1,
    weight: float = 0.1,
    laplacian_gamma: Optional[float] = None,
    epsilon: float = 1e-05,
    gamma: float = 0.05,
    enrichment_gamma: float = 0.05,
    p: int = 2,
    n_jobs: int = -1,
    min_seed_cell_rate: float = 0.01,
    max_seed_cell_rate: float = 0.05,
    credible_threshold: float = 0,
    diff_peak_value: difference_peak_optional = 'emp_effect',
    enrichment_threshold: Union[enrichment_optional, float] = 'golden',
    is_ablation: bool = False,
    model_dir: Optional[path] = None,
    save_path: Optional[path] = None,
    is_simple: bool = True,
    is_save_random_walk_model: bool = False,
    is_file_exist_loading: bool = False,
    filename_dict: Optional[dict] = None,
    single_chunk_size: int = 500,
    block_size: int = -1
) -> AnnData:
    """
    The core algorithm of sciv includes the flow of all algorithms, as well as drawing and saving data.
    In the entire algorithm, the samples are in the row position, and the traits or diseases are in the column position,
        while ensuring that there is no interaction between the traits or diseases,
        ensuring the stability of the results;
    Meaning of main variables:
        1. `overlap_adata`, (obs: peaks, var: traits/diseases) Peaks-traits/diseases data obtained by overlaying variant
         data with peaks.
        2. `da_peaks`, (obs: clusters (Leiden), var: peaks) Differential peak data of cell clustering, used for weight
         correction of cells.
        3. `init_score`, (obs: cells, var: traits/diseases) This is the initial TRS data.
        4. `cc_data`, (obs: cells, var: cells) Cell similarity data.
        5. `random_walk`, RandomWalk class.
        6. `trs`, (obs: cells, var: traits/diseases) This is the final TRS data.
    :param adata: scATAC-seq data;
    :param variants: variant data; This data is recommended to be obtained by executing the `fl.read_variants` method.
    :param trait_info: variant annotation file information;
    :param cell_rate: Removing the percentage of cell count in total cell count only takes effect when the min_cells
        parameter is None;
    :param peak_rate: Removing the percentage of peak count in total peak count only takes effect when the min_peaks
        parameter is None;
    :param max_epochs: The maximum number of epochs for PoissonVI training;
    :param lr: Learning rate for optimization;
    :param batch_size: Minibatch size to use during training;
    :param eps: Optimizer eps;
    :param early_stopping: Whether to perform early stopping with respect to the validation set;
    :param early_stopping_patience: How many epochs to wait for improvement before early stopping;
    :param batch_key: Batch information in scATAC-seq data;
    :param resolution: Resolution of the Leiden Cluster. The recommended values are any one of 0.4, 0.9, 1.3, 1.5;
    :param k: When building an mKNN network, the number of nodes connected by each node (and operation);
    :param or_k: When building an mKNN network, the number of nodes connected by each node (or operation);
    :param weight: The weight of interactions or operations;
    :param laplacian_gamma: If None, defaults to 1.0 / n_features. Otherwise, it should be strictly positive;
    :param epsilon: conditions for stopping in random walk;
    :param gamma: reset weight for random walk;
    :param enrichment_gamma: reset weight for random walk for enrichment;
    :param p: Distance used for loss {1: Manhattan distance, 2: Euclidean distance};
    :param n_jobs: The maximum number of concurrently running jobs;
    :param min_seed_cell_rate: The minimum percentage of seed cells in all cells;
    :param max_seed_cell_rate: The maximum percentage of seed cells in all cells;
    :param credible_threshold: The threshold for determining the credibility of enriched cells in the context of
        enrichment, i.e. the threshold for judging enriched cells;
    :param diff_peak_value: Specify the correction value in peak correction of clustering type differences.
        {'emp_effect', 'bayes_factor', 'emp_prob1'}
    :param enrichment_threshold: Only by setting a threshold for the standardized output TRS can a portion of the enrichment
        results be obtained. Parameters support string types {'golden', 'half', 'e', 'pi', 'none'}, or valid floating-point types
        within the range of (0, log1p(1)).
    :param is_ablation: True represents obtaining the results of the ablation experiment. This parameter is limited by
        the `is_simple` parameter, and its effectiveness requires setting `is_simple` to `False`;
    :param model_dir: The folder name saved by the training module;
        It is worth noting that if the training model file (`model.pt`) exists in this path, it will be automatically read and skip
        the training of `PoissonVI` model.
    :param save_path: Save path for process files and result files;
    :param is_simple: True represents not adding unnecessary intermediate variables, only adding the final result.
        It is worth noting that when set to `True`, the `is_ablation` parameter will become invalid, and when set to
        `False`, `is_ablation` will only take effect;
    :param is_save_random_walk_model: Default to `False`, do not save random walk model. When setting `True`, please
        ensure sufficient storage as the saved `pkl` file is relatively large.
    :param is_file_exist_loading: By default, the file will be overwritten. When set to `True`, if the file exists, the
        process will be skipped and the file will be directly read as the result;
    :param single_chunk_size: The size of a single chunk;
    :param filename_dict: The name of the file that exists.
        default: {
            "sc_atac": "sc_atac.h5ad",
            "da_peaks": "da_peaks.h5ad",
            "atac_overlap": "atac_overlap.h5ad",
            "init_score": "init_score.h5ad",
            "cc_data": "cc_data.h5ad",
            "random_walk": "random_walk.h5ad",
            "trs": "trs.h5ad"
        }
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        By sacrificing time and space to reduce memory consumption to a certain extent.
        If the value is less than or equal to zero, no block operation will be performed.
    :return: `trs`, (obs: cells, var: traits/diseases) This is the final TRS data.
    """

    # start time
    start_time = time.time()

    if len(variants.keys()) == 0:
        ul.log(__name__).error("The number of mutations is empty.")
        raise ValueError("The number of mutations is empty.")

    _trait_count_ = trait_info.shape[0]

    if len(variants.keys()) != _trait_count_:
        ul.log(__name__).error(
            "The parameters `variants` and `trait_info` are inconsistent. "
            "These two parameters can be obtained using method `fl.read_variants`."
        )
        raise ValueError(
            "The parameters `variants` and `trait_info` are inconsistent. "
            "These two parameters can be obtained using method `fl.read_variants`."
        )

    (
        cache_path_dict, params, save_path, is_file_exist_loading,
        atac_overlap_save_file, init_score_save_file, random_walk_save_file, trs_save_file,
        adata, da_peaks, cc_data
    ) = _check_and_run_two_step_(
        adata=adata,
        cell_rate=cell_rate,
        peak_rate=peak_rate,
        max_epochs=max_epochs,
        lr=lr,
        batch_size=batch_size,
        eps=eps,
        early_stopping=early_stopping,
        early_stopping_patience=early_stopping_patience,
        batch_key=batch_key,
        resolution=resolution,
        k=k,
        or_k=or_k,
        weight=weight,
        laplacian_gamma=laplacian_gamma,
        epsilon=epsilon,
        gamma=gamma,
        p=p,
        n_jobs=n_jobs,
        min_seed_cell_rate=min_seed_cell_rate,
        max_seed_cell_rate=max_seed_cell_rate,
        credible_threshold=max_seed_cell_rate,
        enrichment_threshold=enrichment_threshold,
        diff_peak_value=diff_peak_value,
        is_ablation=is_ablation,
        model_dir=model_dir,
        save_path=save_path,
        is_simple=is_simple,
        is_save_random_walk_model=is_save_random_walk_model,
        is_file_exist_loading=is_file_exist_loading,
        filename_dict=filename_dict,
        single_chunk_size=single_chunk_size,
        block_size=block_size
    )

    """
    3, 4, 5 steps
    """
    variants_key_list: list = list(trait_info["id"])
    # Quantity of traits
    trait_size: int = trait_info.shape[0]

    # Determine whether it is necessary to read the file
    overlap_is_read: bool = is_file_exist_loading and os.path.exists(atac_overlap_save_file)
    init_score_is_read: bool = is_file_exist_loading and os.path.exists(init_score_save_file)

    # Number of Blocks
    chunk_size: int = int(np.ceil(trait_size / single_chunk_size))

    overlap_adata: Union[AnnData, None] = None
    init_score: Union[AnnData, None] = None

    # overlap
    if overlap_is_read:
        overlap_adata: AnnData = read_h5ad(atac_overlap_save_file)

        if chunk_size > 1:

            if overlap_adata.var.shape[0] != _trait_count_:
                ul.log(__name__).error(
                    f"The number of diseases read from file `atac_overlap.h5ad` are inconsistent with the input ({overlap_adata.var.shape[0]} != {_trait_count_}). "
                    f"Please check and verify. If the verification is not as expected, file `atac_overlap.h5ad` needs to be moved or deleted."
                )
                raise ValueError(
                    f"The number of diseases read from file `atac_overlap.h5ad` are inconsistent with the input ({overlap_adata.var.shape[0]} != {_trait_count_}). "
                    f"Please check and verify. If the verification is not as expected, file `atac_overlap.h5ad` needs to be moved or deleted."
                )

        else:

            if overlap_adata.var.shape[0] != _trait_count_:
                ul.log(__name__).warning(
                    f"The number of diseases read from file `atac_overlap.h5ad` are inconsistent with the input ({overlap_adata.var.shape[0]} != {_trait_count_}). "
                    f"Please check and verify. If the verification is not as expected, file `atac_overlap.h5ad` needs to be moved or deleted."
                )

    if init_score_is_read:
        init_score: AnnData = read_h5ad(init_score_save_file)

        if chunk_size > 1:

            if init_score.var.shape[0] != _trait_count_:
                ul.log(__name__).warning(
                    f"The number of diseases read from file `init_score.h5ad` are inconsistent with the input ({init_score.var.shape[0]} != {_trait_count_}). "
                    f"Please check and verify. If the verification is not as expected, file `init_score.h5ad` needs to be moved or deleted."
                )
                raise ValueError(
                    f"The number of diseases read from file `init_score.h5ad` are inconsistent with the input ({init_score.var.shape[0]} != {_trait_count_}). "
                    f"Please check and verify. If the verification is not as expected, file `init_score.h5ad` needs to be moved or deleted."
                )

        else:

            if init_score.var.shape[0] != _trait_count_:
                ul.log(__name__).warning(
                    f"The number of diseases read from file `init_score.h5ad` are inconsistent with the input ({init_score.var.shape[0]} != {_trait_count_}). "
                    f"Please check and verify. If the verification is not as expected, file `init_score.h5ad` needs to be moved or deleted."
                )

    if chunk_size > 1:

        # Create cache container folder
        for _path_ in cache_path_dict.values():
            ul.file_method(__name__).makedirs(_path_)

        ul.log(__name__).info(f"Due to excessive traits/diseases, divide and conquer. A total of {chunk_size} blocks need to be processed, with {single_chunk_size} elements per block.")
        # Separate execution
        for chunk in range(chunk_size):
            # Index of the start and end of the traits obtained
            _start_ = chunk * single_chunk_size
            _end_ = _start_ + single_chunk_size if trait_size > _start_ + single_chunk_size else trait_size
            ul.log(__name__).info(f"Processing blocks from {_start_ + 1} to {_end_}")

            # chunk cache file
            _chunk_atac_overlap_save_file_ = os.path.join(cache_path_dict["atac_overlap"], f"atac_overlap_{chunk}.h5ad")
            _chunk_init_score_save_file_ = os.path.join(cache_path_dict["init_score"], f"init_score_{chunk}.h5ad")
            _chunk_random_walk_save_file_ = os.path.join(cache_path_dict["random_walk"], f"random_walk_{chunk}.pkl")
            _chunk_trs_save_file_ = os.path.join(cache_path_dict["trs"], f"trs_{chunk}.h5ad")

            # get variant info
            _chunk_variants_key_list_ = variants_key_list[_start_:_end_]
            _chunk_variants_: dict = {key: variants[key] for key in _chunk_variants_key_list_}
            _chunk_trait_info_: DataFrame = trait_info[trait_info["id"].isin(_chunk_variants_key_list_)]
            del _chunk_variants_key_list_

            # Determine whether the final result has been generated, and if it has, skip all intermediate calculation processes
            _chunk_overlap_is_read_: bool = is_file_exist_loading and os.path.exists(_chunk_atac_overlap_save_file_)
            _chunk_init_score_is_read_: bool = is_file_exist_loading and os.path.exists(_chunk_init_score_save_file_)
            _chunk_random_walk_is_read_: bool = is_file_exist_loading and os.path.exists(_chunk_random_walk_save_file_) and is_save_random_walk_model
            _chunk_trs_is_read_: bool = is_file_exist_loading and os.path.exists(_chunk_trs_save_file_)

            if _chunk_trs_is_read_:
                ul.log(__name__).warning(f"{_chunk_trs_save_file_} result file already exists, so skip this calculation process.")
                continue

            """
            3. Overlap regional data and mutation data and sum the PP values of all mutations in a region 
            as the values for that region
            """

            # overlap
            if overlap_is_read:
                _chunk_overlap_adata_: AnnData = overlap_adata[:, _start_:_end_]
            elif _chunk_overlap_is_read_:
                _chunk_overlap_adata_: AnnData = read_h5ad(_chunk_atac_overlap_save_file_)

                if _chunk_overlap_adata_.var.shape[0] != (_end_ - _start_):
                    ul.log(__name__).warning(
                        f"The number of diseases read from file `{_chunk_atac_overlap_save_file_}` are inconsistent with the input ({_chunk_overlap_adata_.var.shape[0]} != {_end_ - _start_}) (chunk: {chunk}). "
                        f"Please check and verify. If the verification is not as expected, file `{_chunk_atac_overlap_save_file_}` needs to be moved or deleted."
                    )

            else:
                _chunk_overlap_adata_: AnnData = overlap_sum(adata, _chunk_variants_, _chunk_trait_info_)
                save_h5ad(_chunk_overlap_adata_, file=_chunk_atac_overlap_save_file_)

            del _chunk_overlap_is_read_, _chunk_atac_overlap_save_file_

            """
            4. Calculate the initial trait- or disease-related cell score with weight
            """

            # overlap
            if init_score_is_read:
                _chunk_init_score_: AnnData = init_score[:, _start_:_end_]
            elif _chunk_init_score_is_read_:
                _chunk_init_score_: AnnData = read_h5ad(_chunk_init_score_save_file_)

                if _chunk_init_score_.var.shape[0] != (_end_ - _start_):
                    ul.log(__name__).warning(
                        f"The number of diseases read from file `{_chunk_init_score_save_file_}` are inconsistent with the input ({_chunk_init_score_.var.shape[0]} != {_end_ - _start_}) (chunk: {chunk}). "
                        f"Please check and verify. If the verification is not as expected, file `{_chunk_init_score_save_file_}` needs to be moved or deleted."
                    )

            else:
                # intermediate score data, integration data
                _chunk_init_score_: AnnData = calculate_init_score_weight(
                    adata=adata,
                    da_peaks_adata=da_peaks,
                    overlap_adata=_chunk_overlap_adata_,
                    diff_peak_value=diff_peak_value,
                    is_simple=is_simple,
                    block_size=block_size
                )
                save_h5ad(_chunk_init_score_, file=_chunk_init_score_save_file_)

            del _chunk_overlap_adata_, _chunk_init_score_is_read_, _chunk_init_score_save_file_

            """
            5. Random walk
            """

            if _chunk_random_walk_is_read_:
                _chunk_random_walk_: RandomWalk = read_pkl(_chunk_random_walk_save_file_)
            else:
                # random walk
                # noinspection DuplicatedCode
                _chunk_random_walk_: RandomWalk = RandomWalk(
                    cc_adata=cc_data,
                    init_status=_chunk_init_score_,
                    epsilon=epsilon,
                    gamma=gamma,
                    enrichment_gamma=enrichment_gamma,
                    p=p,
                    n_jobs=n_jobs,
                    min_seed_cell_rate=min_seed_cell_rate,
                    max_seed_cell_rate=max_seed_cell_rate,
                    credible_threshold=credible_threshold,
                    enrichment_threshold=enrichment_threshold,
                    is_ablation=is_ablation,
                    is_simple=is_simple
                )

                if is_save_random_walk_model:
                    save_pkl(_chunk_random_walk_, save_file=_chunk_random_walk_save_file_)

            del _chunk_init_score_, _chunk_random_walk_is_read_, _chunk_random_walk_save_file_

            if not _chunk_trs_is_read_:
                _chunk_trs_: AnnData = _run_random_walk_(_chunk_random_walk_, is_ablation, is_simple)
                _chunk_params_: dict = params.copy()
                _chunk_params_.update({"_start_": _start_})
                _chunk_params_.update({"_end_": _end_})
                # Save parameters
                _chunk_trs_.uns["params"] = _chunk_params_
                del _chunk_params_
                # save result
                save_h5ad(_chunk_trs_, file=_chunk_trs_save_file_)
                del _chunk_trs_

            del _chunk_trs_is_read_, _chunk_random_walk_, _chunk_trs_save_file_

        if save_path is not None:

            """
            (Merge) 3. Overlap regional data and mutation data and sum the PP values of all mutations in a region 
            as the values for that region
            """

            _chunk_atac_overlap_adata_list_: list[AnnData] = []
            ul.log(__name__).info(f"Merge peak-trait/disease files.")
            for chunk in tqdm(range(chunk_size)):
                # chunk cache file
                _chunk_atac_overlap_save_file_ = os.path.join(cache_path_dict["atac_overlap"], f"atac_overlap_{chunk}.h5ad")
                _chunk_atac_overlap_adata_ = read_h5ad(_chunk_atac_overlap_save_file_, is_verbose=False)
                _chunk_atac_overlap_adata_list_.append(_chunk_atac_overlap_adata_)
                del _chunk_atac_overlap_save_file_, _chunk_atac_overlap_adata_

            # save atac_overlap
            _chunk_atac_overlap_adata_all_: AnnData = ad.concat(_chunk_atac_overlap_adata_list_, axis=1)
            del _chunk_atac_overlap_adata_list_
            _chunk_atac_overlap_adata_all_.var = trait_info.copy()
            _chunk_atac_overlap_adata_all_.uns["is_overlap"] = True
            save_h5ad(_chunk_atac_overlap_adata_all_, atac_overlap_save_file)
            del _chunk_atac_overlap_adata_all_

            # delete cache data
            ul.log(__name__).info(f"Clear cache file information: {cache_path_dict['atac_overlap']}")
            shutil.rmtree(cache_path_dict["atac_overlap"])

            """
            (Merge) 4. Calculate the initial trait- or disease-related cell score with weight
            """

            # merge init_score
            _chunk_init_score_adata_list_: list[AnnData] = []
            ul.log(__name__).info(f"Merge iTRS files.")
            for chunk in tqdm(range(chunk_size)):
                # chunk cache file
                _chunk_init_score_save_file_ = os.path.join(cache_path_dict["init_score"], f"init_score_{chunk}.h5ad")
                _chunk_init_score_adata_ = read_h5ad(_chunk_init_score_save_file_, is_verbose=False)
                _chunk_init_score_adata_list_.append(_chunk_init_score_adata_)
                del _chunk_init_score_save_file_, _chunk_init_score_adata_

            # save init_score
            _chunk_init_score_adata_all_: AnnData = ad.concat(_chunk_init_score_adata_list_, axis=1)
            del _chunk_init_score_adata_list_
            _chunk_init_score_adata_all_.obs = adata.obs.copy()
            _chunk_init_score_adata_all_.var = trait_info.copy()
            save_h5ad(_chunk_init_score_adata_all_, init_score_save_file)
            del _chunk_init_score_adata_all_

            # delete cache data
            ul.log(__name__).info(f"Clear cache file information: {cache_path_dict['init_score']}")
            shutil.rmtree(cache_path_dict["init_score"])

        """
        (Merge) 5. Random walk and result files
        """

        # merge trs
        _chunk_trs_adata_list_: list[AnnData] = []
        # Separate execution
        ul.log(__name__).info(f"Merge TRS files.")
        for chunk in tqdm(range(chunk_size)):
            # chunk cache file
            _chunk_trs_save_file_ = os.path.join(cache_path_dict["trs"], f"trs_{chunk}.h5ad")
            _chunk_trs_adata_ = read_h5ad(_chunk_trs_save_file_, is_verbose=False)
            _chunk_trs_adata_list_.append(_chunk_trs_adata_)
            del _chunk_trs_save_file_, _chunk_trs_adata_

        # save trs
        trs: AnnData = ad.concat(_chunk_trs_adata_list_, axis=1)
        del _chunk_trs_adata_list_
        trs.obs = adata.obs.copy()
        trs.var = trait_info.copy()

        # start time
        elapsed_time = time.time() - start_time

        params.update({"chunk_size": chunk_size})
        params.update({"elapsed_time": elapsed_time})
        # Save parameters
        trs.uns["params"] = params
        trs.uns["variants"] = variants
        trs.uns["trait_info"] = trait_info
        del params, variants, trait_info

        # delete cache data
        ul.log(__name__).info(f"Clear cache file information: {cache_path_dict['trs']}")
        shutil.rmtree(cache_path_dict["trs"])

        if save_path is not None:
            save_h5ad(trs, file=trs_save_file)

            if is_save_random_walk_model:
                _chunk_random_walk_dict_: dict = {}
                ul.log(__name__).info(f"Merge random walk model files.")
                for chunk in tqdm(range(chunk_size)):
                    _start_ = chunk * single_chunk_size
                    _end_ = min(_start_ + single_chunk_size, trait_size)

                    # chunk cache file
                    _chunk_random_walk_save_file_ = os.path.join(cache_path_dict["random_walk"], f"random_walk_{chunk}.pkl")
                    _chunk_random_walk_data_ = read_pkl(_chunk_random_walk_save_file_, is_verbose=False)
                    _chunk_random_walk_dict_.update({f"{_start_}_{_end_}": _chunk_random_walk_data_})
                    del _chunk_random_walk_save_file_, _chunk_random_walk_data_

                save_pkl(_chunk_random_walk_dict_, save_file=random_walk_save_file)

                # delete cache data
                ul.log(__name__).info(f"Clear cache file information: {cache_path_dict['random_walk']}")
                shutil.rmtree(cache_path_dict["random_walk"])

        # Delete cache files
        for _path_ in cache_path_dict.values():
            if os.path.exists(_path_):
                shutil.rmtree(_path_)

    else:

        """
        3. Overlap regional data and mutation data and sum the PP values of all mutations 
        in a region as the values for that region
        """

        # overlap
        if not overlap_is_read:
            overlap_adata: AnnData = overlap_sum(adata, variants, trait_info)

        if save_path is not None and not overlap_is_read:
            save_h5ad(overlap_adata, file=atac_overlap_save_file)

        del overlap_is_read

        """
        4. Calculate the initial trait relevance scores for each cell
        """

        if not init_score_is_read:
            # intermediate score data, integration data
            init_score: AnnData = calculate_init_score_weight(
                adata=adata,
                da_peaks_adata=da_peaks,
                overlap_adata=overlap_adata,
                diff_peak_value=diff_peak_value,
                is_simple=is_simple,
                block_size=block_size
            )

        if save_path is not None and not init_score_is_read:
            save_h5ad(init_score, file=init_score_save_file)

        del init_score_is_read, da_peaks, overlap_adata

        """
        5. Random walk
        """

        random_walk_is_read: bool = is_file_exist_loading and os.path.exists(random_walk_save_file) and is_save_random_walk_model

        if random_walk_is_read:
            random_walk: RandomWalk = read_pkl(random_walk_save_file)
        else:
            # random walk
            # noinspection DuplicatedCode
            random_walk: RandomWalk = RandomWalk(
                cc_adata=cc_data,
                init_status=init_score,
                epsilon=epsilon,
                gamma=gamma,
                enrichment_gamma=enrichment_gamma,
                p=p,
                n_jobs=n_jobs,
                min_seed_cell_rate=min_seed_cell_rate,
                max_seed_cell_rate=max_seed_cell_rate,
                credible_threshold=credible_threshold,
                enrichment_threshold=enrichment_threshold,
                is_ablation=is_ablation,
                is_simple=is_simple
            )

            if save_path is not None and random_walk_is_read:
                save_pkl(random_walk, save_file=random_walk_save_file)

        del random_walk_is_read, init_score, cc_data

        trs = _run_random_walk_(random_walk, is_ablation, is_simple)

        # start time
        elapsed_time = time.time() - start_time

        params.update({"chunk_size": chunk_size})
        params.update({"elapsed_time": elapsed_time})
        # Save parameters
        trs.uns["params"] = params
        trs.uns["variants"] = variants
        trs.uns["trait_info"] = trait_info
        del params, variants, trait_info

        if save_path is not None:
            # save result
            save_h5ad(trs, file=trs_save_file)

    return trs


def association_score(
    adata: AnnData,
    score_name: str = "association_score",
    layer: str = "trs_source",
    axis: Literal[0, 1] = 0
) -> None:
    trs_source = to_dense(adata.layers[layer], is_array=True)

    trs_source_copy = trs_source.copy()
    trs_source_copy[trs_source_copy > 0] = 1

    trs_count_sum = trs_source_copy.sum(axis=axis)
    trs_count_sum[trs_count_sum == 0] = 1
    relevance_value = trs_source.sum(axis=axis) / trs_count_sum

    if axis == 0:
        adata.var[score_name] = np.array(relevance_value).flatten() * adata.shape[1]
        ul.log(__name__).info(f"View this related result `adata.var[{score_name}]`.")
    elif axis == 1:
        adata.obs[score_name] = np.array(relevance_value).flatten() * adata.shape[0]
        ul.log(__name__).info(f"View this related result `adata.obs[{score_name}]`.")
    else:
        ul.log(__name__).error("The `axis` parameter supports only 0 and 1.")
        raise ValueError("The `axis` parameter supports only 0 and 1.")

    sorted_indices = np.argsort(relevance_value)[::,]
    ranks = np.zeros_like(relevance_value).tolist()

    for rank, index in enumerate(sorted_indices, start=1):
        ranks[index] = rank

    adata.var["rank"] = ranks
    adata.uns["association_score"] = {
        "layer": layer,
        "axis": axis,
        "causal_variant_sets_count": len(ranks)
    }


def knock(
    trs: AnnData,
    sc_atac: AnnData,
    knock_trait: str,
    knock_info: dict[str, Union[str, collection]],
    knock_value: float = 0,
    is_add_control: bool = False
) -> AnnData:

    if "params" not in trs.uns:
        ul.log(__name__).error("`params` is not in `trs.uns`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")
        raise ValueError("`params` is not in `trs.uns`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")

    if "variants" not in trs.uns:
        ul.log(__name__).error("`variants` is not in `trs.uns`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")
        raise ValueError("`variants` is not in `trs.uns`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")

    if "trait_info" not in trs.uns:
        ul.log(__name__).error("`trait_info` is not in `trs.uns`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")
        raise ValueError("`trait_info` is not in `trs.uns`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")

    if "trs_source" not in trs.layers:
        ul.log(__name__).error("`trs_source` is not in `trs.layers`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")
        raise ValueError("`trs_source` is not in `trs.layers`, please execute function `ml.core` first to obtain the result as input for the `trs` parameter.")

    if knock_value >= 1E-3:
        ul.log(__name__).warning("The value set for `knock_value` here is greater than 1e-3, which can easily fail to achieve the desired effect.")

    # param information
    params = trs.uns["params"]

    # variant information
    variants = trs.uns["variants"]
    trait_info = trs.uns["trait_info"]

    knock_variants: dict = {}
    knock_variants_bg: dict = {}

    if knock_trait not in trs.var["id"]:
        ul.log(__name__).error(f"`{knock_trait}` trait or disease does not exist.")
        raise ValueError(f"`{knock_trait}` trait or disease does not exist.")

    trait_obs = variants[knock_trait].obs
    knock_variant: AnnData = variants[knock_trait].copy()
    knock_variant_value = to_dense(knock_variant.X)

    _trait_info_ = trait_info[trait_info["id"] == knock_trait].values[0]
    knock_trait_info = pd.DataFrame(columns=trait_info.columns)

    ul.log(__name__).info(f"Knockdown or knockout settings for `{knock_trait}` trait or disease.")

    for k, v in knock_info.items():

        if isinstance(v, str):
            if v not in trait_obs["rsId"].tolist():
                ul.log(__name__).error(f"`{v}` variant does not exist in `{knock_trait}` trait or disease")
                raise ValueError(f"`{v}` variant does not exist in `{knock_trait}` trait or disease")
        elif isinstance(v, collection):
            if not set(v).issubset(set(trait_obs["rsId"].tolist())):
                ul.log(__name__).error(f"`{v}` variants does not exist in `{knock_trait}` trait or disease")
                raise ValueError(f"`{v}` variants does not exist in `{knock_trait}` trait or disease")

        need_k_index = trait_obs["rsId"].isin(list([v] if isinstance(v, str) else v)).values
        knock_variant_k = knock_variant.copy()
        knock_variant_k_value = knock_variant_value.copy()
        knock_variant_k_value[need_k_index, :] = knock_value
        knock_variant_k.X = to_sparse(knock_variant_k_value)
        knock_variants[k] = knock_variant_k

        knock_variant_k_bg = knock_variant.copy()
        knock_variant_k_value_bg = knock_variant_value.copy()
        knock_variant_k_value_bg[~need_k_index, :] = knock_value
        knock_variant_k_bg.X = to_sparse(knock_variant_k_value_bg)
        knock_variants_bg[k] = knock_variant_k_bg

        _trait_info_[0] = k
        knock_trait_info.loc[knock_trait_info.shape[0], :] = _trait_info_

    knock_trait_info.index = knock_trait_info["id"].astype(str)

    (
        cache_path_dict, params, save_path, is_file_exist_loading, _, _, _, _, adata, da_peaks, cc_data
    ) = _check_and_run_two_step_(
        adata=sc_atac,
        cell_rate=params["cell_rate"] if "cell_rate" in params else None,
        peak_rate=params["peak_rate"] if "peak_rate" in params else None,
        max_epochs=params["max_epochs"],
        lr=params["lr"] if "lr" in params else None,
        batch_size=params["batch_size"] if "batch_size" in params else None,
        eps=params["eps"] if "eps" in params else None,
        early_stopping=params["early_stopping"] if "early_stopping" in params else None,
        early_stopping_patience=params["early_stopping_patience"] if "early_stopping_patience" in params else None,
        batch_key=params["batch_key"] if "batch_key" in params else None,
        resolution=params["resolution"],
        k=params["k"],
        or_k=params["or_k"],
        weight=params["weight"],
        laplacian_gamma=params["laplacian_gamma"] if "laplacian_gamma" in params else None,
        epsilon=params["epsilon"],
        gamma=params["gamma"],
        p=params["p"],
        n_jobs=params["n_jobs"] if "n_jobs" in params else -1,
        min_seed_cell_rate=params["min_seed_cell_rate"],
        max_seed_cell_rate=params["max_seed_cell_rate"],
        credible_threshold=params["credible_threshold"],
        enrichment_threshold=params["enrichment_threshold"],
        diff_peak_value=params["diff_peak_value"],
        is_ablation=False,
        model_dir=params["model_dir"] if "model_dir" in params else None,
        save_path=params["save_path"] if "save_path" in params else None,
        is_simple=True,
        is_save_random_walk_model=False,
        is_file_exist_loading=True,
        single_chunk_size=params["single_chunk_size"],
        block_size=params["block_size"]
    )

    ul.log(__name__).info(f"Run the process after knocking down or knocking out.")
    knock_overlap_adata: AnnData = overlap_sum(adata, knock_variants, knock_trait_info)

    # intermediate score data, integration data
    knock_init_score: AnnData = calculate_init_score_weight(
        adata=adata,
        da_peaks_adata=da_peaks,
        overlap_adata=knock_overlap_adata,
        diff_peak_value=params["diff_peak_value"],
        is_simple=True,
        block_size=params["block_size"]
    )

    # random walk
    # noinspection DuplicatedCode
    knock_random_walk: RandomWalk = RandomWalk(
        cc_adata=cc_data,
        init_status=knock_init_score,
        epsilon=params["epsilon"],
        gamma=params["gamma"],
        enrichment_gamma=params["enrichment_gamma"],
        p=params["p"],
        n_jobs=params["n_jobs"] if "n_jobs" in params else -1,
        min_seed_cell_rate=params["min_seed_cell_rate"],
        max_seed_cell_rate=params["max_seed_cell_rate"],
        credible_threshold=params["credible_threshold"],
        enrichment_threshold=params["enrichment_threshold"],
        is_ablation=False,
        is_simple=True
    )

    # RUN
    knock_random_walk.run_knock(trs, knock_trait, False)

    if is_add_control:
        knock_random_walk.run_knock(trs, knock_trait, True)

    # Obtain result data
    knock_trs = knock_random_walk.trs_adata

    knock_trs.uns["params"] = {
        "knock_trait": knock_trait,
        "knock_info": knock_info,
        "knock_value": knock_value,
        "is_add_control": is_add_control,
        "run_core_params": params
    }

    trs.uns["is_knock"] = True

    if "pp_sum" in knock_trs.var.columns:
        knock_trs.var["pp_sum"] = knock_trs.var["pp_sum"].astype(float)

    if "pp_mean" in knock_trs.var.columns:
        knock_trs.var["pp_mean"] = knock_trs.var["pp_mean"].astype(float)

    if "count" in knock_trs.var.columns:
        knock_trs.var["count"] = knock_trs.var["count"].astype(int)

    # save result
    if save_path is not None:
        save_h5ad(knock_trs, file=os.path.join(save_path, f"knock_trs_{knock_trait}.h5ad"))

    return knock_trs
