import os
import warnings
from datetime import datetime

import hydra
import numpy as np
import pandas as pd
from conf.scenario_entra import scenario_entra
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from tqdm import tqdm

from entra import (CovarianceMinimizer, EffectiveCovarianceMinimizer,
                   EffectiveTransformation, TensorBasis, Transformation,
                   VectorSampler, shannon_entropy_gaussian,
                   shannon_entropy_uniform)

# Register dataclass with ConfigStore
configstore = ConfigStore.instance()
configstore.store(name="entra_base", node=scenario_entra)

# Silence numpy warnings during optimization
warnings.filterwarnings("ignore", category=RuntimeWarning)


def run_optimization(eval_points, centers, sigma, cfg: scenario_entra, verbose=True):
    """
    Run full two-stage optimization.

    Stage 1: TensorBasis optimization with LxD parameters
    Stage 2: Outer loop with EffectiveTransformation using L parameters

    Returns dict with final results and full history.
    """

    target_entropy = shannon_entropy_uniform(eval_points)

    max_iter_stage1 = cfg.stage1.max_iterations
    max_iter_outer = cfg.stage2.max_iterations
    n_outer = cfg.stage2.n_outer

    # History tracking (one entry per major round)
    full_history = {
        'round': [],
        'determinant': [],
        'gaussian_entropy': [],
        'gap': [],
    }

    # =========================================================================
    # STAGE 1: TensorBasis optimization
    # =========================================================================
    basis = TensorBasis(centers, sigma=sigma)
    transformation = Transformation(basis)
    minimizer = CovarianceMinimizer(transformation, eval_points)

    x = transformation.get_coefficients_flat().copy()
    n_params = len(x)

    lam = 1.0
    eps = 1e-7
    tol = cfg.stage1.tolerance

    stage1_iter_count = 0
    pbar = tqdm(range(1, max_iter_stage1 + 1), desc=f"Stage 1 (s={sigma})", disable=not verbose)
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
            pbar.set_postfix(det=f"{det_val:.2e}", gap=f"{entropy_val - target_entropy:.4f}")

            if improvement < tol:
                stage1_iter_count = iteration
                pbar.close()
                break
        else:
            lam *= 10.0
    else:
        # Loop completed without convergence
        stage1_iter_count = max_iter_stage1

    transformation.set_coefficients_flat(x)

    # Get results after Stage 1
    stage1_cov = minimizer.compute_covariance()
    stage1_det = np.linalg.det(stage1_cov)
    stage1_entropy = shannon_entropy_gaussian(stage1_cov)
    stage1_points = transformation.transform(eval_points)

    # Record Stage 1 as round 0
    full_history['round'].append(0)
    full_history['determinant'].append(stage1_det)
    full_history['gaussian_entropy'].append(stage1_entropy)
    full_history['gap'].append(stage1_entropy - target_entropy)

    if verbose:
        print(f"  Round 0: det = {stage1_det:.6e}, H = {stage1_entropy:.6f}, gap = {stage1_entropy - target_entropy:.6f}")

    # =========================================================================
    # STAGE 2: Outer loop with EffectiveTransformation
    # =========================================================================
    updated_basis = transformation.get_updated_basis(eval_points)
    current_basis = updated_basis.copy()
    current_points = stage1_points.copy()

    pbar2 = tqdm(range(1, n_outer + 1), desc=f"Stage 2 (s={sigma})", disable=not verbose)
    for outer_round in pbar2:
        eff_transform = EffectiveTransformation(current_basis, current_points)
        eff_minimizer = EffectiveCovarianceMinimizer(eff_transform)

        result = eff_minimizer.optimize(
            max_iterations=max_iter_outer,
            tolerance=cfg.stage2.tolerance,
            verbose=False
        )

        round_det = result['final_determinant']
        round_cov = result['final_covariance']
        round_entropy = shannon_entropy_gaussian(round_cov)

        current_points = eff_transform.transform()
        current_basis = eff_transform.get_updated_basis()

        # Record this round
        full_history['round'].append(outer_round)
        full_history['determinant'].append(round_det)
        full_history['gaussian_entropy'].append(round_entropy)
        full_history['gap'].append(round_entropy - target_entropy)

        pbar2.set_postfix(det=f"{round_det:.2e}", gap=f"{round_entropy - target_entropy:.4f}")

    final_det = full_history['determinant'][-1]
    final_entropy = full_history['gaussian_entropy'][-1]
    final_gap = full_history['gap'][-1]

    if verbose:
        print(f"\n  Final: det = {final_det:.6e}, H(Gaussian) = {final_entropy:.6f}, gap = {final_gap:.6f}")

    return {
        'sigma': sigma,
        'target_entropy': target_entropy,
        'final_det': final_det,
        'final_entropy': final_entropy,
        'gap': final_gap,
        'full_history': full_history,
        'final_points': current_points,
        'stage1_iterations': stage1_iter_count,
    }


