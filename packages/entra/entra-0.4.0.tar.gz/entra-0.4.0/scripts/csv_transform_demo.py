"""
CSV Transform Demo with Hydra Configuration

Transforms CSV data towards Gaussian distribution using entropy-conserving
divergence-free vector fields. Includes visualization at each optimization stage.

Usage:
    python csv_transform_demo.py                           # Generate synthetic 2D data
    python csv_transform_demo.py data.csv_path=/path/to/data.csv  # Use existing CSV
    python csv_transform_demo.py data.dimension=3          # Generate synthetic 3D data
"""

import os
import warnings

import hydra
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from conf.scenario_csv_transform import scenario_csv_transform
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from tqdm import tqdm

from entra import (CovarianceMinimizer, EffectiveCovarianceMinimizer,
                   EffectiveTransformation, TensorBasis, Transformation,
                   VectorSampler, shannon_entropy_gaussian,
                   shannon_entropy_uniform)

matplotlib.use("Agg")
# Register dataclass with ConfigStore
configstore = ConfigStore.instance()
configstore.store(name="csv_transform_base", node=scenario_csv_transform)

# Silence numpy warnings during optimization
warnings.filterwarnings("ignore", category=RuntimeWarning)


def generate_synthetic_data(dimension: int, num_points_per_dim: int) -> pd.DataFrame:
    """Generate synthetic uniform distribution data using VectorSampler."""
    center = [0.0] * dimension
    sampler = VectorSampler(
        center=center,
        delta_x=1.0,
        num_points_per_dim=num_points_per_dim,
        distribution="uniform",
    )
    points = sampler.sample()

    if dimension == 2:
        return pd.DataFrame({"x": points[:, 0], "y": points[:, 1]})
    elif dimension == 3:
        return pd.DataFrame({"x": points[:, 0], "y": points[:, 1], "z": points[:, 2]})
    else:
        raise ValueError(f"Dimension must be 2 or 3, got {dimension}")


def create_centers(points: np.ndarray) -> np.ndarray:
    """Create centers for basis functions along axes."""
    D = points.shape[1]
    max_coord = int(np.max(np.abs(points)))

    center_list = []
    for i in range(max_coord):
        for d in range(D):
            c_pos = [0.0] * D
            c_pos[d] = float(i)
            center_list.append(c_pos)
            c_neg = [0.0] * D
            c_neg[d] = float(-i)
            center_list.append(c_neg)

    return np.asarray(center_list)


