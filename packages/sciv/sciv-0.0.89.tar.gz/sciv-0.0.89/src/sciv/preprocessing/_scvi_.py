# -*- coding: UTF-8 -*-

import os
import warnings
from typing import Optional

import numpy as np
import pandas as pd

from anndata import AnnData

from .. import util as ul
from ..tool import umap, tsne
from ..util import path

__name__: str = "preprocessing_scvi"


def poisson_vi(
    adata: AnnData,
    max_epochs: int = 500,
    lr: float = 1e-4,
    batch_size: int = 128,
    eps: float = 1e-08,
    early_stopping: bool = True,
    early_stopping_patience: int = 50,
    batch_key: Optional[str] = None,
    resolution: float = 0.5,
    dp_delta: float = 0.05,
    latent_name: str = "latent",
    model_dir: Optional[path] = None
) -> AnnData:
    """
    PoissonVI processing of the data results in the current sample representation and peak difference data after Leiden clustering.
    :param adata: processing data;
    :param max_epochs: The maximum number of epochs for PoissonVI training;
    :param lr: Learning rate for optimization;
    :param batch_size: Minibatch size to use during training;
    :param eps: Optimizer eps;
    :param early_stopping: Whether to perform early stopping with respect to the validation set;
    :param early_stopping_patience: How many epochs to wait for improvement before early stopping;
    :param batch_key: Batch information in scATAC-seq data;
    :param resolution: Resolution of the Leiden Cluster;
    :param dp_delta: PeakVI method in differential analysis empirical effect size threshold;
    :param latent_name: The name of latent representation;
    :param model_dir: The folder name saved by the training module;
    :return: Differential peak of clustering types.
    """
    ul.log(__name__).info("Start PoissonVI")

    import scvi
    import scanpy as sc

    if resolution <= 0:
        ul.log(__name__).error("The parameter `resolution` must be greater than zero.")
        raise ValueError("The parameter `resolution` must be greater than zero.")

    if dp_delta <= 0:
        ul.log(__name__).error("The parameter `dp_delta` must be greater than zero.")
        raise ValueError("The parameter `dp_delta` must be greater than zero.")

    if batch_key is not None and batch_key not in adata.obs.columns:
        ul.log(__name__).error(f"The cells information {adata.obs.columns} in data `adata` must include the {batch_key} column.")
        raise ValueError(f"The cells information {adata.obs.columns} in data `adata` must include the {batch_key} column.")

    # PoissonVI, Binarization
    ul.log(__name__).info("Calculate fragment counts matrix.")
    scvi.data.reads_to_fragments(adata)

    def __train__():

        # PoissonVI
        scvi.external.POISSONVI.setup_anndata(adata, layer="fragments", batch_key=batch_key)
        _model_ = scvi.external.POISSONVI(adata)

        try:
            data_splitter_kwargs = {"drop_dataset_tail": True, "drop_last": False}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _model_.train(
                    max_epochs=int(max_epochs),
                    check_val_every_n_epoch=1,
                    accelerator="gpu",
                    devices=-1,
                    datasplitter_kwargs=data_splitter_kwargs,
                    strategy="ddp_notebook_find_unused_parameters_true",
                    lr=lr,
                    batch_size=int(batch_size),
                    eps=eps,
                    early_stopping=early_stopping,
                    early_stopping_patience=int(early_stopping_patience)
                )
        except Exception as ex:

            try:
                ul.log(__name__).warning(f"Multiple GPU failed to run, attempting to run on one card.\n {ex}")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    _model_.train(
                        max_epochs=int(max_epochs),
                        check_val_every_n_epoch=1,
                        lr=lr,
                        batch_size=int(batch_size),
                        eps=eps,
                        early_stopping=early_stopping,
                        early_stopping_patience=int(early_stopping_patience)
                    )
            except Exception as exc:
                ul.log(__name__).warning(f"GPU failed to run, try to switch to CPU running.\n {exc}")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    _model_.to_device('cpu')
                    _model_.train(
                        max_epochs=int(max_epochs),
                        check_val_every_n_epoch=1,
                        lr=lr,
                        batch_size=int(batch_size),
                        eps=eps,
                        early_stopping=early_stopping,
                        early_stopping_patience=int(early_stopping_patience),
                        accelerator="cpu"
                    )

        return _model_

    if model_dir is not None:
        if os.path.exists(os.path.join(model_dir, "model.pt")):
            ul.log(__name__).info(f"Due to the existence of file `model.pt`, it is loaded by default.")
            try:
                model = scvi.external.POISSONVI.load(model_dir, adata=adata)
            except FileExistsError as fee:
                ul.log(__name__).error(f"File `model.pt` failed to load, you can execute `Poisson VI` again by deleting file `model.pt` ({model_dir}/model.pt).\n {fee}")
                raise ValueError(f"File `model.pt` failed to load, you can execute `Poisson VI` again by deleting file `model.pt` ({model_dir}/model.pt).")
        else:
            ul.file_method(__name__).makedirs(model_dir)
            model = __train__()
            model.save(model_dir, overwrite=True)
    else:
        model = __train__()

    # latent space
    latent = model.get_latent_representation()
    adata.obsm[latent_name] = latent

    if "clusters" in adata.obs.columns:
        ul.log(__name__).warning("Due to the original inclusion of the `clusters` column, the original `clusters` column name has been changed to `clusters_x`.")
        adata.obs["clusters_x"] = adata.obs["clusters"]

    ul.log(__name__).info(f"Perform kNN and Leiden clustering.")
    # compute the k-nearest-neighbor graph that is used in both clustering and umap algorithms
    sc.pp.neighbors(adata, use_rep=latent_name)
    # cluster the space (we use a lower resolution to get fewer clusters than the default)
    sc.tl.leiden(adata, key_added="clusters", resolution=resolution)
    adata.obs["clusters"] = adata.obs["clusters"].astype(str)

    # umap
    try:
        data_umap = umap(adata.obsm[latent_name])
        adata.obsm["umap"] = data_umap
        adata.obs["latent_umap1"] = data_umap[:, 0]
        adata.obs["latent_umap2"] = data_umap[:, 1]
    except Exception as e:
        ul.log(__name__).warning(f"UMAP error, your system does not support it, but it does not affect the process. Continue with execution: {e}")

    # tsne
    try:
        data_tsne = tsne(adata.obsm[latent_name])
        adata.obsm["tsne"] = data_tsne
        adata.obs["latent_tsne1"] = data_tsne[:, 0]
        adata.obs["latent_tsne2"] = data_tsne[:, 1]
    except Exception as e:
        ul.log(__name__).warning(f"TSNE error, your system does not support it, but it does not affect the process. Continue with execution: {e}")

    clusters_list = list(set(adata.obs["clusters"]))
    clusters_list.sort()

    adata.uns["poisson_vi"] = {
        "model_dir": model_dir,
        "cluster_size": len(clusters_list),
        "dp_delta": dp_delta,
        "latent_name": latent_name
    }
    peaks_info = adata.var.copy()
    peaks_info["index"] = peaks_info.index
    peaks_info.rename_axis("peak_index", inplace=True)

    matrix_bf = np.ones((len(clusters_list), adata.shape[1]))
    matrix_ep1 = np.ones((len(clusters_list), adata.shape[1]))
    matrix_ee = np.ones((len(clusters_list), adata.shape[1]))

    if len(clusters_list) == 1:
        ul.log(__name__).warning(f"The number of clusters is one, ignoring cluster type correction. It is recommended to increase the `resolution` value to make it effective.")
    else:
        # differential peak
        da_peaks_all: dict = {}

        for cluster in clusters_list:
            ul.log(__name__).info(f"Start difference peak: {cluster}/({', '.join(clusters_list)})")
            clusters_all = clusters_list.copy()
            clusters_all.remove(cluster)

            # differential peak
            try:
                da_peaks = model.differential_accessibility(adata, groupby="clusters", delta=dp_delta, group1=cluster, mode="vanilla", two_sided=False)
            except Exception as e:
                ul.log(__name__).warning(f"GPU failed to run, try to switch to CPU running.\n {e}")
                # PyTorch uses CPU
                model.to_device('cpu')
                da_peaks = model.differential_accessibility(adata, groupby="clusters", delta=dp_delta, group1=cluster, mode="vanilla", two_sided=False)

            da_peaks_all.update({cluster: da_peaks})

        adata.uns["da_peaks"] = da_peaks_all

        for i in range(len(clusters_list)):
            cluster_info = da_peaks_all[clusters_list[i]]
            cluster_info["index"] = cluster_info.index
            cluster_info.rename_axis("cluster_index", inplace=True)
            cluster_info = pd.merge(left=peaks_info, right=cluster_info, left_on="index", right_on="index", how="left")
            matrix_bf[i, :] = cluster_info["bayes_factor"]
            matrix_ep1[i, :] = cluster_info["emp_prob1"]
            matrix_ee[i, :] = cluster_info["emp_effect"]

    ul.log(__name__).info("End PoissonVI")

    obs = pd.DataFrame(clusters_list, columns=["id"])
    obs.index = obs["id"].astype(str)
    da_peaks_adata = AnnData(matrix_ee, obs=obs, var=adata.var)
    da_peaks_adata.layers["bayes_factor"] = matrix_bf
    da_peaks_adata.layers["emp_prob1"] = matrix_ep1
    da_peaks_adata.uns["latent_name"] = latent_name
    da_peaks_adata.uns["dp_delta"] = dp_delta

    adata.uns["step"] = 1
    return da_peaks_adata
