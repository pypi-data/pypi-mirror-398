"""
Utility functions for entra.
"""

import math
from typing import Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse


def gradient_component(
    scalar_field: np.ndarray,
    dx: float,
    axis: int,
    grid_shape: Tuple[int, ...] = None,
) -> np.ndarray:
    """
    Compute partial derivative of a scalar field along one axis.

    Parameters
    ----------
    scalar_field : np.ndarray
        Scalar field in flat (N,) or grid (N_1, ..., N_D) format.
    dx : float
        Grid spacing along the specified axis.
    axis : int
        The axis along which to compute the derivative.
    grid_shape : tuple, optional
        Required if scalar_field is flat (N,) format.

    Returns
    -------
    np.ndarray
        Partial derivative ∂f/∂x_axis with same shape as input.
        Values are signed (positive or negative).
    """
    scalar_field = np.asarray(scalar_field)
    is_flat = scalar_field.ndim == 1

    if is_flat:
        if grid_shape is None:
            raise ValueError("For flat format, grid_shape must be provided.")
        scalar_field = scalar_field.reshape(grid_shape)

    D = scalar_field.ndim
    grad = np.zeros_like(scalar_field)

    # Central difference for interior
    slices_forward = [slice(None)] * D
    slices_backward = [slice(None)] * D
    slices_center = [slice(None)] * D

    slices_forward[axis] = slice(2, None)
    slices_backward[axis] = slice(None, -2)
    slices_center[axis] = slice(1, -1)

    grad[tuple(slices_center)] = (
        scalar_field[tuple(slices_forward)] - scalar_field[tuple(slices_backward)]
    ) / (2 * dx)

    # Forward difference at start boundary
    slices_start = [slice(None)] * D
    slices_start_next = [slice(None)] * D
    slices_start[axis] = 0
    slices_start_next[axis] = 1

    grad[tuple(slices_start)] = (
        scalar_field[tuple(slices_start_next)] - scalar_field[tuple(slices_start)]
    ) / dx

    # Backward difference at end boundary
    slices_end = [slice(None)] * D
    slices_end_prev = [slice(None)] * D
    slices_end[axis] = -1
    slices_end_prev[axis] = -2

    grad[tuple(slices_end)] = (
        scalar_field[tuple(slices_end)] - scalar_field[tuple(slices_end_prev)]
    ) / dx

    if is_flat:
        return grad.ravel()
    return grad


def divergence_components(
    vector_field: np.ndarray,
    dx: Union[float, np.ndarray] = 1.0,
    grid_shape: Tuple[int, ...] = None,
) -> np.ndarray:
    """
    Compute individual components of divergence (signed partial derivatives).

    Returns ∂F_d/∂x_d for each component d, preserving signs.
    The sum of these components gives the total divergence.

    Parameters
    ----------
    vector_field : np.ndarray
        Vector field in flat (N, D) or grid (N_1, ..., N_D, D) format.
    dx : float or array-like
        Grid spacing. Scalar or array of shape (D,).
    grid_shape : tuple, optional
        Required if vector_field is flat format.

    Returns
    -------
    np.ndarray
        Individual divergence components with shape:
        - Flat input: (N, D) where [:, d] = ∂F_d/∂x_d (signed)
        - Grid input: (N_1, ..., N_D, D) where [..., d] = ∂F_d/∂x_d (signed)

    Examples
    --------
    >>> V = np.random.randn(100, 2)  # 2D vector field, J=100
    >>> components = divergence_components(V, dx=0.1, grid_shape=(10, 10))
    >>> components.shape
    (100, 2)
    >>> # components[:, 0] = ∂V_x/∂x (signed)
    >>> # components[:, 1] = ∂V_y/∂y (signed)
    >>> # Total divergence = components[:, 0] + components[:, 1]
    """
    vector_field = np.asarray(vector_field)
    is_flat = vector_field.ndim == 2

    if is_flat:
        if grid_shape is None:
            raise ValueError("For flat format (N, D), grid_shape must be provided.")
        N, D = vector_field.shape
        expected_N = np.prod(grid_shape)
        if N != expected_N:
            raise ValueError(
                f"vector_field has {N} points but grid_shape {grid_shape} "
                f"implies {expected_N} points."
            )
        vector_field = vector_field.reshape(*grid_shape, D)

    D = vector_field.shape[-1]

    if np.isscalar(dx):
        dx = np.full(D, dx)
    else:
        dx = np.asarray(dx)

    # Store individual components
    components = np.zeros_like(vector_field)

    for d in range(D):
        F_d = vector_field[..., d]
        grad_d = np.zeros_like(F_d)

        # Central difference for interior
        slices_forward = [slice(None)] * D
        slices_backward = [slice(None)] * D
        slices_center = [slice(None)] * D

        slices_forward[d] = slice(2, None)
        slices_backward[d] = slice(None, -2)
        slices_center[d] = slice(1, -1)

        grad_d[tuple(slices_center)] = (
            F_d[tuple(slices_forward)] - F_d[tuple(slices_backward)]
        ) / (2 * dx[d])

        # Forward difference at start boundary
        slices_start = [slice(None)] * D
        slices_start_next = [slice(None)] * D
        slices_start[d] = 0
        slices_start_next[d] = 1

        grad_d[tuple(slices_start)] = (
            F_d[tuple(slices_start_next)] - F_d[tuple(slices_start)]
        ) / dx[d]

        # Backward difference at end boundary
        slices_end = [slice(None)] * D
        slices_end_prev = [slice(None)] * D
        slices_end[d] = -1
        slices_end_prev[d] = -2

        grad_d[tuple(slices_end)] = (
            F_d[tuple(slices_end)] - F_d[tuple(slices_end_prev)]
        ) / dx[d]

        components[..., d] = grad_d

    if is_flat:
        return components.reshape(-1, D)
    return components


