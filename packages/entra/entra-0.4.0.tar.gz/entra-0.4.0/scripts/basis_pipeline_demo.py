"""
Divergence-Free Tensor Basis Demo

Demonstrates the full pipeline:
1. Sample J points on a regular grid
2. Create tensor basis with L centers
3. Extract column vector fields
4. Verify divergence-free property via symmetric cancellation
"""

import sys

sys.path.insert(0, "/home/debian/python_workspace/entra/src")

import numpy as np  # noqa: E402

from entra import (  # noqa: E402
    TensorBasis,
    VectorSampler,
    verify_divergence_free_symmetric,
)


def main():
    print("=" * 60)
    print("DIVERGENCE-FREE TENSOR BASIS DEMO")
    print("=" * 60)

    # Parameters
    D = 2
    num_points_per_dim = 50
    delta_x = 0.02
    sigma = 0.7 * delta_x

    print("\nParameters:")
    print(f"  D (dimension)           = {D}")
    print(f"  num_points_per_dim      = {num_points_per_dim}")
    print(f"  delta_x                 = {delta_x}")
    print(f"  J (total grid points)   = {num_points_per_dim**D}")
    print(f"  sigma                   = {sigma:.4f}")

    # Step 1: Create evaluation grid
    print("\n" + "-" * 60)
    print("STEP 1: Create evaluation grid")
    print("-" * 60)

    sampler = VectorSampler(
        center=[0.0, 0.0],
        delta_x=delta_x,
        num_points_per_dim=num_points_per_dim,
        distribution="uniform",
    )

    eval_points = sampler.sample()
    grid_shape = sampler.num_points_per_dim

    print(f"  eval_points shape: {eval_points.shape}  (J, D)")
    print(
        f"  Grid extent: x=[{eval_points[:, 0].min():.2f}, {eval_points[:, 0].max():.2f}]"
    )

    # Step 2: Create tensor basis with L=1 center at origin
    print("\n" + "-" * 60)
    print("STEP 2: Create TensorBasis with center at origin")
    print("-" * 60)

    centers = np.array([[0.0, 0.0]])
    tensor_basis = TensorBasis(centers, sigma=sigma)

    print(f"  Centers: {centers}")
    print(f"  TensorBasis: L={tensor_basis.L}, D={tensor_basis.D}")

    # Step 3: Evaluate and extract columns
    print("\n" + "-" * 60)
    print("STEP 3: Evaluate tensor basis and extract columns")
    print("-" * 60)

    Phi = tensor_basis.evaluate(eval_points)[:, 0, :, :]  # (J, D, D)
    V0 = Phi[:, :, 0]  # Column 0
    V1 = Phi[:, :, 1]  # Column 1

    print(f"  Phi shape: {Phi.shape}  (J, D, D)")
    print(f"  V0 shape: {V0.shape}  (J, D) - Column 0")
    print(f"  V1 shape: {V1.shape}  (J, D) - Column 1")

    # Step 4: Verify divergence-free via symmetric cancellation
    print("\n" + "-" * 60)
    print("STEP 4: Verify divergence-free (symmetric cancellation)")
    print("-" * 60)

    for name, V in [("V0", V0), ("V1", V1)]:
        is_free, stats = verify_divergence_free_symmetric(
            V, dx=delta_x, grid_shape=grid_shape
        )
        print(f"\n  {name}:")
        print(f"    Positive sum:  {stats['positive_sum']:+.6e}")
        print(f"    Negative sum:  {stats['negative_sum']:+.6e}")
        print(f"    Total sum:     {stats['total_sum']:+.6e}")
        print(f"    Cancellation:  {stats['cancellation_ratio']:.2%}")
        print(f"    Divergence-free: {is_free}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
