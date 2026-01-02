"""
Effective Basis Module

After the first iteration, the tensor basis (J, L, D, D) with coefficients (L, D)
collapses to an effective basis (J, L, D) - L vector fields.

Subsequent iterations use this effective basis with L scalar coefficients.
"""

from typing import Any, Dict, Optional

import numpy as np


class EffectiveTransformation:
    """
    Transformation using effective basis with scalar coefficients.

    y' = y + Σ_l c_l * V_l

    where V_l is the l-th vector field and c_l is a scalar coefficient.

    Parameters
    ----------
    basis : np.ndarray
        Effective basis of shape (J, L, D).
    points : np.ndarray
        Original points of shape (J, D).
    coefficients : np.ndarray, optional
        Initial coefficients of shape (L,). If None, initialized to zeros.
    """

    def __init__(
        self,
        basis: np.ndarray,
        points: np.ndarray,
        coefficients: Optional[np.ndarray] = None,
    ):
        self.basis = np.asarray(basis, dtype=np.float64)
        self.points = np.asarray(points, dtype=np.float64)

        self.J, self.L, self.D = self.basis.shape

        if coefficients is None:
            self.coefficients = np.zeros(self.L, dtype=np.float64)
        else:
            coefficients = np.asarray(coefficients, dtype=np.float64)
            if coefficients.shape != (self.L,):
                raise ValueError(
                    f"coefficients must have shape ({self.L},), got {coefficients.shape}"
                )
            self.coefficients = coefficients

    def transform(self) -> np.ndarray:
        """
        Apply transformation: y' = y + Σ_l c_l * V_l

        Returns
        -------
        np.ndarray
            Transformed points of shape (J, D).
        """
        displacement = self.get_displacement()
        return self.points + displacement

    def get_displacement(self) -> np.ndarray:
        """
        Get displacement: Σ_l c_l * V_l

        Returns
        -------
        np.ndarray
            Displacement of shape (J, D).
        """
        # basis: (J, L, D), coefficients: (L,)
        # result: (J, D)
        return (self.basis * self.coefficients[np.newaxis, :, np.newaxis]).sum(
            axis=1
        )

    def set_coefficients(self, coefficients: np.ndarray) -> None:
        """Set coefficients."""
        coefficients = np.asarray(coefficients, dtype=np.float64)
        if coefficients.shape != (self.L,):
            raise ValueError(
                f"coefficients must have shape ({self.L},), got {coefficients.shape}"
            )
        self.coefficients = coefficients

    def get_coefficients(self) -> np.ndarray:
        """Get coefficients."""
        return self.coefficients.copy()

    def get_updated_basis(self) -> np.ndarray:
        """
        Get updated basis by multiplying current basis with coefficients.

        new_basis[:, l, :] = c_l * basis[:, l, :]

        Returns
        -------
        np.ndarray
            Updated basis of shape (J, L, D).
        """
        return self.basis * self.coefficients[np.newaxis, :, np.newaxis]

    @property
    def num_parameters(self) -> int:
        """Number of parameters (L)."""
        return self.L

    def __repr__(self) -> str:
        return f"EffectiveTransformation(J={self.J}, L={self.L}, D={self.D})"


class EffectiveCovarianceMinimizer:
    """
    Minimizes covariance determinant using effective basis.

    Parameters
    ----------
    transformation : EffectiveTransformation
        The transformation to optimize.
    """

    def __init__(self, transformation: EffectiveTransformation):
        self.transformation = transformation
        self.J = transformation.J
        self.D = transformation.D
        self.L = transformation.L

    def compute_transformed_points(
        self, coefficients: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Compute transformed points."""
        if coefficients is not None:
            self.transformation.set_coefficients(coefficients)
        return self.transformation.transform()

    def compute_covariance(
        self, coefficients: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Compute covariance matrix of transformed points."""
        y_prime = self.compute_transformed_points(coefficients)
        return np.cov(y_prime, rowvar=False)

    def objective_logdet(self, coefficients: np.ndarray) -> float:
        """Compute log-determinant of covariance."""
        cov = self.compute_covariance(coefficients)
        sign, logdet = np.linalg.slogdet(cov)
        if sign <= 0:
            return 1e10
        return logdet

    def residuals_for_lm(self, coefficients: np.ndarray) -> np.ndarray:
        """Compute residuals for Levenberg-Marquardt."""
        cov = self.compute_covariance(coefficients)
        try:
            L_chol = np.linalg.cholesky(cov)
            return np.log(np.diag(L_chol))
        except np.linalg.LinAlgError:
            eigvals = np.linalg.eigvalsh(cov)
            eigvals = np.maximum(eigvals, 1e-10)
            return np.log(np.sqrt(eigvals))

    def optimize(
        self,
        max_iterations: int = 500,
        tolerance: float = 1e-10,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Optimize coefficients using Levenberg-Marquardt.

        Parameters
        ----------
        max_iterations : int
            Maximum iterations.
        tolerance : float
            Convergence tolerance.
        verbose : bool
            Print progress.

        Returns
        -------
        dict
            Optimization result.
        """
        x = self.transformation.get_coefficients()
        n_params = len(x)

        initial_cov = self.compute_covariance(x)
        initial_det = np.linalg.det(initial_cov)

        lam = 1.0
        eps = 1e-7

        for iteration in range(1, max_iterations + 1):
            r = self.residuals_for_lm(x)

            # Jacobian
            J_mat = np.zeros((len(r), n_params))
            for i in range(n_params):
                x_plus = x.copy()
                x_plus[i] += eps
                J_mat[:, i] = (self.residuals_for_lm(x_plus) - r) / eps

            JTJ = J_mat.T @ J_mat
            JTr = J_mat.T @ r

            try:
                delta = np.linalg.solve(JTJ + lam * np.eye(n_params), -JTr)
            except np.linalg.LinAlgError:
                delta = -JTr / (np.diag(JTJ) + lam + 1e-10)

            x_new = x + delta
            obj_new = self.objective_logdet(x_new)
            obj_old = self.objective_logdet(x)

            if obj_new < obj_old:
                x = x_new
                lam *= 0.1
                improvement = abs(obj_old - obj_new)

                if improvement < tolerance:
                    if verbose:
                        print(f"Converged at iteration {iteration}")
                    break
            else:
                lam *= 10.0

        self.transformation.set_coefficients(x)
        final_cov = self.compute_covariance()
        final_det = np.linalg.det(final_cov)

        return {
            "success": True,
            "coefficients": self.transformation.get_coefficients(),
            "final_covariance": final_cov,
            "final_determinant": final_det,
            "initial_determinant": initial_det,
            "iterations": iteration,
        }

    def __repr__(self) -> str:
        return (
            f"EffectiveCovarianceMinimizer(J={self.J}, L={self.L}, D={self.D})"
        )
