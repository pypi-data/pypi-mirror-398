"""
Scalar Basis Function Module

Provides Gaussian RBF scalar basis functions centered at L center vectors,
evaluated at N points in D-dimensional space.
"""

from typing import Union

import numpy as np


class ScalarBasis:
    """
    Creates L smooth scalar basis functions (Gaussian RBFs) from L center vectors.

    Each basis function is defined as:
        φ_l(x) = exp(-Σ_d (x_d - c_l,d)² / (2s_d²))

    where c_l is the l-th center vector and s_d = sigma_factor * Δx_d.

    Parameters
    ----------
    centers : np.ndarray
        Array of shape (L, D) containing L center vectors of dimension D.
    delta_x : float, list, or np.ndarray
        Grid spacing per dimension. Scalar applies to all dimensions.
    sigma_factor : float, optional
        Multiplier for delta_x to compute s. Default is 0.7.

    Attributes
    ----------
    centers : np.ndarray
        The (L, D) array of center vectors.
    L : int
        Number of basis functions (centers).
    D : int
        Dimension of the space.
    center_vector : np.ndarray
        Mean of the center vectors.
    delta_x : np.ndarray
        Spacing per dimension.
    sigma : np.ndarray
        s values per dimension.
    sigma_sq : np.ndarray
        s² values per dimension.
    """

    def __init__(
        self,
        centers: np.ndarray,
        delta_x: Union[float, list, np.ndarray],
        sigma_factor: float = 0.7,
    ):
        self.centers = np.array(centers, dtype=np.float64)
        self.L, self.D = self.centers.shape
        self.center_vector = np.mean(self.centers, axis=0)

        if np.isscalar(delta_x):
            self.delta_x = np.full(self.D, delta_x, dtype=np.float64)
        else:
            self.delta_x = np.array(delta_x, dtype=np.float64)

        self.sigma_factor = sigma_factor
        self.sigma = self.sigma_factor * self.delta_x
        self.sigma_sq = self.sigma**2

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        """
        Evaluate all L basis functions at N point(s) x.

        Parameters
        ----------
        x : np.ndarray
            Shape (D,) for single point or (N, D) for N points.

        Returns
        -------
        np.ndarray
            Shape (L,) for single point or (N, L) for N points.
        """
        x = np.array(x, dtype=np.float64)
        single_point = x.ndim == 1

        if single_point:
            x = x.reshape(1, -1)

        # diff: (N, L, D)
        diff = x[:, np.newaxis, :] - self.centers[np.newaxis, :, :]
        weighted_sq_dist = np.sum(diff**2 / self.sigma_sq, axis=2)
        values = np.exp(-weighted_sq_dist / 2.0)

        if single_point:
            return values[0]
        return values

    def evaluate_gradient(self, x: np.ndarray) -> np.ndarray:
        """
        Compute gradients of all L basis functions at N point(s) x.

        Parameters
        ----------
        x : np.ndarray
            Shape (D,) or (N, D).

        Returns
        -------
        np.ndarray
            Shape (L, D) for single point or (N, L, D) for N points.
        """
        x = np.array(x, dtype=np.float64)
        single_point = x.ndim == 1

        if single_point:
            x = x.reshape(1, -1)

        diff = x[:, np.newaxis, :] - self.centers[np.newaxis, :, :]
        phi_values = self.evaluate(x)
        gradients = -phi_values[:, :, np.newaxis] * diff / self.sigma_sq

        if single_point:
            return gradients[0]
        return gradients

    def __repr__(self) -> str:
        return (
            f"ScalarBasis(L={self.L}, D={self.D}, "
            f"sigma={self.sigma.tolist()})"
        )

    def __len__(self) -> int:
        return self.L
