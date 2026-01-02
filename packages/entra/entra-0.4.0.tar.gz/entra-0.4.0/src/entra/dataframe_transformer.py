"""
DataFrame Transformer for applying entropy-conserving transformations to real data.

Provides a high-level API for transforming data from CSV files or pandas DataFrames
towards Gaussian distributions using divergence-free vector fields.
"""

import numpy as np
import pandas as pd

from .covariance_minimizer import CovarianceMinimizer
from .tensor_basis import TensorBasis
from .transformation import Transformation
from .utils import shannon_entropy_gaussian, shannon_entropy_uniform


class DataFrameTransformer:
    """
    High-level transformer for applying entropy-conserving transformations to DataFrames.

    This class provides a simple interface for:
    1. Reading vector data from a pandas DataFrame
    2. Fitting a divergence-free transformation to minimize covariance determinant
    3. Transforming the data towards Gaussian form
    4. Writing results back to a DataFrame

    Parameters
    ----------
    sigma : float, optional
        Width parameter for Gaussian RBF basis functions. Default is 5.0.
    max_iterations : int, optional
        Maximum iterations for optimization. Default is 1000.
    tolerance : float, optional
        Convergence tolerance. Default is 1e-18.
    verbose : bool, optional
        Print progress during optimization. Default is True.

    Examples
    --------
    >>> import pandas as pd
    >>> from entra import DataFrameTransformer
    >>>
    >>> # Read data
    >>> df = pd.read_csv("data.csv")
    >>>
    >>> # Transform
    >>> transformer = DataFrameTransformer(sigma=5.0)
    >>> df_transformed = transformer.fit_transform(df, columns=['x', 'y', 'z'])
    >>>
    >>> # Save results
    >>> df_transformed.to_csv("transformed_data.csv", index=False)
    """

    def __init__(
        self,
        sigma: float = 5.0,
        max_iterations: int = 1000,
        tolerance: float = 1e-18,
        verbose: bool = True,
        progress_callback: callable = None,
    ):
        self.sigma = sigma
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.verbose = verbose
        self.progress_callback = progress_callback

        # Fitted attributes
        self.transformation_ = None
        self.basis_ = None
        self.columns_ = None
        self.history_ = None
        self.centers_ = None

    def _create_centers(self, points):
        """
        Create centers along the coordinate axes.

        Same pattern as covariance_optimization.ipynb.
        """
        D = points.shape[1]
        max_coord = int(np.max(np.abs(points)))

        center_list = []
        for i in range(max_coord):
            for d in range(D):
                # Positive direction
                c = [0.0] * D
                c[d] = float(i)
                center_list.append(c)
                # Negative direction
                c = [0.0] * D
                c[d] = float(-i)
                center_list.append(c)

        return np.asarray(center_list)

    def fit(self, df, columns: list[str]):
        """
        Fit the transformation to minimize covariance determinant.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame containing the data.
        columns : list of str
            Column names containing the coordinates to transform.

        Returns
        -------
        self
            Fitted transformer.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        self.columns_ = columns
        points = df[columns].values.astype(np.float64)
        J, D = points.shape

        # Create centers along axes
        self.centers_ = self._create_centers(points)
        L = self.centers_.shape[0]

        if self.verbose:
            print(f"Fitting transformer: {J} points, {D} dimensions")
            print(f"  sigma = {self.sigma}")
            print(f"  L = {L} basis centers")

        # Create basis and transformation
        self.basis_ = TensorBasis(self.centers_, sigma=self.sigma)
        self.transformation_ = Transformation(self.basis_)

        # Create minimizer
        minimizer = CovarianceMinimizer(self.transformation_, points)

        # Run optimization
        self._optimize(minimizer, points)

        return self

    def _optimize(self, minimizer, points):
        """Run Levenberg-Marquardt optimization."""
        x = self.transformation_.get_coefficients_flat().copy()
        n_params = len(x)

        lam = 1.0
        eps = 1e-7

        # Initial values
        cov = minimizer.compute_covariance(x)
        det_val = np.linalg.det(cov)
        gaussian_entropy = shannon_entropy_gaussian(cov)

        self.history_ = {
            "iteration": [0],
            "determinant": [det_val],
            "gaussian_entropy": [gaussian_entropy],
            "lambda": [lam],
        }

        if self.verbose:
            print(
                "\n  Note: H(Gaussian) is the entropy IF the distribution were Gaussian with"
            )
            print(
                "  the current covariance. It decreases because we start from uniform."
            )
            print(
                f"\n  {'Iter':>5}  {'Determinant':>14}  {'H(Gaussian)':>12}  {'Lambda':>10}"
            )
            print("  " + "-" * 50)
            print(
                f"  {0:>5}  {det_val:>14.6e}  {gaussian_entropy:>12.4f}  {lam:>10.2e}"
            )

        # Initial progress callback
        if self.progress_callback is not None:
            self.progress_callback(0, self.max_iterations, det_val, gaussian_entropy)

        for iteration in range(1, self.max_iterations + 1):
            # Compute residuals and Jacobian
            r = minimizer.residuals_for_lm(x)

            J_mat = np.zeros((len(r), n_params))
            for i in range(n_params):
                x_plus = x.copy()
                x_plus[i] += eps
                r_plus = minimizer.residuals_for_lm(x_plus)
                J_mat[:, i] = (r_plus - r) / eps

            # LM update
            JTJ = J_mat.T @ J_mat
            JTr = J_mat.T @ r

            try:
                delta = np.linalg.solve(JTJ + lam * np.eye(n_params), -JTr)
            except np.linalg.LinAlgError:
                delta = -JTr / (np.diag(JTJ) + lam + 1e-10)

            x_new = x + delta
            obj_new = minimizer.objective_logdet(x_new)
            obj_old = minimizer.objective_logdet(x)

            if obj_new < obj_old:
                x = x_new
                lam *= 0.1
                improvement = abs(obj_old - obj_new)

                cov = minimizer.compute_covariance(x)
                det_val = np.linalg.det(cov)
                gaussian_entropy = shannon_entropy_gaussian(cov)

                self.history_["iteration"].append(iteration)
                self.history_["determinant"].append(det_val)
                self.history_["gaussian_entropy"].append(gaussian_entropy)
                self.history_["lambda"].append(lam)

                if self.verbose and (iteration % 50 == 0 or iteration <= 5):
                    print(
                        f"  {iteration:>5}  {det_val:>14.6e}  {gaussian_entropy:>12.4f}  {lam:>10.2e}"
                    )

                # Progress callback
                if self.progress_callback is not None:
                    self.progress_callback(
                        iteration, self.max_iterations, det_val, gaussian_entropy
                    )

                if improvement < self.tolerance:
                    if self.verbose:
                        print(f"\n  Converged after {iteration} iterations")
                    break
            else:
                lam *= 10.0

        # Set final coefficients
        self.transformation_.set_coefficients_flat(x)

        if self.verbose:
            print(
                f"\n  Final: det = {det_val:.6e}, H(Gaussian) = {gaussian_entropy:.4f}"
            )

    def transform(self, df):
        """
        Transform data using the fitted transformation.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame containing the data.

        Returns
        -------
        pandas.DataFrame
            Transformed DataFrame with same structure as input.
        """
        if self.transformation_ is None:
            raise RuntimeError("Transformer not fitted. Call fit() first.")

        points = df[self.columns_].values.astype(np.float64)
        transformed_points = self.transformation_.transform(points)

        # Create output DataFrame
        df_out = df.copy()
        df_out[self.columns_] = transformed_points

        return df_out

    def fit_transform(self, df, columns: list[str]):
        """
        Fit the transformation and transform data in one step.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame containing the data.
        columns : list of str
            Column names containing the coordinates to transform.

        Returns
        -------
        pandas.DataFrame
            Transformed DataFrame with same structure as input.
        """
        self.fit(df, columns)
        return self.transform(df)

    def get_entropy_comparison(self, df_original, df_transformed):
        """
        Compare entropy before and after transformation.

        Parameters
        ----------
        df_original : pandas.DataFrame
            Original DataFrame before transformation.
        df_transformed : pandas.DataFrame
            Transformed DataFrame.

        Returns
        -------
        dict
            Dictionary with entropy estimates.
        """
        if self.columns_ is None:
            raise RuntimeError("Transformer not fitted. Call fit() first.")

        points_original = df_original[self.columns_].values.astype(np.float64)
        points_transformed = df_transformed[self.columns_].values.astype(np.float64)

        cov_original = np.cov(points_original, rowvar=False)
        cov_transformed = np.cov(points_transformed, rowvar=False)

        return {
            "original": {
                "uniform_entropy": shannon_entropy_uniform(points_original),
                "determinant": np.linalg.det(cov_original),
            },
            "transformed": {
                "gaussian_entropy": shannon_entropy_gaussian(cov_transformed),
                "determinant": np.linalg.det(cov_transformed),
            },
        }


def transform_csv(
    input_path: str,
    output_path: str,
    columns: list[str],
    sigma: float = 5.0,
    verbose: bool = True,
):
    """
    Transform vectors in a CSV file towards Gaussian distribution.

    Convenience function for CSV-to-CSV transformation.

    Parameters
    ----------
    input_path : str
        Path to input CSV file.
    output_path : str
        Path to output CSV file.
    columns : list of str
        Column names containing the coordinates to transform.
    sigma : float, optional
        Width parameter for Gaussian RBF basis functions. Default is 5.0.
    verbose : bool, optional
        Print progress. Default is True.

    Returns
    -------
    dict
        Entropy comparison before and after transformation.

    Examples
    --------
    >>> from entra import transform_csv
    >>> entropy = transform_csv(
    ...     "input.csv",
    ...     "output.csv",
    ...     columns=["x", "y", "z"],
    ...     sigma=5.0
    ... )
    """
    if verbose:
        print(f"Reading: {input_path}")

    df = pd.read_csv(input_path)

    transformer = DataFrameTransformer(
        sigma=sigma,
        verbose=verbose,
    )

    df_transformed = transformer.fit_transform(df, columns)

    if verbose:
        print(f"\nWriting: {output_path}")

    df_transformed.to_csv(output_path, index=False)

    entropy = transformer.get_entropy_comparison(df, df_transformed)

    if verbose:
        print("\nEntropy comparison:")
        print(
            f"  Original uniform entropy: {entropy['original']['uniform_entropy']:.6f}"
        )
        print(f"  Original k-NN entropy:    {entropy['original']['knn_entropy']:.6f}")
        print(
            f"  Transformed k-NN entropy: {entropy['transformed']['knn_entropy']:.6f}"
        )
        print(
            f"  Transformed Gaussian H:   {entropy['transformed']['gaussian_entropy']:.6f}"
        )
        print(f"\n  Original determinant:     {entropy['original']['determinant']:.6e}")
        print(
            f"  Transformed determinant:  {entropy['transformed']['determinant']:.6e}"
        )

    return entropy
