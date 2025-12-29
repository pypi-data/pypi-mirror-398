# -*- coding: UTF-8 -*-

import random
from typing import Union, Tuple, Literal, Optional

from scipy import sparse
from scipy.stats import norm
from tqdm import tqdm

import numpy as np
from anndata import AnnData
import pandas as pd
from pandas import DataFrame

from ._matrix_ import (
    matrix_dot_block_storage,
    vector_multiply_block_storage
)

from .. import util as ul
from ..util import (
    matrix_data,
    to_sparse,
    to_dense,
    sparse_matrix,
    dense_data,
    number,
    collection,
    get_index,
    difference_peak_optional
)

__name__: str = "tool_algorithm"

_Affinity = Literal["nearest_neighbors", "rbf", "precomputed", "precomputed_nearest_neighbors", "jaccard"]
_EigenSolver = Literal["arpack", "lobpcg", "amg"]


def sigmoid(data: Union[collection, matrix_data]) -> Union[collection, matrix_data]:
    return 1 / (1 + np.exp(-data))


def tf_idf(data: matrix_data, ri_sparse: bool = True) -> matrix_data:
    """
    TF-IDF transformer
    :param data: Matrix data that needs to be converted;
    :param ri_sparse: (return_is_sparse) Whether to return sparse matrix.
    :return: Matrix processed by TF-IDF.
    """
    from sklearn.feature_extraction.text import TfidfTransformer

    ul.log(__name__).info("TF-IDF transformer")
    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(to_dense(data, is_array=True))
    return to_sparse(tfidf) if ri_sparse else to_dense(tfidf)


def z_score_normalize(
    data: matrix_data,
    with_mean: bool = True,
    ri_sparse: bool | None = None,
    is_sklearn: bool = False
) -> Union[dense_data, sparse_matrix]:
    """
    Matrix standardization (z-score)
    :param data: Standardized data matrix required.
    :param with_mean: If True, center the data before scaling.
    :param ri_sparse: (return_is_sparse) Whether to return sparse matrix.
    :param is_sklearn: This parameter represents whether to use the sklearn package.
    :return: Standardized matrix.
    """
    ul.log(__name__).info("Matrix z-score standardization")

    if is_sklearn:
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler(with_mean=with_mean)

        if with_mean:
            dense_data_ = to_dense(data, is_array=True)
        else:
            dense_data_ = data

        data = scaler.fit_transform(np.array(dense_data_))
    else:

        if sparse.issparse(data):
            _data_: sparse_matrix = data
            __mean__ = np.mean(_data_.data)
            __std__ = np.std(_data_.data)
            data.data = (_data_.data - __mean__) / (1 if __std__ == 0 else __std__)
            del _data_, __mean__, __std__
        else:
            __mean__ = np.mean(data)
            __std__ = np.std(data)
            data = (data - __mean__) / (1 if __std__ == 0 else __std__)

    return data if ri_sparse is None else (to_sparse(data) if ri_sparse else to_dense(data))


def z_score_marginal(matrix: matrix_data, axis: Literal[0, 1] = 0) -> Tuple[matrix_data, matrix_data]:
    """
    Matrix standardization (z-score, marginal)
    :param matrix: Standardized data matrix required.
    :param axis: Standardize according to which dimension.
    :return: Standardized matrix.
    """
    ul.log(__name__).info("Start marginal z-score")
    matrix = np.matrix(to_dense(matrix))
    # Separate z-score for each element
    __mean__ = np.mean(matrix, axis=axis)
    __std__ = np.std(matrix, axis=axis)
    # Control denominator is not zero
    __std__[__std__ == 0] = 1
    _z_score_ = (matrix - __mean__) / __std__
    ul.log(__name__).info("End marginal z-score")
    return _z_score_, __mean__


def z_score_to_p_value(z_score: matrix_data):
    return 2 * (1 - norm.cdf(abs(z_score)))


def marginal_normalize(matrix: matrix_data, axis: Literal[0, 1] = 0, default: float = 1e-50) -> matrix_data:
    """
    Marginal standardization
    :param matrix: Standardized data matrix required;
    :param axis: Standardize according to which dimension;
    :param default: To prevent division by 0, this value needs to be added to the denominator.
    :return: Standardized data.
    """
    matrix = np.matrix(to_dense(matrix))
    __sum__ = np.sum(matrix, axis=axis)
    return matrix / (__sum__ + default)


def min_max_norm(data: matrix_data, axis: Literal[0, 1, -1] = -1) -> dense_data:
    """
    Calculate min max standardized data
    :param data: input data;
    :param axis: Standardize according to which dimension.
    :return: Standardized data.
    """
    data = to_dense(data, is_array=True)

    # Judgment dimension
    if axis == -1:
        data_extremum = data.max() - data.min()
        if data_extremum == 0:
            data_extremum = 1
        new_data = (data - data.min()) / data_extremum
    elif axis == 0:
        data_extremum = np.array(data.max(axis=axis) - data.min(axis=axis)).flatten()
        data_extremum[data_extremum == 0] = 1
        new_data = (data - data.min(axis=axis).flatten()) / data_extremum
    elif axis == 1:
        data_extremum = np.array(data.max(axis=axis) - data.min(axis=axis)).flatten()
        data_extremum[data_extremum == 0] = 1
        new_data = (data - data.min(axis=axis).flatten()[:, np.newaxis]) / data_extremum[:, np.newaxis]
    else:
        ul.log(__name__).error(
            "The `axis` parameter supports only -1, 0, and 1, while other values will make the `scale` parameter value "
            "equal to 1."
        )
        raise ValueError("The `axis` parameter supports only -1, 0, and 1")

    return new_data


