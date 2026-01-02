"""Minimal unit tests for TensorBasis class."""

import numpy as np

from entra import TensorBasis


class TestTensorBasis:
    """Tests for TensorBasis."""

    def test_evaluate_single_point_shape(self):
        """Test evaluation at a single point returns correct shape."""
        centers = np.array([[0, 0], [1, 0], [0, 1]])  # L=3, D=2
        basis = TensorBasis(centers, sigma=1.0)

        x = np.array([0.5, 0.5])
        result = basis.evaluate(x)

        assert result.shape == (3, 2, 2)  # (L, D, D)

    def test_evaluate_multiple_points_shape(self):
        """Test evaluation at multiple points returns correct shape."""
        centers = np.array([[0, 0, 0], [1, 0, 0]])  # L=2, D=3
        basis = TensorBasis(centers, sigma=0.5)

        x = np.array(
            [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.0, 1.0, 1.0]]
        )  # J=3 eval points
        result = basis.evaluate(x)

        assert result.shape == (3, 2, 3, 3)  # (J, L, D, D)

    def test_result_is_symmetric(self):
        """Test that each resulting matrix is symmetric."""
        centers = np.array([[0, 0], [1, 1]])  # L=2, D=2
        basis = TensorBasis(centers, sigma=0.7)

        x = np.array([0.3, 0.7])
        result = basis.evaluate(x)  # (L, D, D)

        for idx in range(basis.L):
            matrix = result[idx]
            np.testing.assert_array_almost_equal(matrix, matrix.T)

    def test_at_center_identity_term_dominates(self):
        """Test behavior at center where diff=0, outer product vanishes."""
        centers = np.array([[0.0, 0.0, 0.0]])  # L=1, D=3
        sigma = 1.0
        basis = TensorBasis(centers, sigma=sigma)

        # At the center, diff=0, so:
        # Φ = (D-1)/σ² * I * 1 + 0
        x = np.array([0.0, 0.0, 0.0])
        result = basis.evaluate(x)  # (L, D, D) = (1, 3, 3)

        D = 3
        expected_coeff = (D - 1) / sigma**2
        expected = expected_coeff * np.eye(D)

        np.testing.assert_array_almost_equal(result[0], expected)

    def test_scalar_evaluation(self):
        """Test that evaluate_scalar returns Gaussian values."""
        centers = np.array([[0.0, 0.0]])  # L=1, D=2
        sigma = 1.0
        basis = TensorBasis(centers, sigma=sigma)

        x = np.array([1.0, 0.0])
        phi = basis.evaluate_scalar(x)

        expected = np.exp(-1.0 / (2 * sigma**2))
        np.testing.assert_almost_equal(phi[0], expected)

    def test_center_vector_computed(self):
        """Test that center_vector is mean of centers."""
        centers = np.array([[0.0, 0.0], [2.0, 4.0]])  # L=2, D=2
        basis = TensorBasis(centers, sigma=1.0)

        np.testing.assert_array_almost_equal(basis.center_vector, [1.0, 2.0])

    def test_L_and_D_attributes(self):
        """Test L and D attributes."""
        centers = np.array(
            [[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]]
        )  # L=4, D=3
        basis = TensorBasis(centers, sigma=0.5)

        assert basis.L == 4
        assert basis.D == 3
        assert len(basis) == 4


# Minimal example
if __name__ == "__main__":
    from entra import VectorSampler

    print("=== TensorBasis Minimal Example ===\n")

    # Create evaluation grid
    sampler = VectorSampler(
        center=[0.0, 0.0], delta_x=0.5, num_points_per_dim=5
    )
    eval_points = sampler.sample()  # J=25 points
    print(f"Evaluation points: {eval_points.shape}  (J, D)")

    # L=3 centers
    centers = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    sigma = 0.7 * 0.5  # 0.7 * delta_x

    basis = TensorBasis(centers, sigma=sigma)
    print(f"Basis: {basis}")
    print(f"L={basis.L}, D={basis.D}")

    # Evaluate: (J, L, D, D) output
    Phi = basis.evaluate(eval_points)
    print(f"\nOutput shape: {Phi.shape}  (J, L, D, D)")

    # Verify symmetry
    is_symmetric = np.allclose(Phi, np.swapaxes(Phi, -1, -2))
    print(f"All matrices symmetric: {is_symmetric}")