def create_centers(eval_points):
    """Create centers for basis functions along axes."""
    center_list = []
    for i in range(int(eval_points[:, 0].max())):
        center_list.append([i, 0.0])
        center_list.append([-i, 0.0])
        center_list.append([0.0, i])
        center_list.append([0.0, -i])
    return np.asarray(center_list)


def run_single(cfg: scenario_entra):
    """Run optimization for a single sigma value."""
    print("=" * 70)
    print("COVARIANCE OPTIMIZATION WITH DIVERGENCE-FREE TRANSFORMATION")
    print("=" * 70)

    D = cfg.sampling.dimension
    sigma = cfg.single.sigma

    print("\nParameters:")
    print(f"  D (dimension)           = {D}")
    print(f"  num_points_per_dim      = {cfg.sampling.num_points_per_dim}")
    print(f"  delta_x                 = {cfg.sampling.delta_x}")
    print(f"  J (total grid points)   = {cfg.sampling.num_points_per_dim**D}")
    print(f"  sigma                   = {sigma:.4f}")

    # Sample points from uniform distribution
    print("\n" + "-" * 70)
    print("STEP 1: Sample points from uniform distribution")
    print("-" * 70)

    sampler = VectorSampler(
        center=list(cfg.sampling.center),
        delta_x=cfg.sampling.delta_x,
        num_points_per_dim=cfg.sampling.num_points_per_dim,
        distribution=cfg.sampling.distribution,
    )

    eval_points = sampler.sample()
    print(f"  Points shape: {eval_points.shape}")
    print(f"  Range: [{eval_points.min():.2f}, {eval_points.max():.2f}]")

    # Initial statistics
    initial_cov = np.cov(eval_points, rowvar=False)
    initial_det = np.linalg.det(initial_cov)
    initial_entropy_uniform = shannon_entropy_uniform(eval_points)

    print(f"  Initial determinant: {initial_det:.6e}")
    print(f"  Entropy (uniform): {initial_entropy_uniform:.6f} nats")

    # Create centers
    print("\n" + "-" * 70)
    print("STEP 2: Create centers for basis functions")
    print("-" * 70)

    centers = create_centers(eval_points)
    print(f"  Centers shape: {centers.shape}")

    # Run optimization
    print("\n" + "-" * 70)
    print("STEP 3: Two-stage optimization")
    print("-" * 70)

    result = run_optimization(
        eval_points, centers, sigma, cfg,
        verbose=cfg.output.verbose
    )

    # Final summary
    print("\n" + "-" * 70)
    print("FINAL SUMMARY")
    print("-" * 70)
    print(f"  Initial det:     {initial_det:.6e}")
    print(f"  Final det:       {result['final_det']:.6e}")
    print(f"  Reduction:       {initial_det / result['final_det']:.2f}x")
    print(f"  Target H:        {initial_entropy_uniform:.6f} nats")
    print(f"  Final H:         {result['final_entropy']:.6f} nats")
    print(f"  Gap:             {result['gap']:.6f} nats")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)

    return result