def symmetric_scale(
    data: matrix_data,
    scale: Union[number, collection] = 2.0,
    axis: Literal[0, 1, -1] = -1,
    is_verbose: bool = True
) -> matrix_data:
    """
    Symmetric scale Function
    :param data: input data;
    :param axis: Standardize according to which dimension;
    :param scale: scaling factor.
    :param is_verbose: log information.
    :return: Standardized data
    """

    from scipy import special

    if is_verbose:
        ul.log(__name__).info("Start symmetric scale function")

    # Judgment dimension
    if axis == -1:
        scale = 1 if scale == 0 else scale
        x_data = to_dense(data) / scale
    elif axis == 0:
        scale = to_dense(scale, is_array=True).flatten()
        scale[scale == 0] = 1
        x_data = to_dense(data) / scale
    elif axis == 1:
        scale = to_dense(scale, is_array=True).flatten()
        scale[scale == 0] = 1
        x_data = to_dense(data) / scale[:, np.newaxis]
    else:
        ul.log(__name__).warning(
            "The `axis` parameter supports only -1, 0, and 1, while other values will make the `scale` parameter value "
            "equal to 1."
        )
        x_data = to_dense(data)

    # Record symbol information
    symbol = to_dense(x_data).copy()
    symbol[symbol > 0] = 1
    symbol[symbol < 0] = -1

    # Log1p standardized data
    y_data = np.multiply(x_data, symbol)
    y_data = special.log1p(y_data)
    del x_data

    # Return symbols and make changes and sigmoid mapped data
    z_data = np.multiply(y_data, symbol)

    if is_verbose:
        ul.log(__name__).info("End symmetric scale function")
    return z_data


def mean_symmetric_scale(data: matrix_data, axis: Literal[0, 1, -1] = -1, is_verbose: bool = True) -> matrix_data:
    """
    Calculate the mean symmetric
    :param data: input data;
    :param axis: Standardize according to which dimension.
    :param is_verbose: log information.
    :return: Standardized data after average symmetry.
    """

    # Judgment dimension
    if axis == -1:
        return symmetric_scale(data, np.abs(data).mean(), axis=-1, is_verbose=is_verbose)
    elif axis == 0:
        return symmetric_scale(data, np.abs(data).mean(axis=0), axis=0, is_verbose=is_verbose)
    elif axis == 1:
        return symmetric_scale(data, np.abs(data).mean(axis=1), axis=1, is_verbose=is_verbose)
    else:
        ul.log(__name__).warning("The `axis` parameter supports only -1, 0, and 1")
        raise ValueError("The `axis` parameter supports only -1, 0, and 1")


def coefficient_of_variation(matrix: matrix_data, axis: Literal[0, 1, -1] = 0, default: float = 0) -> Union[
    float, collection]:
    if axis == -1:
        _std_ = np.array(np.std(matrix))
        _mean_ = np.array(np.mean(matrix))

        if _mean_ == 0:
            return default
        else:
            factor = _std_ / _mean_

            if factor == 0:
                return default

            return factor
    else:
        _std_ = np.array(np.std(matrix, axis=axis))
        _mean_ = np.array(np.mean(matrix, axis=axis))
        _mean_[_mean_ == 0] = 1 if default == 0 else default
        # coefficient of variation
        factor = _std_ / _mean_
        factor[_std_ == 0] = default
        return factor


def is_asc_sort(positions_list: list) -> bool:
    """
    Judge whether the site is in ascending order
    :param positions_list: positions list.
    :return: True for ascending order, otherwise False.
    """
    length: int = len(positions_list)

    if length <= 1:
        return True

    tmp = positions_list[0]

    for i in range(1, length):
        if positions_list[i] < tmp:
            return False
        tmp = positions_list[i]

    return True


def lsi(data: matrix_data, n_components: int = 50, is_to_dense: bool = False) -> dense_data:
    """
    SVD LSI
    :param data: input cell feature data;
    :param n_components: Dimensions that need to be reduced to.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Reduced dimensional data (SVD LSI model).
    """

    from sklearn.decomposition import TruncatedSVD

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    if data_x.shape[1] <= n_components:
        ul.log(__name__).info(
            "The features of the data are less than or equal to the `n_components` parameter, ignoring LSI"
        )
        return data_x
    else:
        ul.log(__name__).info("Start LSI")
        svd = TruncatedSVD(n_components=n_components, algorithm='randomized')
        svd_data = svd.fit_transform(data_x)
        ul.log(__name__).info("End LSI")
        return svd_data


def pca(data: matrix_data, n_components: int = 50, is_to_dense: bool = False) -> dense_data:
    """
    PCA
    :param data: input cell feature data;
    :param n_components: Dimensions that need to be reduced to.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Reduced dimensional data.
    """
    from sklearn.decomposition import PCA

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    if data_x.shape[1] <= n_components:
        ul.log(__name__).info(
            "The features of the data are less than or equal to the `n_components` parameter, ignoring PCA"
        )
        return data_x
    else:
        ul.log(__name__).info("Start PCA")
        pca_n = PCA(n_components=n_components)
        pca_data = pca_n.fit_transform(data_x)
        ul.log(__name__).info("End PCA")
        return pca_data


def jaccard_similarity(data: matrix_data, n_jobs: int = -1, is_to_dense: bool = False) -> matrix_data:
    """
    Calculate the Jaccard similarity matrix
    :param data: input cell feature data;
    :param n_jobs: The number of jobs to use for the computation.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    """
    from sklearn.metrics import pairwise_distances
    from sklearn.preprocessing import binarize

    ul.log(__name__).info("Start Jaccard Similarity")
    data = binarize(data, threshold=0.5).astype(bool)

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    jaccard_data = 1 - pairwise_distances(data_x, metric='jaccard', n_jobs=n_jobs)
    ul.log(__name__).info("End Jaccard Similarity")
    return jaccard_data