def divergence(
    vector_field: np.ndarray,
    dx: Union[float, np.ndarray] = 1.0,
    grid_shape: Tuple[int, ...] = None,
) -> np.ndarray:
    """
    Compute divergence of a D-dimensional vector field.

    div(F) = ∂F_1/∂x_1 + ∂F_2/∂x_2 + ... + ∂F_D/∂x_D

    The result is the sum of signed partial derivatives. Use divergence_components()
    to get individual ∂F_d/∂x_d terms with their signs preserved.

    Parameters
    ----------
    vector_field : np.ndarray
        Vector field array in one of two formats:
        - Grid format: (N_1, N_2, ..., N_D, D) where N_i is grid size in dimension i
        - Flat format: (N, D) where N = N_1 * N_2 * ... * N_D (requires grid_shape)
    dx : float or array-like
        Grid spacing. Scalar for uniform spacing, or array of shape (D,).
    grid_shape : tuple, optional
        Required if vector_field is in flat (N, D) format.
        Specifies the grid dimensions, e.g., (20, 20) for a 20x20 2D grid.

    Returns
    -------
    np.ndarray
        Divergence field (signed values, not magnitudes):
        - Grid format input: shape (N_1, N_2, ..., N_D)
        - Flat format input: shape (N,) if grid_shape provided, else grid format

    Examples
    --------
    >>> # Grid format: 2D vector field on 20x20 grid
    >>> F_grid = np.random.randn(20, 20, 2)
    >>> div_F = divergence(F_grid, dx=0.1)
    >>> div_F.shape
    (20, 20)

    >>> # Flat format: (400, 2) with grid_shape=(20, 20)
    >>> F_flat = np.random.randn(400, 2)
    >>> div_F = divergence(F_flat, dx=0.1, grid_shape=(20, 20))
    >>> div_F.shape
    (400,)

    >>> # Get individual components to see how they sum
    >>> components = divergence_components(F_flat, dx=0.1, grid_shape=(20, 20))
    >>> np.allclose(div_F, components[:, 0] + components[:, 1])
    True
    """
    vector_field = np.asarray(vector_field)

    # Check if flat format (N, D) or grid format (N_1, ..., N_D, D)
    is_flat = vector_field.ndim == 2

    if is_flat:
        if grid_shape is None:
            raise ValueError(
                "For flat format (N, D), grid_shape must be provided. "
                "E.g., grid_shape=(20, 20) for a 20x20 grid."
            )
        N, D = vector_field.shape
        expected_N = np.prod(grid_shape)
        if N != expected_N:
            raise ValueError(
                f"vector_field has {N} points but grid_shape {grid_shape} "
                f"implies {expected_N} points."
            )
        # Reshape to grid format
        vector_field = vector_field.reshape(*grid_shape, D)

    D = vector_field.shape[-1]

    if np.isscalar(dx):
        dx = np.full(D, dx)
    else:
        dx = np.asarray(dx)

    div = np.zeros(vector_field.shape[:-1])

    for d in range(D):
        F_d = vector_field[..., d]
        grad_d = np.zeros_like(F_d)

        # Central difference for interior
        slices_forward = [slice(None)] * D
        slices_backward = [slice(None)] * D
        slices_center = [slice(None)] * D

        slices_forward[d] = slice(2, None)
        slices_backward[d] = slice(None, -2)
        slices_center[d] = slice(1, -1)

        grad_d[tuple(slices_center)] = (
            F_d[tuple(slices_forward)] - F_d[tuple(slices_backward)]
        ) / (2 * dx[d])

        # Forward difference at start boundary
        slices_start = [slice(None)] * D
        slices_start_next = [slice(None)] * D
        slices_start[d] = 0
        slices_start_next[d] = 1

        grad_d[tuple(slices_start)] = (
            F_d[tuple(slices_start_next)] - F_d[tuple(slices_start)]
        ) / dx[d]

        # Backward difference at end boundary
        slices_end = [slice(None)] * D
        slices_end_prev = [slice(None)] * D
        slices_end[d] = -1
        slices_end_prev[d] = -2

        grad_d[tuple(slices_end)] = (
            F_d[tuple(slices_end)] - F_d[tuple(slices_end_prev)]
        ) / dx[d]

        div += grad_d

    # If input was flat, return flat
    if is_flat:
        return div.ravel()

    return div