def plot_distribution(
    points: np.ndarray, title: str, output_path: str, target_entropy: float = None
):
    """Plot 2D or 3D point distribution."""
    D = points.shape[1]

    if D == 2:
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # Scatter plot
        axes[0].scatter(points[:, 0], points[:, 1], alpha=0.5, s=10)
        axes[0].set_xlabel("x")
        axes[0].set_ylabel("y")
        axes[0].set_title(f"{title} - Scatter")
        axes[0].set_aspect("equal")
        axes[0].grid(True, alpha=0.3)

        # X histogram
        axes[1].hist(points[:, 0], bins=30, alpha=0.7, edgecolor="black")
        axes[1].set_xlabel("x")
        axes[1].set_ylabel("Count")
        axes[1].set_title("X Distribution")
        axes[1].grid(True, alpha=0.3)

        # Y histogram
        axes[2].hist(points[:, 1], bins=30, alpha=0.7, edgecolor="black")
        axes[2].set_xlabel("y")
        axes[2].set_ylabel("Count")
        axes[2].set_title("Y Distribution")
        axes[2].grid(True, alpha=0.3)

    elif D == 3:
        fig = plt.figure(figsize=(16, 4))

        # 3D scatter
        ax0 = fig.add_subplot(1, 4, 1, projection="3d")
        ax0.scatter(points[:, 0], points[:, 1], points[:, 2], alpha=0.3, s=5)
        ax0.set_xlabel("x")
        ax0.set_ylabel("y")
        ax0.set_zlabel("z")
        ax0.set_title(f"{title} - 3D Scatter")

        # Histograms
        for i, (col, label) in enumerate([(0, "X"), (1, "Y"), (2, "Z")]):
            ax = fig.add_subplot(1, 4, i + 2)
            ax.hist(points[:, col], bins=30, alpha=0.7, edgecolor="black")
            ax.set_xlabel(label.lower())
            ax.set_ylabel("Count")
            ax.set_title(f"{label} Distribution")
            ax.grid(True, alpha=0.3)

    # Add entropy info
    cov = np.cov(points, rowvar=False)
    det = np.linalg.det(cov)
    entropy = shannon_entropy_gaussian(cov)

    info_text = f"Det: {det:.2e}, H(Gaussian): {entropy:.4f}"
    if target_entropy is not None:
        gap = entropy - target_entropy
        info_text += f", Gap: {gap:+.4f}"

    fig.suptitle(f"{title}\n{info_text}", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def run_transformation(
    points: np.ndarray, cfg: scenario_csv_transform, output_dir: str
):
    """
    Run full two-stage transformation with plotting at each stage.

    Returns transformed points and history.
    """
    D = points.shape[1]
    target_entropy = shannon_entropy_uniform(points)

    print(f"\nTarget H(uniform): {target_entropy:.6f} nats")
    print(f"Points: {points.shape[0]}, Dimensions: {D}")

    # Create centers
    centers = create_centers(points)
    print(f"Basis centers: {centers.shape[0]}")

    sigma = cfg.transform.sigma
    print(f"Sigma: {sigma}")

    # Plot initial distribution
    if cfg.output.save_plots:
        plot_distribution(
            points,
            "Round 0 (Initial)",
            os.path.join(output_dir, "round_00_initial.png"),
            target_entropy,
        )

    # =========================================================================
    # STAGE 1: TensorBasis optimization
    # =========================================================================
    print("\n" + "-" * 70)
    print("STAGE 1: TensorBasis Optimization")
    print("-" * 70)

    basis = TensorBasis(centers, sigma=sigma)
    transformation = Transformation(basis)
    minimizer = CovarianceMinimizer(transformation, points)

    x = transformation.get_coefficients_flat().copy()
    n_params = len(x)

    lam = 1.0
    eps = 1e-7
    tol = cfg.transform.stage1_tolerance
    max_iter = cfg.transform.stage1_max_iterations

    pbar = tqdm(range(1, max_iter + 1), desc="Stage 1")
    for iteration in pbar:
        r = minimizer.residuals_for_lm(x)

        J_mat = np.zeros((len(r), n_params))
        for i in range(n_params):
            x_plus = x.copy()
            x_plus[i] += eps
            J_mat[:, i] = (minimizer.residuals_for_lm(x_plus) - r) / eps

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
            entropy_val = shannon_entropy_gaussian(cov)
            pbar.set_postfix(
                det=f"{det_val:.2e}", gap=f"{entropy_val - target_entropy:.4f}"
            )

            if improvement < tol:
                pbar.close()
                break
        else:
            lam *= 10.0

    transformation.set_coefficients_flat(x)
    stage1_points = transformation.transform(points)

    # Plot after Stage 1
    if cfg.output.save_plots:
        plot_distribution(
            stage1_points,
            "Round 1 (After Stage 1)",
            os.path.join(output_dir, "round_01_stage1.png"),
            target_entropy,
        )

    # =========================================================================
    # STAGE 2: Outer loop with EffectiveTransformation
    # =========================================================================
    print("\n" + "-" * 70)
    print("STAGE 2: Outer Loop Refinement")
    print("-" * 70)

    updated_basis = transformation.get_updated_basis(points)
    current_basis = updated_basis.copy()
    current_points = stage1_points.copy()

    n_outer = cfg.transform.stage2_n_outer
    max_iter_outer = cfg.transform.stage2_max_iterations
    tol_outer = cfg.transform.stage2_tolerance

    history = {
        "round": [0, 1],
        "determinant": [
            np.linalg.det(np.cov(points, rowvar=False)),
            np.linalg.det(np.cov(stage1_points, rowvar=False)),
        ],
        "gaussian_entropy": [
            shannon_entropy_gaussian(np.cov(points, rowvar=False)),
            shannon_entropy_gaussian(np.cov(stage1_points, rowvar=False)),
        ],
    }

    for outer_round in tqdm(range(1, n_outer + 1), desc="Stage 2"):
        eff_transform = EffectiveTransformation(current_basis, current_points)
        eff_minimizer = EffectiveCovarianceMinimizer(eff_transform)

        eff_minimizer.optimize(
            max_iterations=max_iter_outer, tolerance=tol_outer, verbose=False
        )

        current_points = eff_transform.transform()
        current_basis = eff_transform.get_updated_basis()

        # Record history
        round_cov = np.cov(current_points, rowvar=False)
        round_det = np.linalg.det(round_cov)
        round_entropy = shannon_entropy_gaussian(round_cov)

        history["round"].append(outer_round + 1)
        history["determinant"].append(round_det)
        history["gaussian_entropy"].append(round_entropy)

        # Plot after each outer round
        if cfg.output.save_plots:
            plot_distribution(
                current_points,
                f"Round {outer_round + 1} (Outer Loop {outer_round})",
                os.path.join(
                    output_dir, f"round_{outer_round + 1:02d}_outer{outer_round}.png"
                ),
                target_entropy,
            )

    # Final summary
    final_cov = np.cov(current_points, rowvar=False)
    final_det = np.linalg.det(final_cov)
    final_entropy = shannon_entropy_gaussian(final_cov)
    final_gap = final_entropy - target_entropy

    print("\n" + "=" * 70)
    print("TRANSFORMATION COMPLETE")
    print("=" * 70)
    print(f"  Target H(uniform):  {target_entropy:.6f} nats")
    print(f"  Final H(Gaussian):  {final_entropy:.6f} nats")
    print(f"  Gap:                {final_gap:+.6f} nats")
    print(f"  Final determinant:  {final_det:.6e}")

    return current_points, history


def plot_optimization_history(history: dict, target_entropy: float, output_path: str):
    """Plot optimization history across rounds."""
    rounds = history["round"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].semilogy(rounds, history["determinant"], "b.-", markersize=10, linewidth=2)
    axes[0].set_xlabel("Round")
    axes[0].set_ylabel("Determinant")
    axes[0].set_title("Covariance Determinant vs Round")
    axes[0].set_xticks(rounds)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(rounds, history["gaussian_entropy"], "b.-", markersize=10, linewidth=2)
    axes[1].axhline(
        target_entropy,
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Target H(uniform)={target_entropy:.4f}",
    )
    axes[1].set_xlabel("Round")
    axes[1].set_ylabel("H(Gaussian) [nats]")
    axes[1].set_title("Gaussian Entropy vs Round")
    axes[1].set_xticks(rounds)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.suptitle("Optimization Progress", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


@hydra.main(
    version_base="1.3", config_path="conf", config_name="scenario_csv_transform"
)
def main(cfg: scenario_csv_transform):
    """Main entry point with Hydra configuration."""
    print("=" * 70)
    print("CSV TRANSFORM DEMO")
    print("=" * 70)

    print("\nConfiguration:")
    print(OmegaConf.to_yaml(cfg))

    # Create output directory
    output_dir = cfg.output.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Load or generate data
    if cfg.data.csv_path is not None:
        print(f"\nLoading data from: {cfg.data.csv_path}")
        df = pd.read_csv(cfg.data.csv_path)

        # Determine columns based on dimension
        if cfg.data.dimension == 3:
            if all(col in df.columns for col in ["x", "y", "z"]):
                columns = ["x", "y", "z"]
            else:
                raise ValueError("CSV must have x, y, z columns for 3D data")
        else:
            if all(col in df.columns for col in ["x", "y"]):
                columns = ["x", "y"]
            else:
                raise ValueError("CSV must have x, y columns for 2D data")

        points = df[columns].values.astype(np.float64)
    else:
        print(f"\nGenerating synthetic {cfg.data.dimension}D data...")
        df = generate_synthetic_data(cfg.data.dimension, cfg.data.num_points_per_dim)
        columns = ["x", "y", "z"] if cfg.data.dimension == 3 else ["x", "y"]
        points = df[columns].values.astype(np.float64)

        # Save generated data
        input_path = os.path.join(output_dir, "input_data.csv")
        df.to_csv(input_path, index=False)
        print(f"  Saved input data: {input_path}")

    print(f"  Shape: {points.shape}")
    print(f"  Columns: {columns}")

    # Run transformation
    transformed_points, history = run_transformation(points, cfg, output_dir)

    # Save transformed data
    if cfg.output.save_csv:
        df_transformed = df.copy()
        df_transformed[columns] = transformed_points
        output_path = os.path.join(output_dir, "transformed_data.csv")
        df_transformed.to_csv(output_path, index=False)
        print(f"\n  Saved transformed data: {output_path}")

    # Plot optimization history
    if cfg.output.save_plots:
        target_entropy = shannon_entropy_uniform(points)
        plot_optimization_history(
            history,
            target_entropy,
            os.path.join(output_dir, "csv_optimization_history.png"),
        )

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
