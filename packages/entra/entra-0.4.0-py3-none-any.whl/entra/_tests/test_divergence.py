"""Unit tests for utils module."""

import numpy as np
import pytest

from entra import (
    TensorBasis,
    VectorSampler,
    divergence,
    is_divergence_free,
    tensor_basis_column_divergence,
    verify_tensor_basis_divergence_free,
)


class TestDivergence:
    """Tests for divergence function."""

    def test_divergence_2d_grid_format(self):
        """Test divergence with 2D grid format input."""
        # Create a simple vector field on 10x10 grid
        grid_shape = (100, 100)
        F = np.zeros((*grid_shape, 2))
        # F = (x, y) has div = 2
        x = np.linspace(-1, 1, 10)
        y = np.linspace(-1, 1, 10)
        X, Y = np.meshgrid(x, y, indexing="ij")
        F[..., 0] = X
        F[..., 1] = Y

        dx = 2.0 / 9  # spacing
        div_F = divergence(F, dx=dx)

        # Interior should be approximately 2
        assert div_F.shape == grid_shape
        assert np.allclose(div_F[2:-2, 2:-2], 2.0, atol=0.1)

    def test_divergence_2d_flat_format(self):
        """Test divergence with flat (N, D) format."""
        grid_shape = (10, 10)
        J = 100

        x = np.linspace(-1, 1, 10)
        y = np.linspace(-1, 1, 10)
        X, Y = np.meshgrid(x, y, indexing="ij")

        # Flat format (100, 2)
        F_flat = np.stack([X.ravel(), Y.ravel()], axis=-1)

        dx = 2.0 / 9
        div_F = divergence(F_flat, dx=dx, grid_shape=grid_shape)

        assert div_F.shape == (J,)

    def test_divergence_3d(self):
        """Test divergence with 3D grid."""
        grid_shape = (5, 5, 5)
        F = np.ones((*grid_shape, 3))  # Constant field

        div_F = divergence(F, dx=0.1)

        # Divergence of constant field should be 0
        assert div_F.shape == grid_shape
        assert np.allclose(div_F, 0.0)

    def test_divergence_requires_grid_shape_for_flat(self):
        """Test that flat format requires grid_shape."""
        F_flat = np.random.randn(100, 2)

        with pytest.raises(ValueError, match="grid_shape must be provided"):
            divergence(F_flat, dx=0.1)


class TestIsDivergenceFree:
    """Tests for is_divergence_free function."""

    def test_divergence_free_field(self):
        """Test detection of divergence-free field."""
        x = np.linspace(-1, 1, 20)
        y = np.linspace(-1, 1, 20)
        X, Y = np.meshgrid(x, y, indexing="ij")

        # F = (-y, x) is divergence-free
        F = np.stack([-Y, X], axis=-1)

        dx = 2.0 / 19
        is_free, rel_div = is_divergence_free(F, dx=dx, rtol=0.1)

        assert is_free
        assert rel_div < 0.1

    def test_non_divergence_free_field(self):
        """Test detection of non-divergence-free field."""
        x = np.linspace(-1, 1, 20)
        y = np.linspace(-1, 1, 20)
        X, Y = np.meshgrid(x, y, indexing="ij")

        # F = (x, y) has div = 2
        F = np.stack([X, Y], axis=-1)

        dx = 2.0 / 19
        is_free, rel_div = is_divergence_free(F, dx=dx, rtol=0.01)

        assert not is_free


class TestTensorBasisColumnDivergence:
    """Tests for tensor_basis_column_divergence function."""

    def test_output_shape(self):
        """Test output shape is (J, L, D)."""
        # 2D, 20x20 grid, 3 centers
        grid_shape = (20, 20)
        J = 400
        L = 3
        D = 2

        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=0.1, num_points_per_dim=20
        )
        eval_points = sampler.sample()

        centers = np.array([[0.0, 0.0], [0.5, 0.0], [0.0, 0.5]])
        basis = TensorBasis(centers, sigma=0.2)

        Phi = basis.evaluate(eval_points)  # (J, L, D, D)

        div_cols = tensor_basis_column_divergence(
            Phi, dx=0.1, grid_shape=grid_shape
        )

        assert div_cols.shape == (J, L, D)

    def test_divergence_values_computed(self):
        """Test that divergence values are actually computed."""
        grid_shape = (15, 15)
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=0.2, num_points_per_dim=15
        )
        eval_points = sampler.sample()

        centers = np.array([[0.0, 0.0]])
        basis = TensorBasis(centers, sigma=0.3)

        Phi = basis.evaluate(eval_points)
        div_cols = tensor_basis_column_divergence(
            Phi, dx=0.2, grid_shape=grid_shape
        )

        # Should have some non-trivial values
        assert not np.allclose(div_cols, 0.0)

    def test_grid_shape_mismatch_error(self):
        """Test error when grid_shape doesn't match J."""
        Phi = np.random.randn(100, 2, 2, 2)  # J=100

        with pytest.raises(ValueError, match="grid_shape"):
            tensor_basis_column_divergence(
                Phi, dx=0.1, grid_shape=(5, 5)
            )  # 25 != 100