def is_divergence_free(
    vector_field: np.ndarray,
    dx: Union[float, np.ndarray] = 1.0,
    grid_shape: Tuple[int, ...] = None,
    rtol: float = 1e-5,
) -> Tuple[bool, float]:
    """
    Check if a vector field is approximately divergence-free.

    Parameters
    ----------
    vector_field : np.ndarray
        Vector field in grid format (N_1, ..., N_D, D) or flat format (N, D).
    dx : float or array-like
        Grid spacing.
    grid_shape : tuple, optional
        Required if vector_field is in flat format.
    rtol : float
        Relative tolerance. Field is divergence-free if
        max|div(F)| / max|F| < rtol.

    Returns
    -------
    is_free : bool
        True if field is approximately divergence-free.
    relative_div : float
        The ratio max|div(F)| / max|F|.
    """
    div_F = divergence(vector_field, dx, grid_shape)

    field_magnitude = np.max(np.abs(vector_field))
    div_magnitude = np.max(np.abs(div_F))

    if field_magnitude == 0:
        relative_div = 0.0
    else:
        relative_div = div_magnitude / field_magnitude

    return relative_div < rtol, relative_div


def tensor_basis_column_divergence(
    Phi: np.ndarray, dx: Union[float, np.ndarray], grid_shape: Tuple[int, ...]
) -> np.ndarray:
    """
    Compute divergence for each column of tensor basis output.

    The tensor basis Φ has shape (J, L, D, D) where:
    - J = number of evaluation points on grid
    - L = number of basis function centers
    - D×D = matrix output at each point

    Each column d of the D×D matrix (for center l) is a vector field with D
    components, each having J values. This function computes div(Φ[:, l, :, d])
    for all l and d.

    Parameters
    ----------
    Phi : np.ndarray
        Tensor basis output of shape (J, L, D, D).
    dx : float or array-like
        Grid spacing in each dimension.
    grid_shape : tuple
        Shape of the evaluation grid, e.g., (20, 20) for 2D with J=400.

    Returns
    -------
    np.ndarray
        Divergence values of shape (J, L, D) where result[:, l, d] is the
        divergence of the d-th column vector field for center l.

    Examples
    --------
    >>> # Tensor basis evaluated on 5x5 grid with 3 centers in 2D
    >>> Phi = tensor_basis.evaluate(eval_points)  # shape (25, 3, 2, 2)
    >>> div_cols = tensor_basis_column_divergence(Phi, dx=0.5, grid_shape=(5, 5))
    >>> div_cols.shape
    (25, 3, 2)  # divergence of each column for each center at each point
    """
    J, L, D, D2 = Phi.shape
    assert D == D2, f"Expected square matrices, got ({D}, {D2})"

    expected_J = np.prod(grid_shape)
    if J != expected_J:
        raise ValueError(
            f"Phi has J={J} points but grid_shape {grid_shape} "
            f"implies {expected_J} points."
        )

    result = np.zeros((J, L, D))

    for center_idx in range(L):
        for d in range(D):
            # Extract column d of matrix for center center_idx: shape (J, D)
            # Phi[:, center_idx, :, d] gives the d-th column as a vector field
            vector_field = Phi[:, center_idx, :, d]

            # Compute divergence
            div = divergence(vector_field, dx, grid_shape)
            result[:, center_idx, d] = div

    return result


