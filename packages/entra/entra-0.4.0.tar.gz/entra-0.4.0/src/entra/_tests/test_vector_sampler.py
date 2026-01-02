"""Minimal unit tests for VectorSampler class."""

import numpy as np

from entra import VectorSampler


class TestVectorSampler:
    """Tests for VectorSampler."""

    def test_2d_grid_shape(self):
        """Test that 2D grid has correct shape."""
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=0.5, num_points_per_dim=5
        )
        points = sampler.sample()
        # 5x5 grid = 25 points, 2D
        assert points.shape == (25, 2)
        assert sampler.J == 25
        assert sampler.D == 2

    def test_3d_grid_shape(self):
        """Test that 3D grid has correct shape."""
        sampler = VectorSampler(
            center=[0.0, 0.0, 0.0], delta_x=1.0, num_points_per_dim=3
        )
        points = sampler.sample()
        # 3x3x3 grid = 27 points, 3D
        assert points.shape == (27, 3)
        assert sampler.J == 27
        assert sampler.D == 3

    def test_anisotropic_grid(self):
        """Test grid with different points per dimension."""
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=[0.5, 1.0], num_points_per_dim=(4, 3)
        )
        points = sampler.sample()
        # 4x3 grid = 12 points
        assert points.shape == (12, 2)
        assert sampler.num_points_per_dim == (4, 3)

    def test_grid_centered_at_origin(self):
        """Test that grid is centered at specified center."""
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=1.0, num_points_per_dim=3
        )
        points = sampler.sample()
        # 3x3 grid centered at origin with spacing 1.0
        # Should have points at: (-1,-1), (-1,0), (-1,1), (0,-1), (0,0), (0,1), (1,-1), (1,0), (1,1)
        assert np.allclose(points.mean(axis=0), [0.0, 0.0])

    def test_grid_centered_at_nonzero(self):
        """Test grid centered at non-zero point."""
        sampler = VectorSampler(
            center=[5.0, 10.0], delta_x=1.0, num_points_per_dim=3
        )
        points = sampler.sample()
        assert np.allclose(points.mean(axis=0), [5.0, 10.0])

    def test_grid_spacing(self):
        """Test that grid points have correct spacing."""
        delta_x = 0.5
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=delta_x, num_points_per_dim=5
        )
        points = sampler.sample()

        # Check spacing in x direction (first 5 points have same y)
        x_vals = np.unique(points[:, 0])
        x_diffs = np.diff(x_vals)
        assert np.allclose(x_diffs, delta_x)

    def test_points_ordered(self):
        """Test that points are ordered (increasing x, then y)."""
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=1.0, num_points_per_dim=3
        )
        points = sampler.sample()

        # First dimension should increase first (row-major order with indexing='ij')
        # Points should be: (-1,-1), (-1,0), (-1,1), (0,-1), (0,0), (0,1), (1,-1), (1,0), (1,1)
        expected_x = np.array([-1, -1, -1, 0, 0, 0, 1, 1, 1])
        expected_y = np.array([-1, 0, 1, -1, 0, 1, -1, 0, 1])

        assert np.allclose(points[:, 0], expected_x)
        assert np.allclose(points[:, 1], expected_y)

    def test_gaussian_weights(self):
        """Test Gaussian weights computation."""
        sampler = VectorSampler(
            center=[0.0, 0.0],
            delta_x=1.0,
            num_points_per_dim=3,
            distribution="gaussian",
            sigma=1.0,
        )
        weights = sampler.get_weights()

        # Weight at center should be 1.0
        center_idx = 4  # middle of 3x3 grid
        assert np.isclose(weights[center_idx], 1.0)

        # Weights should decrease away from center
        assert weights[center_idx] > weights[0]

    def test_uniform_weights(self):
        """Test uniform weights are all ones."""
        sampler = VectorSampler(
            center=[0.0, 0.0],
            delta_x=1.0,
            num_points_per_dim=3,
            distribution="uniform",
        )
        weights = sampler.get_weights()

        assert np.allclose(weights, 1.0)

    def test_extent(self):
        """Test get_extent returns correct bounds."""
        sampler = VectorSampler(
            center=[0.0, 0.0], delta_x=1.0, num_points_per_dim=5
        )
        extent = sampler.get_extent()

        # 5 points centered at 0 with spacing 1: [-2, -1, 0, 1, 2]
        assert np.allclose(extent[0], [-2.0, 2.0])
        assert np.allclose(extent[1], [-2.0, 2.0])


# Minimal example
if __name__ == "__main__":
    print("=== VectorSampler Minimal Example ===\n")

    # 2D Gaussian grid
    print("--- 2D Gaussian Grid ---")
    sampler = VectorSampler(
        center=[0.0, 0.0],
        delta_x=0.5,
        num_points_per_dim=5,
        distribution="gaussian",
        sigma=1.0,
    )

    print(f"Sampler: {sampler}")
    points = sampler.sample()
    print(f"Grid points shape: {points.shape}  (J, D)")
    print(f"First 5 points:\n{points[:5]}")

    weights = sampler.get_weights()
    print(f"\nWeights shape: {weights.shape}")
    print(f"Weight at center: {weights[12]:.4f}")  # center of 5x5 grid

    extent = sampler.get_extent()
    print(
        f"\nExtent: x=[{extent[0,0]}, {extent[0,1]}], y=[{extent[1,0]}, {extent[1,1]}]"
    )

    # 3D grid
    print("\n--- 3D Grid ---")
    sampler3d = VectorSampler(
        center=[0.0, 0.0, 0.0],
        delta_x=[0.5, 0.5, 1.0],
        num_points_per_dim=(3, 3, 2),
    )
    print(f"Sampler: {sampler3d}")
    print(f"J = {sampler3d.J} points")