def spectral_eigenmaps(
    data: matrix_data,
    n_components: int = 30,
    affinity: _Affinity = 'nearest_neighbors',
    eigen_solver: Optional[_EigenSolver] = None,
    n_jobs: int = -1,
    is_to_dense: bool = False
) -> dense_data:
    """
    Spectral Eigenmaps
    :param data: input cell feature data;
    :param n_components: Dimensions that need to be reduced to.
    :param eigen_solver: The eigenvalue decomposition strategy to use.
    :param affinity: method
    :param n_jobs: The number of jobs to use for the computation.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Reduced dimensional data.
    """
    from sklearn.manifold import SpectralEmbedding

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    if data_x.shape[1] <= n_components:
        ul.log(__name__).info(
            "The features of the data are less than or equal to the `n_components` parameter, ignoring Spectral "
            "Eigenmaps."
        )
        return data_x
    else:
        ul.log(__name__).info("Start Spectral Eigenmaps")

        if affinity == 'jaccard':
            affinity_matrix = jaccard_similarity(data=data_x, n_jobs=n_jobs)
            affinity = 'precomputed'
        else:
            affinity_matrix = data_x

        se = SpectralEmbedding(
            n_components=n_components,
            affinity=affinity,
            eigen_solver=eigen_solver,
            n_jobs=n_jobs
        )
        se_data = se.fit_transform(affinity_matrix)
        ul.log(__name__).info("End Spectral Eigenmaps")
        return se_data


def semi_mutual_knn_weight(
    data: matrix_data,
    neighbors: int = 30,
    or_neighbors: int = 1,
    weight: float = 0.1,
    is_for: bool = True,
    is_mknn_fully_connected: bool = True
) -> Tuple[matrix_data, matrix_data]:
    """
    Mutual KNN with weight
    :param data: Input data matrix;
    :param neighbors: The number of nearest neighbors;
    :param or_neighbors: The number of or nearest neighbors;
    :param weight: The weight of interactions or operations;
    :param is_for: Obtain the nearest neighbors of each node from each row of the for loop matrix;
        Setting it to True is very suitable for situations with large samples and insufficient memory.
    :param is_mknn_fully_connected: Is the network of MKNN an all connected graph?
        If the value is True, it ensures that a node is connected to at least the node that is not closest to itself.
        This parameter does not affect the result of SM-KNN (the first result), but only affects the result of
        traditional M-KNN (the second result).
    :return: Adjacency weight matrix
    """
    ul.log(__name__).info("Start semi-mutual KNN")

    if weight < 0 or weight > 1:
        ul.log(__name__).error("The `and_weight` parameter must be between 0 and 1.")
        raise ValueError("The `and_weight` parameter must be between 0 and 1.")

    # Work directly on the sparse matrix to avoid a full dense copy
    if sparse.issparse(data):
        # Keep sparse, set diagonal to 0 efficiently
        data = to_sparse(data).astype(np.float32)
        data.setdiag(0)
        data.eliminate_zeros()
        new_data = data
        del data
    else:
        # Dense case: in-place diagonal zeroing
        new_data = to_dense(data).astype(np.float32)
        del data
        np.fill_diagonal(new_data, 0)

    def _knn_k_(_mat: matrix_data, k: int):
        n_rows = _mat.shape[0]
        adj = sparse.lil_matrix((n_rows, n_rows), dtype=np.int8)

        ul.log(__name__).info("Calculate the k-nearest neighbors of each node.")

        for i in tqdm(range(n_rows)):
            row = np.array(_mat[i]).ravel()

            if row.size <= k:
                adj[i, :] = 1
                adj[i, i] = 0
                continue

            # Partial sorting
            kth = np.partition(row, -k)[-k]
            mask = row >= kth
            mask[i] = False  # remove self
            adj[i, mask] = 1

        return adj.tocsr()

    def _knn(_mat: matrix_data, k: int) -> matrix_data:
        """
        Return k-nearest-neighbor 0/1 adjacency matrix (int8 to save memory).
        Supports both sparse and dense inputs.
        """

        if sparse.issparse(_mat):
            # Sparse path: sort each row's data to find the k-th largest
            _mat = _mat.tocsr(copy=False)
            return _knn_k_(_mat, k)
        else:

            if is_for:
                return _knn_k_(_mat, k)
            else:
                # Dense path: vectorized thresholding
                kth_val = np.sort(_mat, axis=1)[:, -(k + 1)]
                adj = (_mat >= kth_val[:, None]).astype(np.int8)
                np.fill_diagonal(adj, 0)
                return adj

    # Compute adjacency matrices for AND/OR logic
    adj_and = _knn(new_data, neighbors)

    if neighbors == or_neighbors:
        adj_or = adj_and
    else:
        adj_or = _knn(new_data, or_neighbors)

    # Symmetrize
    if sparse.issparse(adj_and):
        adj_and = adj_and.minimum(adj_and.T)
        adj_or = adj_or.maximum(adj_or.T)
    else:
        adj_and = np.minimum(adj_and, adj_and.T)
        adj_or = np.maximum(adj_or, adj_or.T)

    # Weighted combination, float32 is sufficient
    adj_weight = (1 - weight) * adj_and.astype(np.float32) + weight * adj_or.astype(np.float32)

    # Ensure full connectivity if required
    if is_mknn_fully_connected and (or_neighbors == 0 or weight == 0):
        adj_1nn = _knn(new_data, 1)

        if sparse.issparse(adj_and):
            adj_and = adj_and.maximum(adj_1nn)
        else:
            adj_and = np.maximum(adj_and, adj_1nn)

    ul.log(__name__).info("End semi-mutual KNN")
    return adj_weight, adj_and


def k_means(data: matrix_data, n_clusters: int = 8, is_to_dense: bool = False):
    """
    Perform k-means clustering on data
    :param data: Input data matrix;
    :param n_clusters: The number of clusters to form as well as the number of centroids to generate.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Tags after k-means clustering.
    """
    ul.log(__name__).info("Start K-means cluster")
    from sklearn.cluster import KMeans

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    model = KMeans(n_clusters=n_clusters, n_init="auto")
    model.fit(to_dense(data_x, is_array=True))
    labels = model.labels_
    ul.log(__name__).info("End K-means cluster")
    return labels