def verify_tensor_basis_divergence_free(
    Phi: np.ndarray,
    dx: Union[float, np.ndarray],
    grid_shape: Tuple[int, ...],
    rtol: float = 1e-3,
) -> Tuple[bool, np.ndarray]:
    """
    Verify that all columns of tensor basis output are divergence-free.

    Parameters
    ----------
    Phi : np.ndarray
        Tensor basis output of shape (J, L, D, D).
    dx : float or array-like
        Grid spacing.
    grid_shape : tuple
        Shape of the evaluation grid.
    rtol : float
        Relative tolerance for divergence-free check.

    Returns
    -------
    all_free : bool
        True if all columns are approximately divergence-free.
    relative_divs : np.ndarray
        Shape (L, D) with relative divergence for each center/column.
    """
    J, L, D, _ = Phi.shape

    div_cols = tensor_basis_column_divergence(Phi, dx, grid_shape)

    # Compute relative divergence for each (center_idx, d)
    relative_divs = np.zeros((L, D))

    for center_idx in range(L):
        for d in range(D):
            # Vector field magnitude for this column
            vec_field = Phi[:, center_idx, :, d]
            field_mag = np.max(np.abs(vec_field))

            # Divergence magnitude
            div_mag = np.max(np.abs(div_cols[:, center_idx, d]))

            if field_mag > 0:
                relative_divs[center_idx, d] = div_mag / field_mag
            else:
                relative_divs[center_idx, d] = 0.0

    all_free = np.all(relative_divs < rtol)
    return all_free, relative_divs


def verify_divergence_free_symmetric(
    vector_field: np.ndarray,
    dx: Union[float, np.ndarray],
    grid_shape: Tuple[int, ...],
    cancellation_threshold: float = 0.95,
) -> Tuple[bool, dict]:
    """
    Verify divergence-free property by checking symmetric cancellation.

    A truly divergence-free field has equal positive and negative divergence
    regions that cancel when integrated. This function checks if the positive
    and negative parts of the divergence sum to approximately zero.

    Parameters
    ----------
    vector_field : np.ndarray
        Vector field in flat (N, D) format.
    dx : float or array-like
        Grid spacing.
    grid_shape : tuple
        Shape of the evaluation grid.
    cancellation_threshold : float
        Minimum cancellation ratio required (0-1). Default 0.95 means
        positive and negative parts must cancel by at least 95%.

    Returns
    -------
    is_divergence_free : bool
        True if divergence shows symmetric cancellation.
    stats : dict
        Dictionary with:
        - 'positive_sum': sum of positive divergence values
        - 'negative_sum': sum of negative divergence values
        - 'total_sum': total sum (should be ~0)
        - 'cancellation_ratio': how well positive/negative cancel (0-1)
    """
    div_field = divergence(vector_field, dx, grid_shape)

    positive_sum = np.sum(div_field[div_field > 0])
    negative_sum = np.sum(div_field[div_field < 0])
    total_sum = np.sum(div_field)

    # Cancellation ratio: 1 means perfect cancellation
    total_magnitude = np.abs(positive_sum) + np.abs(negative_sum)
    if total_magnitude > 0:
        cancellation_ratio = 1.0 - np.abs(total_sum) / total_magnitude
    else:
        cancellation_ratio = 1.0

    is_divergence_free = cancellation_ratio >= cancellation_threshold

    stats = {
        "positive_sum": positive_sum,
        "negative_sum": negative_sum,
        "total_sum": total_sum,
        "cancellation_ratio": cancellation_ratio,
    }

    return is_divergence_free, stats


def shannon_entropy_gaussian(cov: np.ndarray) -> float:
    """
    Compute Shannon entropy assuming Gaussian distribution.

    For a D-dimensional Gaussian with covariance matrix Cov:
    H = (D/2) * log(2*pi*e) + (1/2) * log(det(Cov))
      = (D/2) * (1 + log(2*pi)) + (1/2) * log(det(Cov))

    Parameters
    ----------
    cov : np.ndarray
        Covariance matrix of shape (D, D).

    Returns
    -------
    float
        Shannon entropy in nats.
    """
    D = cov.shape[0]
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        return np.inf
    entropy = 0.5 * D * (1 + np.log(2 * np.pi)) + 0.5 * logdet
    return entropy


