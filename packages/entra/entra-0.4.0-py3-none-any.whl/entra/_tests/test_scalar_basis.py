"""Minimal unit tests for ScalarBasis class."""

import numpy as np

from entra import ScalarBasis


class TestScalarBasis:
    """Tests for ScalarBasis."""

    def test_evaluate_single_point_shape(self):
        """Test evaluation at a single point returns correct shape."""
        centers = np.array([[0, 0], [1, 0], [0, 1]])  # L=3, D=2
        basis = ScalarBasis(centers, delta_x=1.0)

        x = np.array([0.5, 0.5])
        values = basis.evaluate(x)

        assert values.shape == (3,)  # (L,)

    def test_evaluate_multiple_points_shape(self):
        """Test evaluation at multiple points returns correct shape."""
        centers = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])  # L=4, D=2
        basis = ScalarBasis(centers, delta_x=1.0)

        x = np.array([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]])  # J=3 eval points
        values = basis.evaluate(x)

        assert values.shape == (3, 4)  # (J, L)

    def test_basis_value_at_center_is_one(self):
        """Test that φ_l(c_l) = 1 (value at own center is 1)."""
        centers = np.array([[0, 0], [2, 0], [0, 2]])  # L=3
        basis = ScalarBasis(centers, delta_x=1.0)

        for idx in range(basis.L):
            values = basis.evaluate(centers[idx])
            np.testing.assert_almost_equal(values[idx], 1.0)

    def test_basis_decays_with_distance(self):
        """Test that basis function decays as we move away from center."""
        center = np.array([[0.0, 0.0]])  # L=1
        basis = ScalarBasis(center, delta_x=1.0)

        val_at_center = basis.evaluate(np.array([0.0, 0.0]))[0]
        val_near = basis.evaluate(np.array([0.5, 0.0]))[0]
        val_far = basis.evaluate(np.array([2.0, 0.0]))[0]

        assert val_at_center > val_near > val_far

    def test_sigma_computation(self):
        """Test that sigma = 0.7 * delta_x."""
        centers = np.array([[0, 0, 0]])  # L=1, D=3
        delta_x = [1.0, 2.0, 0.5]
        basis = ScalarBasis(centers, delta_x=delta_x, sigma_factor=0.7)

        expected_sigma = 0.7 * np.array(delta_x)
        np.testing.assert_array_almost_equal(basis.sigma, expected_sigma)

    def test_anisotropic_spacing(self):
        """Test with different spacing per dimension."""
        centers = np.array([[0, 0]])  # L=1, D=2
        delta_x = [1.0, 2.0]
        basis = ScalarBasis(centers, delta_x=delta_x)

        val_x = basis.evaluate(np.array([1.0, 0.0]))[0]
        val_y = basis.evaluate(np.array([0.0, 1.0]))[0]

        # Smaller sigma in x -> faster decay in x direction
        assert val_x < val_y

    def test_center_vector_computed_from_centers(self):
        """Test that center_vector is mean of input centers."""
        centers = np.array(
            [[0.0, 0.0], [2.0, 0.0], [0.0, 2.0], [2.0, 2.0]]
        )  # L=4, D=2
        basis = ScalarBasis(centers, delta_x=1.0)

        expected_center = np.array([1.0, 1.0])
        np.testing.assert_array_almost_equal(
            basis.center_vector, expected_center
        )

    def test_L_and_D_attributes(self):
        """Test that L and D are correctly set."""
        centers = np.array(
            [[0, 0], [1, 0], [0, 1], [1, 1], [0.5, 0.5]]
        )  # L=5, D=2
        basis = ScalarBasis(centers, delta_x=0.5)

        assert basis.L == 5
        assert basis.D == 2
        assert len(basis) == 5

    def test_gradient_shape(self):
        """Test gradient computation returns correct shape."""
        centers = np.array([[0, 0], [1, 1]])  # L=2, D=2
        basis = ScalarBasis(centers, delta_x=1.0)

        grad = basis.evaluate_gradient(np.array([0.5, 0.5]))
        assert grad.shape == (2, 2)  # (L, D)

        x = np.array([[0.0, 0.0], [0.5, 0.5]])  # J=2 eval points
        grad = basis.evaluate_gradient(x)
        assert grad.shape == (2, 2, 2)  # (J, L, D)

    def test_gradient_zero_at_center(self):
        """Test that gradient is zero at the center of a basis function."""
        center = np.array([[0.0, 0.0]])  # L=1, D=2
        basis = ScalarBasis(center, delta_x=1.0)

        grad = basis.evaluate_gradient(np.array([0.0, 0.0]))
        np.testing.assert_array_almost_equal(grad[0], [0.0, 0.0])


# Minimal example
if __name__ == "__main__":
    from entra import VectorSampler

    print("=== ScalarBasis Minimal Example ===\n")

    # Create evaluation grid using VectorSampler
    sampler = VectorSampler(
        center=[0.0, 0.0], delta_x=0.5, num_points_per_dim=5
    )
    eval_points = sampler.sample()  # J=25 points
    print(f"Evaluation points: {eval_points.shape}  (J, D)")

    # L=4 centers
    centers = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    basis = ScalarBasis(centers, delta_x=[0.5, 0.5])
    print(f"Basis: {basis}")
    print(f"L={basis.L}, D={basis.D}")

    # Evaluate: (J, L) output
    values = basis.evaluate(eval_points)
    print(f"\nOutput shape: {values.shape}  (J, L)")
    print(f"J={eval_points.shape[0]} eval points, L={basis.L} centers")