def spectral_clustering(
    data: matrix_data,
    n_clusters: int = 8,
    n_components=30,
    eigen_solver="arpack",
    is_to_dense: bool = False
) -> collection:
    """
    Spectral clustering
    :param data: Input data matrix;
    :param n_clusters: The dimension of the projection subspace.
    :param n_components: The dimension of the projection subspace.
    :param eigen_solver: Default use of Nyström approximation.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Tags after spectral clustering.
    """
    ul.log(__name__).info("Start spectral clustering")

    from sklearn.cluster import SpectralClustering

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    model = SpectralClustering(n_clusters=n_clusters, n_components=n_components, eigen_solver=eigen_solver)
    clusters_types = model.fit_predict(data_x)
    ul.log(__name__).info("End spectral clustering")
    return clusters_types


def tsne(data: matrix_data, n_components: int = 2, is_to_dense: bool = False) -> matrix_data:
    """
    T-SNE dimensionality reduction
    :param data: Data matrix that requires dimensionality reduction;
    :param n_components: Dimension of the embedded space.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Reduced dimensional data matrix
    """
    from sklearn.manifold import TSNE

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    _tsne_ = TSNE(n_components=n_components)
    data_tsne = _tsne_.fit_transform(data_x)
    return data_tsne


def umap(
    data: matrix_data,
    n_neighbors: float = 15,
    n_components: int = 2,
    min_dist: float = 0.15,
    is_to_dense: bool = False
) -> matrix_data:
    """
    UMAP dimensionality reduction
    :param data: Data matrix that requires dimensionality reduction;
    :param n_neighbors: float (optional, default 15)
        The size of local neighborhood (in terms of number of neighboring
        sample points) used for manifold approximation. Larger values
        result in more global views of the manifold, while smaller
        values result in more local data being preserved. In general
        values should be in the range 2 to 100;
    :param n_components: The dimension of the space to embed into. This defaults to 2 to
        provide easy visualization, but can reasonably be set to any
        integer value in the range 2 to 100.
    :param min_dist: The effective minimum distance between embedded points. Smaller values
        will result in a more clustered/clumped embedding where nearby points
        on the manifold are drawn closer together, while larger values will
        result on a more even dispersal of points. The value should be set
        relative to the ``spread`` value, which determines the scale at which
        embedded points will be spread out.
    :param is_to_dense: Whether to convert the data into a dense matrix.
    :return: Reduced dimensional data matrix
    """
    import umap as umap_

    data_x = to_dense(data, is_array=True) if is_to_dense else data

    embedding = umap_.UMAP(n_neighbors=n_neighbors, n_components=n_components, min_dist=min_dist).fit_transform(data_x)
    return embedding


def safe_kl_divergence(p: collection, q: collection, epsilon: float = 1e-10):
    """Safe KL divergence calculation to avoid division by zero"""

    # Ensure p and q are probability distributions
    p = to_dense(p, is_array=True).flatten()
    q = to_dense(q, is_array=True).flatten()

    # Smoothing: add small value to q to avoid zeros
    p = p + epsilon
    p = p / np.sum(p)

    q = q + epsilon
    q = q / np.sum(q)

    kl = np.sum(p * np.log(p / q))

    return kl


def kl_divergence(data1: matrix_data, data2: matrix_data) -> float:
    """
    Calculate KL divergence for two data
    :param data1: First data;
    :param data2: Second data.
    :return: KL divergence score
    """
    from scipy import stats

    data1 = to_dense(data1, is_array=True).flatten()
    data2 = to_dense(data2, is_array=True).flatten()

    entropy = stats.entropy(data1, data2)

    if np.isnan(entropy) or np.isinf(entropy):
        entropy = safe_kl_divergence(data1, data2)

    return entropy


def calinski_harabasz(data: matrix_data, labels: collection) -> float:
    """
    The Calinski-Harabasz index is also one of the indicators used to evaluate the quality of clustering models.
    It measures the compactness within the cluster and the separation between clusters in the clustering results. The
    larger the value, the better the clustering effect
    :param data: First data;
    :param labels: Predicted labels for each sample.
    :return:
    """
    from sklearn.metrics import calinski_harabasz_score
    return calinski_harabasz_score(to_dense(data, is_array=True), labels)


def silhouette(data: matrix_data, labels: collection) -> float:
    """
    silhouette
    :param data: An array of pairwise distances between samples, or a feature array;
    :param labels: Predicted labels for each sample.
    :return: index
    """
    from sklearn.metrics import silhouette_score
    return silhouette_score(to_dense(data, is_array=True), labels)


def davies_bouldin(data: matrix_data, labels: collection) -> float:
    """
    Davies-Bouldin index (DBI)
    :param data: A list of ``n_features``-dimensional data points. Each row corresponds to a single data point;
    :param labels: Predicted labels for each sample.
    :return: index
    """
    from sklearn.metrics import davies_bouldin_score
    return davies_bouldin_score(to_dense(data, is_array=True), labels)


def ari(labels_pred: collection, labels_true: collection) -> float:
    """
    ARI (-1, 1)
    :param labels_pred: Predictive labels for clustering;
    :param labels_true: Real labels for clustering.
    :return: index
    """
    from sklearn.metrics import adjusted_rand_score
    return adjusted_rand_score(labels_true, labels_pred)


def ami(labels_pred: collection, labels_true: collection) -> float:
    """
    AMI (0, 1)
    :param labels_pred: Predictive labels for clustering;
    :param labels_true: Real labels for clustering.
    :return: index
    """
    from sklearn.metrics import adjusted_mutual_info_score
    return adjusted_mutual_info_score(labels_true, labels_pred)