class TestVerifyTensorBasisDivergenceFree:
    """Tests for verify_tensor_basis_divergence_free function."""

    def test_returns_correct_shape(self):
        """Test that relative_divs has shape (L, D)."""
        grid_shape = (15, 15)
        L = 2
        D = 2

        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=0.2, num_points_per_dim=15
        )
        eval_points = sampler.sample()

        centers = np.array([[0.0, 0.0], [0.5, 0.5]])
        basis = TensorBasis(centers, sigma=0.3)

        Phi = basis.evaluate(eval_points)
        all_free, rel_divs = verify_tensor_basis_divergence_free(
            Phi, dx=0.2, grid_shape=grid_shape, rtol=0.1
        )

        assert rel_divs.shape == (L, D)
        assert isinstance(all_free, (bool, np.bool_))

    def test_tensor_basis_columns_approximately_divergence_free(self):
        """Test that tensor basis columns are approximately divergence-free.

        The operator Ô = -I∇² + ∇∇ᵀ applied to a scalar produces divergence-free
        vector fields. Each column of Φ should be approximately divergence-free.
        """
        # Use finer grid for better numerical accuracy
        grid_shape = (30, 30)
        delta_x = 0.1
        sigma = 0.5

        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=delta_x, num_points_per_dim=30
        )
        eval_points = sampler.sample()

        centers = np.array([[0.0, 0.0], [0.5, 0.0], [0.0, 0.5]])
        basis = TensorBasis(centers, sigma=sigma)

        Phi = basis.evaluate(eval_points)
        all_free, rel_divs = verify_tensor_basis_divergence_free(
            Phi, dx=delta_x, grid_shape=grid_shape, rtol=0.1
        )

        print(f"Relative divergences:\n{rel_divs}")
        print(f"Max relative divergence: {np.max(rel_divs):.4f}")

        # The columns should be approximately divergence-free
        # Allow some tolerance for numerical discretization error
        assert (
            np.max(rel_divs) < 0.5
        ), f"Max relative divergence too high: {np.max(rel_divs)}"


class TestTensorBasisDivergenceFree3D:
    """Test divergence-free property in 3D."""

    def test_3d_tensor_basis_divergence_free(self):
        """Test tensor basis columns are divergence-free in 3D."""
        grid_shape = (10, 10, 10)
        delta_x = 0.2
        sigma = 0.4

        sampler = VectorSampler(
            center=[0.0, 0.0, 0.0], delta_x=delta_x, num_points_per_dim=10
        )
        eval_points = sampler.sample()

        centers = np.array([[0.0, 0.0, 0.0], [0.3, 0.0, 0.0]])
        basis = TensorBasis(centers, sigma=sigma)

        Phi = basis.evaluate(eval_points)

        # Verify shape
        assert Phi.shape == (1000, 2, 3, 3)

        all_free, rel_divs = verify_tensor_basis_divergence_free(
            Phi, dx=delta_x, grid_shape=grid_shape, rtol=0.2
        )

        print(f"3D Relative divergences:\n{rel_divs}")

        # Should be approximately divergence-free
        assert np.max(rel_divs) < 1.0


# Demo example
if __name__ == "__main__":
    print("=" * 60)
    print("TENSOR BASIS DIVERGENCE-FREE VERIFICATION DEMO")
    print("=" * 60)

    # Setup
    grid_shape = (25, 25)
    delta_x = 0.1
    sigma = 0.4

    print("\nParameters:")
    print(
        f"  Grid: {grid_shape[0]}x{grid_shape[1]} = {np.prod(grid_shape)} points"
    )
    print(f"  delta_x = {delta_x}")
    print(f"  sigma = {sigma}")

    # Create evaluation grid
    sampler = VectorSampler(
        center=[0.0, 0.0], delta_x=delta_x, num_points_per_dim=grid_shape[0]
    )
    eval_points = sampler.sample()
    print(f"  Evaluation points shape: {eval_points.shape}")

    # Create tensor basis
    centers = np.array([[0.0, 0.0], [0.5, 0.0], [0.0, 0.5], [-0.5, 0.0]])
    L = len(centers)
    D = 2

    print(f"  Centers: L={L}")

    basis = TensorBasis(centers, sigma=sigma)
    Phi = basis.evaluate(eval_points)
    print(f"  Tensor basis Φ shape: {Phi.shape} (J, L, D, D)")

    # Compute column divergences
    print("\n" + "-" * 60)
    print("COLUMN DIVERGENCE COMPUTATION")
    print("-" * 60)

    div_cols = tensor_basis_column_divergence(
        Phi, dx=delta_x, grid_shape=grid_shape
    )
    print(f"  Column divergence shape: {div_cols.shape} (J, L, D)")

    # Verify divergence-free
    print("\n" + "-" * 60)
    print("DIVERGENCE-FREE VERIFICATION")
    print("-" * 60)

    all_free, rel_divs = verify_tensor_basis_divergence_free(
        Phi, dx=delta_x, grid_shape=grid_shape, rtol=0.1
    )

    print("\nRelative divergence for each (center, column):")
    print(f"  Shape: {rel_divs.shape} (L, D)")
    for center_idx in range(L):
        for d in range(D):
            print(
                f"    Center {center_idx}, Column {d}: {rel_divs[center_idx, d]:.6f}"
            )

    print(f"\nMax relative divergence: {np.max(rel_divs):.6f}")
    print(f"All columns divergence-free (rtol=0.1): {all_free}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
