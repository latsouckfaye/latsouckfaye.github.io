"""Sampling helpers for the strategic-sampling tutorial.

`kmeans_medoids` is the Python counterpart of the R `scsCLARA`/`cdCLARA`
functions: cluster on a feature space with k-means, then within each
cluster keep the real observation closest to the centroid as the sampled
location (a medoid), instead of the centroid itself. `scikit-learn-extra`
(which ships an actual CLARA/KMedoids) isn't available here, so this is a
small, honest stand-in built directly on `scikit-learn`'s k-means.
"""
import numpy as np
from sklearn.cluster import KMeans


def kmeans_medoids(X, coords, k, seed=0, n_init=10):
    km = KMeans(n_clusters=k, random_state=seed, n_init=n_init).fit(X)
    labels, centers = km.labels_, km.cluster_centers_
    medoid_idx = []
    for c in range(k):
        idx = np.where(labels == c)[0]
        if len(idx) == 0:
            continue
        d = np.linalg.norm(X[idx] - centers[c], axis=1)
        medoid_idx.append(idx[np.argmin(d)])
    medoid_idx = np.array(medoid_idx)
    return coords[medoid_idx], medoid_idx