def binary_indicator(
    labels_true: collection,
    labels_pred: collection
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Accuracy, Recall, F1, FPR, TPR, AUROC, AUPRC
    :param labels_true: Real labels for clustering;
    :param labels_pred: Predictive labels for clustering.
    :return: Indicators
    """
    from sklearn.metrics import (
        accuracy_score,
        recall_score,
        f1_score,
        roc_curve,
        roc_auc_score,
        average_precision_score
    )

    acc_s = accuracy_score(labels_true, labels_pred)
    rec_s = recall_score(labels_true, labels_pred)
    f1_s = f1_score(labels_true, labels_pred)
    fpr, tpr, thresholds = roc_curve(labels_true, labels_pred)
    auroc_s = roc_auc_score(labels_true, labels_pred)
    auprc_s = average_precision_score(labels_true, labels_pred)
    return acc_s, rec_s, f1_s, fpr, tpr, auroc_s, auprc_s


def euclidean_distances(data1: matrix_data, data2: matrix_data = None, block_size: int = -1) -> matrix_data:
    """
    Calculate the Euclidean distance between two matrices
    :param data1: First data;
    :param data2: Second data (If the second data is empty, it will default to the first data.)
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed
    :return: Data of Euclidean distance.
    """
    ul.log(__name__).info("Start euclidean distances")

    if data2 is None:
        data2 = data1.copy()

    data1 = to_dense(data1)
    data2 = to_dense(data2)
    __data1_sum_sq__ = np.power(data1, 2).sum(axis=1)
    data1_sum_sq = __data1_sum_sq__.reshape((-1, 1))
    data2_sum_sq = __data1_sum_sq__ if data2 is None else np.power(data2, 2).sum(axis=1)
    del __data1_sum_sq__

    distances = data1_sum_sq + data2_sum_sq - 2 * to_dense(
        matrix_dot_block_storage(data1, data2.transpose(), block_size))
    del data1_sum_sq, data2_sum_sq

    distances[distances < 0] = 0.0
    distances = np.sqrt(distances)
    return distances


def _overlap_(regions_sort: DataFrame, variants: DataFrame) -> DataFrame:
    """
    Relate the peak region and variant site
    :param regions_sort: peaks information
    :param variants: variants information
    :return: The variant maps data in the peak region
    """

    columns = ['variant_id', 'index', 'chr', 'position', 'rsId', 'chr_a', 'start', 'end']

    if regions_sort.shape[0] == 0 or variants.shape[0] == 0:
        ul.log(__name__).warning("Data is empty.")
        return pd.DataFrame(columns=columns)

    variants_sort = variants.sort_values(["chr", "position"])[["variant_id", "chr", "position", "rsId"]]

    # Intersect and Sort
    chr_keys: list = list(set(regions_sort["chr"]).intersection(set(variants_sort["chr"])))
    chr_keys.sort()

    variants_chr_type: dict = {}
    variants_position_list: dict = {}

    # Cyclic region chromatin
    for chr_key in chr_keys:
        # variant chr information
        sort_chr_regions_chr = variants_sort[variants_sort["chr"] == chr_key]
        variants_chr_type.update({chr_key: sort_chr_regions_chr})
        variants_position_list.update({chr_key: list(sort_chr_regions_chr["position"])})

    variants_overlap_info_list: list = []

    for index, chr_a, start, end in zip(regions_sort["index"],
                                        regions_sort["chr"],
                                        regions_sort["start"],
                                        regions_sort["end"]):

        # judge chr
        if chr_a in chr_keys:
            # get chr variant
            variants_chr_type_position_list = variants_position_list[chr_a]
            # judge start and end position
            if start <= variants_chr_type_position_list[-1] and end >= variants_chr_type_position_list[0]:
                # get index
                start_index = get_index(start, variants_chr_type_position_list)
                end_index = get_index(end, variants_chr_type_position_list)

                # Determine whether it is equal, Equality means there is no overlap
                if start_index != end_index:
                    start_index = start_index if isinstance(start_index, number) else start_index[1]
                    end_index = end_index + 1 if isinstance(end_index, number) else end_index[1]

                    if start_index > end_index:
                        ul.log(__name__).error("The end index in the region is greater than the start index.")
                        raise IndexError("The end index in the region is greater than the start index.")

                    variants_chr_type_chr_a = variants_chr_type[chr_a]
                    # get data
                    variants_overlap_info: DataFrame = variants_chr_type_chr_a[start_index:end_index].copy()
                    variants_overlap_info["index"] = index
                    variants_overlap_info["chr_a"] = chr_a
                    variants_overlap_info["start"] = start
                    variants_overlap_info["end"] = end
                    variants_overlap_info.index = (
                        variants_overlap_info["variant_id"].astype(str) + "_"
                        + variants_overlap_info["index"].astype(str)
                    )
                    variants_overlap_info_list.append(variants_overlap_info)

    # merge result
    if len(variants_overlap_info_list) > 0:
        overlap_data: DataFrame = pd.concat(variants_overlap_info_list, axis=0)
    else:
        return pd.DataFrame(columns=columns)

    return overlap_data


def overlap(regions: DataFrame, variants: DataFrame) -> DataFrame:
    """
    Relate the peak region and variant site
    :param regions: peaks information
    :param variants: variants information
    :return: The variant maps data in the peak region
    """
    regions_columns: list = list(regions.columns)

    if "chr" not in regions_columns or "start" not in regions_columns or "end" not in regions_columns:
        ul.log(__name__).error(
            f"The peaks information {regions_columns} in data `adata` must include three columns: `chr`, `start` and "
            f"`end`. (It is recommended to use the `read_sc_atac` method.)"
        )
        raise ValueError(
            f"The peaks information {regions_columns} in data `adata` must include three columns: `chr`, `start` and "
            f"`end`. (It is recommended to use the `read_sc_atac` method.)"
        )

    columns = ['variant_id', 'index', 'chr', 'position', 'rsId', 'chr_a', 'start', 'end']

    if regions.shape[0] == 0 or variants.shape[0] == 0:
        ul.log(__name__).warning("Data is empty.")
        return pd.DataFrame(columns=columns)

    regions = regions.rename_axis("index")
    regions = regions.reset_index()
    # sort
    regions_sort = regions.sort_values(["chr", "start", "end"])[["index", "chr", "start", "end"]]

    return _overlap_(regions_sort, variants)


def overlap_sum(regions: AnnData, variants: dict, trait_info: DataFrame) -> AnnData:
    """
    Overlap regional data and mutation data and sum the PP values of all mutations in a region as the values for that
    region.
    :param regions: peaks data
    :param variants: variants data
    :param trait_info: traits information
    :return: overlap data
    """

    # Unique feature set
    label_all = regions.var.index.tolist()
    # Peak number
    label_all_size: int = len(label_all)

    # Pre-build a dict of peak indices for O(1) lookup
    label2idx = {lb: i for i, lb in enumerate(label_all)}

    trait_names = trait_info["id"].tolist()
    n_trait = len(trait_names)
    # Pre-allocate sparse matrix, fill column by column, then convert to csc and then csr for efficiency
    row_indices, col_indices, data_vals = [], [], []

    # Check column existence once
    required = {"chr", "start", "end"}

    if not required.issubset(regions.var.columns):
        ul.log(__name__).error(
            f"The peaks information {regions.var.columns} in data `adata` must include three columns: `chr`, `start` "
            f"and `end`. (It is recommended to use the `read_sc_atac` method.)"
        )
        raise ValueError(
            f"The peaks information {regions.var.columns} in data `adata` must include three columns: `chr`, `start` "
            f"and `end`. (It is recommended to use the `read_sc_atac` method.)"
        )

    regions_df = (
        regions.var
        .reset_index()
        .loc[:, ["index", "chr", "start", "end"]]
        .sort_values(["chr", "start", "end"])
    )

    ul.log(__name__).info("Obtain peak-trait/disease matrix. (overlap variant information)")

    # The outer loop can be further accelerated by parallelizing over traits; here we keep it single-threaded for now.
    for col_idx, trait_name in enumerate(tqdm(trait_names)):
        variant: AnnData = variants[trait_name]
        overlap_df: DataFrame = _overlap_(regions_df, variant.obs)

        if overlap_df.empty:
            continue

        # Sum at once: first group by label and collect variant_id into a list
        label_var_ids = (
            overlap_df
            .groupby("index")["variant_id"]
            .apply(list)
            .reset_index()
        )

        # Traverse each label, sum once for each variant_id list
        for _, row in label_var_ids.iterrows():
            label = row["index"]
            row_idx = label2idx[label]
            var_ids = row["variant_id"]
            # Sum once for all variant_ids in the list, avoiding row-by-row slicing
            matrix_sum = variant[var_ids, :].X.sum(axis=0)

            if np.isscalar(matrix_sum):
                matrix_sum = np.asarray(matrix_sum).reshape(1)

            # Collect non-zero values
            if matrix_sum.size == 1:
                val = float(matrix_sum)
                if val != 0:
                    row_indices.append(row_idx)
                    col_indices.append(col_idx)
                    data_vals.append(val)
            else:
                for t_idx, v in enumerate(matrix_sum):
                    if v != 0:
                        row_indices.append(row_idx)
                        col_indices.append(col_idx + t_idx)
                        data_vals.append(float(v))

    # Build sparse matrix, then convert to csr format
    overlap_sparse = sparse.csc_matrix(
        (data_vals, (row_indices, col_indices)),
        shape=(label_all_size, n_trait),
        dtype=np.float32
    ).tocsr()

    overlap_adata = AnnData(overlap_sparse, var=trait_info, obs=regions.var)
    overlap_adata.uns["is_overlap"] = True
    return overlap_adata


def calculate_fragment_weighted_accessibility(input_data: dict, block_size: int = -1) -> matrix_data:
    """
    Calculate the initial trait- or disease-related cell score
    :param input_data:
        1. data: Convert the `counts` matrix to the `fragments` matrix using the `scvi.data.reads_to_fragments`
        2. overlap_data: Peaks-traits/diseases data
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed
    :return: Initial TRS
    """

    if "data" not in input_data:
        ul.log(__name__).error("The `data` field needs to be included in parameter `input_data`.")
        raise ValueError("The `data` field needs to be included in parameter `input_data`.")

    if "overlap_data" not in input_data:
        ul.log(__name__).error("The `overlap_data` field needs to be included in parameter `input_data`.")
        raise ValueError("The `overlap_data` field needs to be included in parameter `input_data`.")

    # Processing data
    ul.log(__name__).info("Data pre conversion.")

    matrix = input_data.pop("data")
    overlap_matrix = input_data.pop("overlap_data")

    if sparse.issparse(matrix):
        matrix = matrix.tocsr(copy=False)
    else:
        matrix = to_sparse(matrix)

    if sparse.issparse(overlap_matrix):
        overlap_matrix = overlap_matrix.tocsr(copy=False)
    else:
        overlap_matrix = to_sparse(overlap_matrix)

    matrix.data = matrix.data.astype(np.float32)
    overlap_matrix.data = overlap_matrix.data.astype(np.float32)

    row_sum = np.asarray(matrix.sum(axis=1)).ravel()
    col_sum = np.asarray(matrix.sum(axis=0)).ravel()
    all_sum = row_sum.sum()

    ul.log(__name__).info("Calculate fragment weighted accessibility ===> (numerator)")
    init_score = matrix.dot(overlap_matrix)

    del matrix

    ul.log(__name__).info("Calculate expected counts matrix ===> (numerator)")
    global_scale_data = vector_multiply_block_storage(row_sum, col_sum, block_size=block_size)

    if block_size <= 0:
        global_scale_data = global_scale_data.astype(np.float32)

    del row_sum, col_sum

    global_scale_data /= all_sum * 1.0

    del all_sum

    ul.log(__name__).info("Calculate fragment weighted accessibility ===> (denominator)")
    overlap_matrix = to_dense(overlap_matrix)
    global_scale_data = global_scale_data.dot(overlap_matrix)

    global_scale_data[global_scale_data == 0] = global_scale_data[global_scale_data != 0].min() / 2

    ul.log(__name__).info("Calculate fragment weighted accessibility.")
    init_score = to_dense(init_score)
    init_score /= global_scale_data

    del global_scale_data

    return init_score


def calculate_init_score_weight(
    adata: AnnData,
    da_peaks_adata: AnnData,
    overlap_adata: AnnData,
    diff_peak_value: difference_peak_optional = 'emp_effect',
    is_simple: bool = True,
    block_size: int = -1
) -> AnnData:
    """
    Calculate the initial trait- or disease-related cell score with weight.
    :param adata: scATAC-seq data;
    :param da_peaks_adata: Differential peak data;
    :param overlap_adata: Peaks-traits/diseases data;
    :param diff_peak_value: Specify the correction value in peak correction of clustering type differences.
        {'emp_effect', 'bayes_factor', 'emp_prob1', 'all'}
    :param is_simple: True represents not adding unnecessary intermediate variables, only adding the final result. It
        is worth noting that when set to `True`, the `is_ablation` parameter will become invalid, and when set to
        `False`, `is_ablation` will only take effect;
    :param block_size: The size of the segmentation stored in block wise matrix multiplication.
        If the value is less than or equal to zero, no block operation will be performed
    :return: Initial TRS with weight.
    """
    if "is_overlap" not in overlap_adata.uns:
        ul.log(__name__).warning(
            "The `is_overlap` is not in `overlap_data.uns`. (Suggest using the 'tl.overlap_stum' function to obtain the result.)"
        )

    if "dp_delta" not in da_peaks_adata.uns:
        ul.log(__name__).warning(
            "The `dp_delta` is not in `da_peaks_adata.uns`. (Suggest using the 'pp.poisson_vi' function to obtain the result.)"
        )

    fragments = adata.layers["fragments"]
    cell_anno = adata.obs
    del adata

    fragments = to_sparse(fragments.astype(np.int32))
    overlap_matrix = to_dense(overlap_adata.X)
    trait_anno = overlap_adata.var
    del overlap_adata

    ul.log(__name__).info("Calculate cell type weight")

    def _get_cluster_weight_(da_matrix: matrix_data):
        _cluster_weight_data_: matrix_data = min_max_norm(da_matrix, axis=0).dot(overlap_matrix)
        return sigmoid(mean_symmetric_scale(_cluster_weight_data_, axis=0, is_verbose=False))

    if diff_peak_value == "emp_effect":
        _cluster_weight_ = _get_cluster_weight_(da_peaks_adata.X)
    elif diff_peak_value == "bayes_factor":
        _cluster_weight_ = _get_cluster_weight_(da_peaks_adata.layers["bayes_factor"])
    elif diff_peak_value == "emp_prob1":
        _cluster_weight_ = _get_cluster_weight_(da_peaks_adata.layers["emp_prob1"])
    elif diff_peak_value == "all":
        _cluster_weight1_ = _get_cluster_weight_(da_peaks_adata.X)
        _cluster_weight2_ = _get_cluster_weight_(da_peaks_adata.layers["bayes_factor"])
        _cluster_weight3_ = _get_cluster_weight_(da_peaks_adata.layers["emp_prob1"])
        _cluster_weight_ = (_cluster_weight1_ + _cluster_weight2_ + _cluster_weight3_) / 3
        del _cluster_weight1_, _cluster_weight2_, _cluster_weight3_
    else:
        ul.log(__name__).error(
            "The `diff_peak_value` parameter only supports one of the {'emp_effect', 'bayes_factor', 'emp_prob1', "
            "'all'} values."
        )
        raise ValueError(
            "The `diff_peak_value` parameter only supports one of the {'emp_effect', 'bayes_factor', 'emp_prob1', "
            "'all'} values."
        )

    overlap_matrix = to_sparse(overlap_matrix.astype(np.float32))

    row_sum = np.asarray(fragments.sum(axis=1)).ravel()
    col_sum = np.asarray(fragments.sum(axis=0)).ravel()
    all_sum = row_sum.sum()

    ul.log(__name__).info("Calculate fragment weighted accessibility ===> (numerator)")
    _init_trs_ncw_ = fragments.dot(overlap_matrix)

    del fragments

    ul.log(__name__).info("Calculate expected counts matrix ===> (numerator)")
    global_scale_data = vector_multiply_block_storage(row_sum, col_sum, block_size=block_size)

    if block_size <= 0:
        global_scale_data = global_scale_data.astype(np.float32)

    del row_sum, col_sum

    global_scale_data /= all_sum * 1.0

    del all_sum

    ul.log(__name__).info("Calculate fragment weighted accessibility ===> (denominator)")
    overlap_matrix = to_dense(overlap_matrix)
    global_scale_data = global_scale_data.dot(overlap_matrix)
    del overlap_matrix

    global_scale_data[global_scale_data == 0] = global_scale_data[global_scale_data != 0].min() / 2

    ul.log(__name__).info("Calculate fragment weighted accessibility.")
    _init_trs_ncw_ = to_dense(_init_trs_ncw_)
    _init_trs_ncw_ /= global_scale_data

    del global_scale_data

    da_peaks_adata.obsm["cluster_weight"] = to_dense(_cluster_weight_, is_array=True)
    del _cluster_weight_

    ul.log(__name__).info("Broadcasting the weight factor to the cellular level")
    _cell_type_weight_ = np.zeros((cell_anno.shape[0], da_peaks_adata.obsm["cluster_weight"].shape[1]), dtype=np.float32)

    cluster_series = cell_anno["clusters"]

    for cluster in da_peaks_adata.obs_names:
        mask = cluster_series == cluster
        _cell_type_weight_[mask, :] = da_peaks_adata[cluster, :].obsm["cluster_weight"].flatten().astype(np.float32)

    ul.log(__name__).info("Calculate initial trait relevance scores")
    _init_trs_weight_ = np.multiply(_init_trs_ncw_, _cell_type_weight_)
    init_trs_adata = AnnData(_init_trs_weight_, obs=cell_anno, var=trait_anno)
    del _init_trs_weight_

    if not is_simple:
        init_trs_adata.layers["init_trs_ncw"] = _init_trs_ncw_
        init_trs_adata.layers["cell_type_weight"] = to_sparse(_cell_type_weight_)
        init_trs_adata.uns["cluster_weight_factor"] = da_peaks_adata.obsm["cluster_weight"]

    del _init_trs_ncw_, _cell_type_weight_

    init_trs_adata.uns["is_sample"] = is_simple
    return init_trs_adata


def obtain_cell_cell_network(
    adata: AnnData,
    k: int = 30,
    or_k: int = 1,
    weight: float = 0.1,
    gamma: Optional[float] = None,
    is_simple: bool = True
) -> AnnData:
    """
    Calculate cell-cell correlation
    :param adata: scATAC-seq data;
    :param k: When building an M-KNN network, the number of nodes connected by each node (and);
    :param or_k: When building an M-KNN network, the number of nodes connected by each node (or);
    :param weight: The weight of interactions or operations;
    :param gamma: If None, defaults to 1.0 / n_features. Otherwise, it should be strictly positive;
    :param is_simple: True represents not adding unnecessary intermediate variables, only adding the final result.
        It is worth noting that when set to `True`, the `is_ablation` parameter will become invalid, and when set to
        `False`, `is_ablation` will only take effect;
    :return: Cell similarity data.
    """

    from sklearn.metrics.pairwise import laplacian_kernel

    # data
    if "poisson_vi" not in adata.uns.keys():
        ul.log(__name__).error(
            "`poisson_vi` is not in the `adata.uns` dictionary, and the scATAC-seq data needs to be processed through "
            "the `poisson_vi` function."
        )
        raise ValueError(
            "`poisson_vi` is not in the `adata.uns` dictionary, and the scATAC-seq data needs to be processed through "
            "the `poisson_vi` function."
        )

    _latent_name_ = "latent" if adata.uns["poisson_vi"]["latent_name"] is None \
        else adata.uns["poisson_vi"]["latent_name"]

    latent = adata.obsm[_latent_name_].astype(np.float32)
    del _latent_name_
    cell_anno = adata.obs
    del adata

    ul.log(__name__).info("Laplacian kernel")
    # Laplacian kernel
    cell_affinity = laplacian_kernel(latent, gamma=gamma).astype(np.float32)

    # Define KNN network
    cell_mutual_knn_weight, cell_mutual_knn = semi_mutual_knn_weight(
        cell_affinity,
        neighbors=k,
        or_neighbors=or_k,
        weight=weight
    )

    if is_simple:
        del cell_mutual_knn

    # cell-cell graph
    cc_data: AnnData = AnnData(cell_mutual_knn_weight, var=cell_anno, obs=cell_anno)
    cc_data.layers["cell_affinity"] = cell_affinity

    if not is_simple:
        cc_data.layers["cell_mutual_knn"] = to_sparse(cell_mutual_knn)

    return cc_data


def perturb_data(data: collection, percentage: float) -> collection:
    """
    Randomly perturbs the positions of a percentage of data.
    :param data: List of data elements to be perturbed.
    :param percentage: Percentage of data to be perturbed.
    :return: Perturbed data list.
    """

    if percentage <= 0 or percentage > 1:
        raise ValueError("The value of the `percentage` parameter must be greater than 0 and less than or equal to 1.")

    new_data = data.copy()
    num_elements = len(new_data)
    num_to_perturb = int(num_elements * percentage)

    # Select random indices to perturb
    indices_to_perturb = random.sample(range(num_elements), num_to_perturb)

    # Swap elements at selected indices with other random elements
    for index in indices_to_perturb:
        swap_index = random.choice([i for i in range(num_elements) if i != index])
        new_data[index], new_data[swap_index] = new_data[swap_index], new_data[index]

    return new_data


def add_noise(data: matrix_data, rate: float) -> matrix_data:
    """
    Add peak percentage noise to each cell
    """

    if rate <= 0 or rate >= 1:
        raise ValueError("The value of the `rate` parameter must be greater than 0 and less than 1.")

    shape = data.shape
    noise = to_dense(data.copy())

    for i in tqdm(range(shape[0])):
        count_i = np.array(noise[i, :]).flatten()
        # Add noise to the accessibility of unopened chromatin
        count0_i = count_i[count_i == 0]
        max_i = np.max(count_i)
        count0 = int(count0_i.size * rate)
        noise0_i = np.random.randint(low=1, high=2 if max_i < 2 else max_i, size=count0)
        random_index0 = np.random.choice(np.arange(0, count0_i.size), size=count0, replace=False)
        count0_i[random_index0] = noise0_i
        count_i_value = count_i.copy()
        count_i_value[count_i_value == 0] = count0_i
        noise[i, :] = count_i_value

        # Close open chromatin accessibility
        count1_i = count_i[count_i == 1]
        count1 = int(count1_i.size * rate)
        random_index1 = np.random.choice(np.arange(0, count1_i.size), size=count1, replace=False)
        count1_i[random_index1] = 0
        count_i[count_i == 1] = count1_i
        noise[i, :] = count_i

        # disturbance
        noise[i, :] = perturb_data(noise[i, :], rate)

    return noise
