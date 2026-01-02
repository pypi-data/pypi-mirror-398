"""
Vector Sampler Module

Samples D-dimensional vectors on a regular grid with specified spacing.
Points are ordered by increasing coordinate values.
"""

from typing import Tuple, Union

import numpy as np


class VectorSampler:
    """
    Samples D-dimensional vectors on a regular grid with specified spacing.

    Points are sampled on an ordered grid centered at `center` with spacing
    `delta_x` in each dimension. The distribution type determines the extent
    or weighting of the grid.

    For Gaussian: grid extends to ±n_sigma * sigma in each dimension
    For Uniform: grid extends to ±half_width in each dimension

    Parameters
    ----------
    center : np.ndarray or list
        Center point of the distribution, shape (D,).
    delta_x : float or np.ndarray
        Grid spacing in each dimension. Scalar or shape (D,).
    num_points_per_dim : int or tuple
        Number of grid points per dimension. Scalar (same for all dims)
        or tuple of length D.
    distribution : str, optional
        Distribution type: "gaussian", "uniform". Default "gaussian".
    **kwargs : dict
        Distribution-specific parameters:
        - For "gaussian": `sigma` (default: 1.0) - can be scalar or (D,) array
        - For "uniform": `half_width` is inferred from delta_x and num_points

    Attributes
    ----------
    center : np.ndarray
        Center of the distribution, shape (D,).
    delta_x : np.ndarray
        Spacing per dimension, shape (D,).
    D : int
        Dimension of the space.
    J : int
        Total number of grid points.
    num_points_per_dim : tuple
        Number of points in each dimension.
    grid_points : np.ndarray
        The sampled grid points, shape (J, D), ordered.

    Examples
    --------
    >>> sampler = VectorSampler(
    ...     center=[0.0, 0.0],
    ...     delta_x=0.5,
    ...     num_points_per_dim=5,
    ...     distribution="gaussian"
    ... )
    >>> points = sampler.sample()
    >>> points.shape
    (25, 2)  # 5x5 grid in 2D
    """

    def __init__(
        self,
        center: Union[np.ndarray, list],
        delta_x: Union[float, np.ndarray, list],
        num_points_per_dim: Union[int, Tuple[int, ...]],
        distribution: str = "gaussian",
        **kwargs,
    ):
        self.center = np.array(center, dtype=np.float64)
        self.D = len(self.center)

        # Handle delta_x
        if np.isscalar(delta_x):
            self.delta_x = np.full(self.D, delta_x, dtype=np.float64)
        else:
            self.delta_x = np.array(delta_x, dtype=np.float64)

        if len(self.delta_x) != self.D:
            raise ValueError(
                f"delta_x length ({len(self.delta_x)}) must match dimension ({self.D})"
            )

        # Handle num_points_per_dim
        if isinstance(num_points_per_dim, int):
            self.num_points_per_dim = tuple([num_points_per_dim] * self.D)
        else:
            self.num_points_per_dim = tuple(num_points_per_dim)

        if len(self.num_points_per_dim) != self.D:
            raise ValueError(
                f"num_points_per_dim length must match dimension ({self.D})"
            )

        self.J = int(np.prod(self.num_points_per_dim))
        self.distribution = distribution.lower()
        self._params = kwargs

        # Generate the grid points
        self.grid_points = self._generate_grid()

    def _generate_grid(self) -> np.ndarray:
        """Generate ordered grid points centered at self.center."""
        # Create 1D arrays for each dimension
        axes = []
        for d in range(self.D):
            n = self.num_points_per_dim[d]
            # Create symmetric grid around center
            # For n=5: indices = [-2, -1, 0, 1, 2]
            # For n=4: indices = [-1.5, -0.5, 0.5, 1.5]
            half = (n - 1) / 2.0
            indices = np.arange(n) - half
            axis = self.center[d] + indices * self.delta_x[d]
            axes.append(axis)

        # Create meshgrid and flatten in order (last dim varies fastest, then second-to-last, etc.)
        grids = np.meshgrid(*axes, indexing="ij")

        # Stack and reshape to (J, D)
        points = np.stack([g.ravel() for g in grids], axis=-1)

        return points

    def sample(self) -> np.ndarray:
        """
        Return the grid points.

        Returns
        -------
        np.ndarray
            Grid points of shape (J, D), ordered by increasing coordinates.
        """
        return self.grid_points.copy()

    def get_weights(self) -> np.ndarray:
        """
        Compute distribution weights for each grid point.

        Returns
        -------
        np.ndarray
            Weights of shape (J,), based on the distribution type.
        """
        if self.distribution == "gaussian":
            return self._gaussian_weights()
        elif self.distribution == "uniform":
            return self._uniform_weights()
        else:
            raise ValueError(f"Unknown distribution: {self.distribution}")

    def _gaussian_weights(self) -> np.ndarray:
        """
        Compute Gaussian weights: exp(-||x - center||² / (2σ²))

        With per-dimension sigma:
        w(x) = exp(-Σ_d (x_d - center_d)² / (2σ_d²))
        """
        sigma = self._params.get("sigma", 1.0)
        if np.isscalar(sigma):
            sigma = np.full(self.D, sigma)
        else:
            sigma = np.array(sigma)

        sigma_sq = sigma**2

        # diff[j, d] = grid_points[j, d] - center[d]
        diff = self.grid_points - self.center

        # Weighted squared distance
        weighted_sq_dist = np.sum(diff**2 / sigma_sq, axis=1)

        weights = np.exp(-weighted_sq_dist / 2.0)
        return weights

    def _uniform_weights(self) -> np.ndarray:
        """Uniform weights: all points have weight 1."""
        return np.ones(self.J)

    def get_extent(self) -> np.ndarray:
        """
        Get the extent of the grid in each dimension.

        Returns
        -------
        np.ndarray
            Array of shape (D, 2) with [min, max] for each dimension.
        """
        extent = np.zeros((self.D, 2))
        for d in range(self.D):
            extent[d, 0] = self.grid_points[:, d].min()
            extent[d, 1] = self.grid_points[:, d].max()
        return extent

    def __repr__(self) -> str:
        return (
            f"VectorSampler(D={self.D}, J={self.J}, "
            f"delta_x={self.delta_x.tolist()}, "
            f"num_points_per_dim={self.num_points_per_dim}, "
            f"distribution='{self.distribution}')"
        )

    def __len__(self) -> int:
        return self.J