def run_sigma_sweep(cfg: scenario_entra, output_dir=None):
    """
    Sweep over different sigma values to find the optimal RBF width.
    Each sigma runs the full two-stage optimization (Stage 1 + Outer Loop).
    Saves results to CSV files.
    """
    print("\n" + "=" * 70)
    print("SIGMA PARAMETER SWEEP (Full Two-Stage Optimization)")
    print("=" * 70)

    # Get sweep description if available
    sweep_desc = cfg.sweep.description
    if sweep_desc:
        print(f"\n{sweep_desc}")

    D = cfg.sampling.dimension

    # Create output directory
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Generate points once
    sampler = VectorSampler(
        center=list(cfg.sampling.center),
        delta_x=cfg.sampling.delta_x,
        num_points_per_dim=cfg.sampling.num_points_per_dim,
        distribution=cfg.sampling.distribution,
    )
    eval_points = sampler.sample()

    # Target entropy
    target_entropy = shannon_entropy_uniform(eval_points)
    initial_cov = np.cov(eval_points, rowvar=False)
    initial_det = np.linalg.det(initial_cov)

    print(f"\nTarget H(uniform): {target_entropy:.6f} nats")
    print(f"Initial determinant: {initial_det:.6e}")
    print(f"Points: {eval_points.shape[0]}, Dimensions: {D}")
    print(f"Stage 1 max iterations: {cfg.stage1.max_iterations}")
    print(f"Outer loop: {cfg.stage2.n_outer} rounds x {cfg.stage2.max_iterations} iterations each")
    print(f"Output directory: {output_dir}")

    # Create centers
    centers = create_centers(eval_points)

    # Sigma values to test (from config)
    sigma_values = list(cfg.sweep.sigmas)

    results = []
    all_histories = []

    print(f"\nTesting sigma values: {sigma_values}")
    print("-" * 70)

    for sigma in sigma_values:
        result = run_optimization(
            eval_points.copy(),
            centers,
            sigma,
            cfg,
            verbose=True
        )

        results.append(result)

        # Save individual history CSV
        history_df = pd.DataFrame(result['full_history'])
        history_df['sigma'] = sigma
        history_df['target_entropy'] = target_entropy
        all_histories.append(history_df)

        if cfg.output.save_csv:
            history_file = os.path.join(output_dir, f'history_sigma_{sigma}_{timestamp}.csv')
            history_df.to_csv(history_file, index=False)

    # Combine all histories
    combined_df = pd.concat(all_histories, ignore_index=True)

    if cfg.output.save_csv:
        combined_file = os.path.join(output_dir, f'history_all_sigmas_{timestamp}.csv')
        combined_df.to_csv(combined_file, index=False)
        print(f"\nCombined history saved: {combined_file}")

        # Save summary table
        summary_data = []
        for r in results:
            summary_data.append({
                'sigma': r['sigma'],
                'final_det': r['final_det'],
                'final_entropy': r['final_entropy'],
                'gap': r['gap'],
                'det_reduction': initial_det / r['final_det'],
                'stage1_iterations': r['stage1_iterations'],
                'target_entropy': target_entropy,
                'initial_det': initial_det,
            })

        summary_df = pd.DataFrame(summary_data)
        summary_file = os.path.join(output_dir, f'sigma_sweep_summary_{timestamp}.csv')
        summary_df.to_csv(summary_file, index=False)
        print(f"Summary saved: {summary_file}")

    # Print analysis table
    print("\n" + "=" * 70)
    print("SIGMA SWEEP ANALYSIS TABLE")
    print("=" * 70)
    print(f"\nTarget H(uniform) = {target_entropy:.6f} nats")
    print(f"Initial determinant = {initial_det:.6e}\n")
    print(f"{'Sigma':>8} | {'Final Det':>14} | {'H(Gaussian)':>12} | {'Gap (nats)':>12} | {'Det Reduction':>14}")
    print("-" * 75)

    best_result = None
    best_gap = float('inf')

    for r in results:
        det_reduction = initial_det / r['final_det']
        print(f"{r['sigma']:>8} | {r['final_det']:>14.6e} | {r['final_entropy']:>12.6f} | {r['gap']:>12.6f} | {det_reduction:>14.2f}x")
        if abs(r['gap']) < abs(best_gap):
            best_gap = r['gap']
            best_result = r

    print("-" * 75)
    print(f"\n*** BEST SIGMA = {best_result['sigma']} ***")
    print(f"    Entropy gap:       {best_result['gap']:.6f} nats")
    print(f"    Final determinant: {best_result['final_det']:.6e}")
    print(f"    Det reduction:     {initial_det / best_result['final_det']:.2f}x")

    print("\n" + "=" * 70)
    print("SIGMA SWEEP COMPLETE")
    print("=" * 70)

    return results, best_result


@hydra.main(version_base="1.3", config_path="conf", config_name="scenario_entra")
def main(cfg: scenario_entra):
    """Main entry point with Hydra configuration."""
    print("\nConfiguration:")
    print(OmegaConf.to_yaml(cfg))

    if cfg.sweep.enabled:
        run_sigma_sweep(cfg)
    else:
        run_single(cfg)


if __name__ == "__main__":
    main()
