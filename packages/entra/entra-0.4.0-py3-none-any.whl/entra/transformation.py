"""
Divergence-Free Transformation Module

Applies a divergence-free transformation to points using tensor basis functions:

    y'_k = y_k + Σ_l Σ_d c_{l,d} * Φ[:, l, :, d]_k

where:
- y_k is the original point (D,)
- y'_k is the transformed point (D,)
- c_{l,d} are coefficients for center l, column d
- Φ[:, l, :, d] is the d-th column of tensor basis for center l (a divergence-free vector field)

Since each column of Φ is divergence-free, and linear combinations of divergence-free
fields are divergence-free, the transformation preserves incompressibility.
"""

from typing import Optional

import numpy as np

from .tensor_basis import TensorBasis


class Transformation:
    """
    Divergence-free transformation using tensor basis functions.

    The transformation is:
        y' = y + Σ_l Φ_l(y) @ c_l

    where Φ_l(y) is the DxD tensor basis matrix for center l, and c_l is a
    D-dimensional coefficient vector. This is equivalent to:
        y' = y + Σ_l Σ_d c_{l,d} * V^l_d(y)

    where V^l_d is the d-th column (divergence-free vector field) of Φ_l.

    Parameters
    ----------
    tensor_basis : TensorBasis
        The tensor basis providing divergence-free vector fields.
    coefficients : np.ndarray, optional
        Initial coefficients of shape (L, D). If None, initialized to zeros.

    Attributes
    ----------
    tensor_basis : TensorBasis
        The underlying tensor basis.
    coefficients : np.ndarray
        Coefficients of shape (L, D) where L is number of centers, D is dimension.
    L : int
        Number of basis function centers.
    D : int
        Dimension of space.
    """

    def __init__(
        self,
        tensor_basis: TensorBasis,
        coefficients: Optional[np.ndarray] = None,
    ):
        self.tensor_basis = tensor_basis
        self.L = tensor_basis.L
        self.D = tensor_basis.D

        if coefficients is None:
            self.coefficients = np.zeros((self.L, self.D), dtype=np.float64)
        else:
            coefficients = np.asarray(coefficients, dtype=np.float64)
            if coefficients.shape != (self.L, self.D):
                raise ValueError(
                    f"coefficients must have shape ({self.L}, {self.D}), "
                    f"got {coefficients.shape}"
                )
            self.coefficients = coefficients

    def transform(self, y: np.ndarray) -> np.ndarray:
        """
        Apply the divergence-free transformation to points.

        y' = y + Σ_l Φ_l(y) @ c_l

        Parameters
        ----------
        y : np.ndarray
            Points to transform. Shape (D,) for single point or (J, D) for J points.

        Returns
        -------
        np.ndarray
            Transformed points with same shape as input.
        """
        y = np.asarray(y, dtype=np.float64)
        single_point = y.ndim == 1

        if single_point:
            y = y.reshape(1, -1)

        J = y.shape[0]

        # Evaluate tensor basis: (J, L, D, D)
        Phi = self.tensor_basis.evaluate(y)

        # Compute displacement: Σ_l Φ[j, l, :, :] @ c_l
        # Phi: (J, L, D, D), coefficients: (L, D)
        # For each point j: displacement[j] = Σ_l Phi[j, l, :, :] @ coefficients[l, :]
        displacement = np.zeros((J, self.D), dtype=np.float64)

        for center_idx in range(self.L):
            # (J, D, D) @ (D,) -> (J, D)
            displacement += (
                Phi[:, center_idx, :, :] @ self.coefficients[center_idx, :]
            )

        y_transformed = y + displacement

        if single_point:
            return y_transformed[0]
        return y_transformed

    def get_displacement(self, y: np.ndarray) -> np.ndarray:
        """
        Get only the displacement (without adding to original points).

        displacement = Σ_l Φ_l(y) @ c_l

        Parameters
        ----------
        y : np.ndarray
            Points at which to compute displacement.
            Shape (D,) for single point or (J, D) for J points.

        Returns
        -------
        np.ndarray
            Displacement vectors with same shape as input.
        """
        y = np.asarray(y, dtype=np.float64)
        single_point = y.ndim == 1

        if single_point:
            y = y.reshape(1, -1)

        J = y.shape[0]
        Phi = self.tensor_basis.evaluate(y)

        displacement = np.zeros((J, self.D), dtype=np.float64)
        for center_idx in range(self.L):
            # (J, D, D) @ (D,) -> (J, D)
            displacement += (
                Phi[:, center_idx, :, :] @ self.coefficients[center_idx, :]
            )

        if single_point:
            return displacement[0]
        return displacement

    def set_coefficients(self, coefficients: np.ndarray) -> None:
        """
        Set the transformation coefficients.

        Parameters
        ----------
        coefficients : np.ndarray
            New coefficients of shape (L, D).
        """
        coefficients = np.asarray(coefficients, dtype=np.float64)
        if coefficients.shape != (self.L, self.D):
            raise ValueError(
                f"coefficients must have shape ({self.L}, {self.D}), "
                f"got {coefficients.shape}"
            )
        self.coefficients = coefficients

    def set_coefficients_flat(self, coefficients_flat: np.ndarray) -> None:
        """
        Set coefficients from a flattened array.

        Parameters
        ----------
        coefficients_flat : np.ndarray
            Flattened coefficients of shape (L * D,).
        """
        coefficients_flat = np.asarray(coefficients_flat, dtype=np.float64)
        expected_size = self.L * self.D
        if coefficients_flat.size != expected_size:
            raise ValueError(
                f"coefficients_flat must have size {expected_size}, "
                f"got {coefficients_flat.size}"
            )
        self.coefficients = coefficients_flat.reshape(self.L, self.D)

    def get_coefficients_flat(self) -> np.ndarray:
        """
        Get coefficients as a flattened array.

        Returns
        -------
        np.ndarray
            Flattened coefficients of shape (L * D,).
        """
        return self.coefficients.ravel()

    @property
    def num_parameters(self) -> int:
        """Total number of parameters (L * D)."""
        return self.L * self.D

    def get_updated_basis(self, y: np.ndarray) -> np.ndarray:
        """
        Get the updated basis by multiplying coefficients with tensor basis rows.

        new_basis[:, l, :] = Φ[:, l, :, :] @ coefficients[l, :]

        Parameters
        ----------
        y : np.ndarray
            Points at which to evaluate. Shape (J, D).

        Returns
        -------
        np.ndarray
            Updated basis of shape (J, L, D).
        """
        y = np.asarray(y, dtype=np.float64)
        if y.ndim == 1:
            y = y.reshape(1, -1)

        J = y.shape[0]
        Phi = self.tensor_basis.evaluate(y)  # (J, L, D, D)

        updated_basis = np.zeros((J, self.L, self.D), dtype=np.float64)
        for li in range(self.L):
            # (J, D, D) @ (D,) -> (J, D)
            updated_basis[:, li, :] = (
                Phi[:, li, :, :] @ self.coefficients[li, :]
            )

        return updated_basis

    def __repr__(self) -> str:
        return (
            f"Transformation(L={self.L}, D={self.D}, "
            f"num_parameters={self.num_parameters})"
        )