def shannon_entropy_knn(points: np.ndarray, k: int = 3) -> float:
    """
    Estimate Shannon entropy using k-nearest neighbor method (Kozachenko-Leonenko).

    This is a non-parametric estimator that doesn't assume any distribution shape.
    For a volume-preserving transformation, this estimate should remain constant.

    Parameters
    ----------
    points : np.ndarray
        Points of shape (J, D).
    k : int
        Number of nearest neighbors to use. Default is 3.

    Returns
    -------
    float
        Estimated Shannon entropy in nats.
    """
    from scipy.spatial import cKDTree
    from scipy.special import digamma

    points = np.asarray(points)
    J, D = points.shape

    # Build KD-tree and find k-th nearest neighbor distances
    tree = cKDTree(points)
    # Query k+1 neighbors (first one is the point itself with distance 0)
    distances, _ = tree.query(points, k=k + 1)
    # Take the k-th neighbor distance (index k, since index 0 is self)
    rho_k = distances[:, k]

    # Kozachenko-Leonenko estimator
    # H = D * mean(log(rho_k)) + log(V_D) + log(J-1) - digamma(k)
    # where V_D is volume of unit ball in D dimensions
    # V_D = pi^(D/2) / Gamma(D/2 + 1)
    log_v_d = (D / 2) * np.log(np.pi) - math.lgamma(D / 2 + 1)

    # Avoid log(0) for duplicate points
    rho_k = np.maximum(rho_k, 1e-10)

    entropy = D * np.mean(np.log(2 * rho_k)) + log_v_d + digamma(J) - digamma(k)

    return entropy


def plot_2d_projections(points, title_prefix, entropy=None, fig=None, axes=None):
    """Plot XY, XZ, YZ projections of 3D points."""
    if fig is None or axes is None:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    projections = [
        (0, 1, 'XY'),
        (0, 2, 'XZ'),
        (1, 2, 'YZ')
    ]

    for ax, (i, j, name) in zip(axes, projections):
        pts_2d = points[:, [i, j]]
        mean_2d = np.mean(pts_2d, axis=0)
        cov_2d = np.cov(pts_2d, rowvar=False)
        det_2d = np.linalg.det(cov_2d)

        ax.scatter(pts_2d[:, 0], pts_2d[:, 1], alpha=0.3, s=10)
        plot_covariance_ellipse(ax, mean_2d, cov_2d, n_std=2,
                                fill=False, color='red', linewidth=2)

        ax.set_xlabel(['X', 'X', 'Y'][projections.index((i, j, name))])
        ax.set_ylabel(['Y', 'Z', 'Z'][projections.index((i, j, name))])
        ax.set_title(f'{name} Projection\ndet = {det_2d:.2e}')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

    if entropy is not None:
        fig.suptitle(f'{title_prefix} (H = {entropy:.4f} nats)', fontsize=14)
    else:
        fig.suptitle(title_prefix, fontsize=14)

    plt.tight_layout()
    return fig, axes


def shannon_entropy_uniform(points: np.ndarray) -> float:
    """
    Compute Shannon entropy assuming uniform distribution.

    For a D-dimensional uniform distribution over a hypercube with volume V:
    H = log(V)

    The volume is computed from the bounding box of the points. If delta_x is
    provided, it is added to the extent in each dimension to account for the
    cell size (since points at the boundary represent the center of their cells).

    Parameters
    ----------
    points : np.ndarray
        Points of shape (J, D).
    delta_x : float, optional
        Grid spacing. If provided, volume = prod((extent + delta_x) for each dim).
        This accounts for the fact that a 20x20 grid with delta_x=1 spans
        -9.5 to 9.5 (extent=19) but represents a volume of 20x20.

    Returns
    -------
    float
        Shannon entropy in nats.
    """
    points = np.asarray(points)
    D = points.shape[1]

    # Compute volume from bounding box
    volume = 1.0
    for d in range(D):
        extent = points[:, d].max() - points[:, d].min()

        volume *= extent

    if volume <= 0:
        return -np.inf
    return np.log(volume)


def plot_covariance_ellipse(
    ax, mean: np.ndarray, cov: np.ndarray, n_std: int = 2, **kwargs
):
    """
    Plot a covariance ellipse on a matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to plot on.
    mean : np.ndarray
        Mean of the distribution, shape (2,).
    cov : np.ndarray
        Covariance matrix, shape (2, 2).
    n_std : int
        Number of standard deviations for the ellipse radius. Default is 2.
    **kwargs
        Additional keyword arguments passed to matplotlib.patches.Ellipse.

    Returns
    -------
    matplotlib.patches.Ellipse
        The ellipse patch added to the axes.
    """
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = eigvals.argsort()[::-1]
    eigvals, eigvecs = eigvals[order], eigvecs[:, order]

    angle = np.degrees(np.arctan2(*eigvecs[:, 0][::-1]))
    width, height = 2 * n_std * np.sqrt(eigvals)

    ellipse = Ellipse(xy=mean, width=width, height=height, angle=angle, **kwargs)
    ax.add_patch(ellipse)
    return ellipse
