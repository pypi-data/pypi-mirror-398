"""
Tensor Basis Function Module

Applies the operator Ô = -I∇² + ∇∇ᵀ to Gaussian RBF basis functions,
producing DxD matrix-valued basis functions.

L centers, N evaluation points, D dimensions → output (N, L, D, D)
"""

import numpy as np


class TensorBasis:
    """
    Applies operator Ô = -I∇² + ∇∇ᵀ to Gaussian RBFs.

    For each basis function φ_l(x) = exp(-||x - x_l||²/(2s²)), produces:

    Φ_l(x) = {(D-1)/s² - ||x-x_l||²/s⁴} I_D exp(-||x-x_l||²/(2s²))
           + {(x-x_l)(x-x_l)ᵀ / s⁴} exp(-||x-x_l||²/(2s²))

    where D is the dimension and I_D is the DxD identity matrix.

    Parameters
    ----------
    centers : np.ndarray
        Array of shape (L, D) containing L center vectors of dimension D.
    sigma : float
        Isotropic width parameter s for the Gaussian RBFs.

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
    sigma : float
        Width parameter.
    """

    def __init__(self, centers: np.ndarray, sigma: float):
        self.centers = np.array(centers, dtype=np.float64)
        self.L, self.D = self.centers.shape
        self.center_vector = np.mean(self.centers, axis=0)
        self.sigma = float(sigma)
        self.sigma_sq = self.sigma**2
        self.sigma_4 = self.sigma**4

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        """
        Evaluate operator on all L basis functions at N point(s) x.

        Parameters
        ----------
        x : np.ndarray
            Shape (D,) for single point or (N, D) for N points.

        Returns
        -------
        np.ndarray
            Shape (L, D, D) for single point or (N, L, D, D) for N points.
        """
        x = np.array(x, dtype=np.float64)
        single_point = x.ndim == 1

        if single_point:
            x = x.reshape(1, -1)

        D = self.D

        # diff[n, l, d] = x[n, d] - centers[l, d]
        diff = (
            x[:, np.newaxis, :] - self.centers[np.newaxis, :, :]
        )  # (N, L, D)

        # Squared distances: ||x - x_l||²
        sq_dist = np.sum(diff**2, axis=2)  # (N, L)

        # Gaussian values: exp(-||x - x_l||²/(2s²))
        phi = np.exp(-sq_dist / (2 * self.sigma_sq))  # (N, L)

        # Coefficient for identity term: (D-1)/s² - ||x-x_l||²/s⁴
        coeff = (D - 1) / self.sigma_sq - sq_dist / self.sigma_4  # (N, L)

        # Identity term: coeff * I * phi
        # Shape: (N, L, D, D)
        identity = np.eye(D)
        term1 = (
            coeff[:, :, np.newaxis, np.newaxis]
            * identity
            * phi[:, :, np.newaxis, np.newaxis]
        )

        # Outer product term: (x-x_l)(x-x_l)ᵀ / s⁴ * phi
        # diff: (N, L, D) -> outer product for each (n, l): (N, L, D, D)
        outer = (
            diff[:, :, :, np.newaxis] * diff[:, :, np.newaxis, :]
        )  # (N, L, D, D)
        term2 = (outer / self.sigma_4) * phi[:, :, np.newaxis, np.newaxis]

        result = term1 + term2  # (N, L, D, D)

        if single_point:
            return result[0]  # (L, D, D)
        return result  # (N, L, D, D)

    def evaluate_scalar(self, x: np.ndarray) -> np.ndarray:
        """
        Evaluate the underlying scalar Gaussian RBF (without operator).

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

        diff = x[:, np.newaxis, :] - self.centers[np.newaxis, :, :]
        sq_dist = np.sum(diff**2, axis=2)
        phi = np.exp(-sq_dist / (2 * self.sigma_sq))

        if single_point:
            return phi[0]
        return phi

    def __repr__(self) -> str:
        return f"TensorBasis(L={self.L}, D={self.D}, " f"sigma={self.sigma})"

    def __len__(self) -> int:
        return self.L
