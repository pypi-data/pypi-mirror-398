"""
Covariance Minimizer Module

Optimizes transformation coefficients to minimize the determinant of the
covariance matrix of transformed points using Levenberg-Marquardt or other
optimization methods.

The objective is to find coefficients c_{l,d} such that:
    min det(Cov(Y'))

where Y' = {y'_1, ..., y'_J} are the transformed points and Cov is the D×D
covariance matrix.
"""

from typing import Any, Dict, Optional

import numpy as np

from .transformation import Transformation


class CovarianceMinimizer:
    """
    Minimizes the determinant of the covariance matrix of transformed points.

    Given a Transformation and a set of original points, finds the optimal
    coefficients that minimize det(Cov(Y')) where Y' are the transformed points.

    Parameters
    ----------
    transformation : Transformation
        The transformation whose coefficients will be optimized.
    points : np.ndarray
        Original points of shape (J, D).

    Attributes
    ----------
    transformation : Transformation
        The transformation being optimized.
    points : np.ndarray
        Original points (J, D).
    J : int
        Number of points.
    D : int
        Dimension of space.
    """

    def __init__(self, transformation: Transformation, points: np.ndarray):
        self.transformation = transformation
        self.points = np.asarray(points, dtype=np.float64)

        if self.points.ndim != 2:
            raise ValueError(
                f"points must be 2D array, got {self.points.ndim}D"
            )

        self.J, self.D = self.points.shape

        if self.D != transformation.D:
            raise ValueError(
                f"points dimension {self.D} doesn't match "
                f"transformation dimension {transformation.D}"
            )

    def compute_transformed_points(
        self, coefficients_flat: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute transformed points for given coefficients.

        Parameters
        ----------
        coefficients_flat : np.ndarray, optional
            Flattened coefficients. If None, uses current transformation coefficients.

        Returns
        -------
        np.ndarray
            Transformed points of shape (J, D).
        """
        if coefficients_flat is not None:
            self.transformation.set_coefficients_flat(coefficients_flat)

        return self.transformation.transform(self.points)

    def compute_covariance(
        self, coefficients_flat: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute covariance matrix of transformed points.

        Parameters
        ----------
        coefficients_flat : np.ndarray, optional
            Flattened coefficients. If None, uses current transformation coefficients.

        Returns
        -------
        np.ndarray
            Covariance matrix of shape (D, D).
        """
        y_prime = self.compute_transformed_points(coefficients_flat)
        # rowvar=False means each column is a variable, each row is an observation
        return np.cov(y_prime, rowvar=False)

    def objective_logdet(self, coefficients_flat: np.ndarray) -> float:
        """
        Compute log-determinant of covariance (objective to minimize).

        Using log-determinant for numerical stability.

        Parameters
        ----------
        coefficients_flat : np.ndarray
            Flattened coefficients of shape (L * D,).

        Returns
        -------
        float
            log(det(Cov)) value.
        """
        cov = self.compute_covariance(coefficients_flat)
        sign, logdet = np.linalg.slogdet(cov)

        if sign <= 0:
            # Covariance should be positive semi-definite
            # Return large penalty if something goes wrong
            return 1e10

        return logdet

    def residuals_for_lm(self, coefficients_flat: np.ndarray) -> np.ndarray:
        """
        Compute residuals for Levenberg-Marquardt optimization.

        For LM, we need a residual vector r such that we minimize ||r||^2.
        We use the Cholesky factor diagonal, since det(Cov) = prod(L_ii)^2.
        Minimizing sum(log(L_ii)^2) is a proxy for minimizing log(det).

        Parameters
        ----------
        coefficients_flat : np.ndarray
            Flattened coefficients.

        Returns
        -------
        np.ndarray
            Residual vector for least-squares.
        """
        cov = self.compute_covariance(coefficients_flat)

        try:
            # Cholesky decomposition: Cov = L @ L.T
            L = np.linalg.cholesky(cov)
            # det(Cov) = prod(diag(L))^2
            # To minimize det, minimize prod(diag(L))
            # Use log for stability: minimize sum(log(diag(L)))
            # For LM, residuals = log(diag(L))
            residuals = np.log(np.diag(L))
        except np.linalg.LinAlgError:
            # Fallback if not positive definite
            eigvals = np.linalg.eigvalsh(cov)
            eigvals = np.maximum(eigvals, 1e-10)
            residuals = np.log(np.sqrt(eigvals))

        return residuals

    def optimize(
        self,
        method: str = "lm",
        max_iterations: int = 1000,
        tolerance: float = 1e-8,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Optimize coefficients to minimize determinant of covariance.

        Parameters
        ----------
        method : str
            Optimization method:
            - 'lm': Levenberg-Marquardt (scipy.optimize.least_squares)
            - 'trf': Trust Region Reflective (scipy.optimize.least_squares)
            - 'L-BFGS-B': L-BFGS-B (scipy.optimize.minimize)
            - 'BFGS': BFGS (scipy.optimize.minimize)
            - 'Nelder-Mead': Nelder-Mead simplex (scipy.optimize.minimize)
        max_iterations : int
            Maximum number of iterations.
        tolerance : float
            Convergence tolerance.
        verbose : bool
            If True, print progress.

        Returns
        -------
        dict
            Optimization result containing:
            - 'success': bool, whether optimization succeeded
            - 'coefficients': optimized coefficients (L, D)
            - 'final_covariance': final covariance matrix (D, D)
            - 'final_determinant': det(Cov) after optimization
            - 'initial_determinant': det(Cov) before optimization
            - 'iterations': number of iterations
            - 'message': status message
        """
        from scipy.optimize import least_squares, minimize

        x0 = self.transformation.get_coefficients_flat()

        # Compute initial determinant
        initial_cov = self.compute_covariance(x0)
        initial_det = np.linalg.det(initial_cov)

        if verbose:
            print(f"Initial log(det(Cov)) = {np.log(initial_det):.6f}")
            print(f"Initial det(Cov) = {initial_det:.6e}")
            print(f"Optimizing {len(x0)} parameters...")

        if method in ["lm", "trf", "dogbox"]:
            # Use least_squares with residuals
            result = least_squares(
                self.residuals_for_lm,
                x0,
                method=method,
                max_nfev=max_iterations,
                ftol=tolerance,
                xtol=tolerance,
                gtol=tolerance,
                verbose=2 if verbose else 0,
            )
            success = result.success
            x_opt = result.x
            n_iter = result.nfev
            message = result.message

        else:
            # Use minimize with log-determinant objective
            iter_count = [0]

            def callback(xk):
                iter_count[0] += 1
                if verbose and iter_count[0] % 10 == 0:
                    obj = self.objective_logdet(xk)
                    print(f"  Iter {iter_count[0]}: log(det) = {obj:.6f}")

            result = minimize(
                self.objective_logdet,
                x0,
                method=method,
                options={"maxiter": max_iterations, "disp": verbose},
                tol=tolerance,
                callback=callback if verbose else None,
            )
            success = result.success
            x_opt = result.x
            n_iter = result.nit if hasattr(result, "nit") else iter_count[0]
            message = result.message if hasattr(result, "message") else ""

        # Set optimized coefficients
        self.transformation.set_coefficients_flat(x_opt)

        # Compute final covariance and determinant
        final_cov = self.compute_covariance()
        final_det = np.linalg.det(final_cov)

        if verbose:
            print(f"\nOptimization {'succeeded' if success else 'failed'}")
            print(f"Final log(det(Cov)) = {np.log(final_det):.6f}")
            print(f"Final det(Cov) = {final_det:.6e}")
            print(f"Reduction: {initial_det / final_det:.2f}x")

        return {
            "success": success,
            "coefficients": self.transformation.coefficients.copy(),
            "final_covariance": final_cov,
            "final_determinant": final_det,
            "initial_determinant": initial_det,
            "iterations": n_iter,
            "message": message,
        }

    def optimize_iterative(
        self,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        damping: float = 1.0,
        damping_increase: float = 10.0,
        damping_decrease: float = 0.1,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Custom Levenberg-Marquardt implementation for minimizing det(Cov).

        This implements the LM algorithm directly with:
        - Jacobian computation via finite differences
        - Adaptive damping parameter
        - Direct minimization of log(det(Cov))

        Parameters
        ----------
        max_iterations : int
            Maximum number of iterations.
        tolerance : float
            Convergence tolerance for objective change.
        damping : float
            Initial damping parameter (lambda in LM).
        damping_increase : float
            Factor to increase damping on failed step.
        damping_decrease : float
            Factor to decrease damping on successful step.
        verbose : bool
            If True, print progress.

        Returns
        -------
        dict
            Optimization result.
        """
        x = self.transformation.get_coefficients_flat().copy()
        n_params = len(x)

        # Compute initial objective
        obj = self.objective_logdet(x)
        initial_det = np.exp(obj)

        if verbose:
            print(f"LM Optimization: {n_params} parameters")
            print(f"Initial log(det) = {obj:.6f}")

        lam = damping  # Damping parameter
        eps = 1e-7  # For finite difference Jacobian

        for iteration in range(max_iterations):
            # Compute residuals and Jacobian
            r = self.residuals_for_lm(x)

            # Jacobian via finite differences
            J = np.zeros((len(r), n_params))
            for i in range(n_params):
                x_plus = x.copy()
                x_plus[i] += eps
                r_plus = self.residuals_for_lm(x_plus)
                J[:, i] = (r_plus - r) / eps

            # LM update: (J^T J + lambda * I) * delta = -J^T r
            JTJ = J.T @ J
            JTr = J.T @ r

            # Try step
            try:
                delta = np.linalg.solve(JTJ + lam * np.eye(n_params), -JTr)
            except np.linalg.LinAlgError:
                delta = -JTr / (np.diag(JTJ) + lam + 1e-10)

            x_new = x + delta
            obj_new = self.objective_logdet(x_new)

            # Check if step improves objective
            if obj_new < obj:
                # Accept step
                x = x_new
                improvement = obj - obj_new
                obj = obj_new
                lam *= damping_decrease

                if verbose:
                    print(
                        f"  Iter {iteration + 1}: log(det) = {obj:.6f}, "
                        f"improvement = {improvement:.2e}, lambda = {lam:.2e}"
                    )

                if improvement < tolerance:
                    if verbose:
                        print(f"Converged after {iteration + 1} iterations")
                    break
            else:
                # Reject step, increase damping
                lam *= damping_increase
                if verbose and iteration % 10 == 0:
                    print(
                        f"  Iter {iteration + 1}: step rejected, lambda = {lam:.2e}"
                    )

        # Set final coefficients
        self.transformation.set_coefficients_flat(x)

        final_cov = self.compute_covariance()
        final_det = np.linalg.det(final_cov)

        if verbose:
            print(f"\nFinal log(det) = {np.log(final_det):.6f}")
            print(f"Final det = {final_det:.6e}")
            print(f"Reduction: {initial_det / final_det:.2f}x")

        return {
            "success": True,
            "coefficients": self.transformation.coefficients.copy(),
            "final_covariance": final_cov,
            "final_determinant": final_det,
            "initial_determinant": initial_det,
            "iterations": iteration + 1,
            "message": "Optimization completed",
        }

    def __repr__(self) -> str:
        return (
            f"CovarianceMinimizer(J={self.J}, D={self.D}, "
            f"n_params={self.transformation.num_parameters})"
        )
