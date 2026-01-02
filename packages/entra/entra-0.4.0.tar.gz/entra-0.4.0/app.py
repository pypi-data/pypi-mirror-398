"""
Gradio App for Entropy-Conserving Transformations

This app demonstrates how divergence-free vector fields can transform
arbitrary distributions towards Gaussian form while conserving entropy.
"""

import gradio as gr
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from entra import DataFrameTransformer, VectorSampler

matplotlib.use("Agg")


def generate_uniform_data(n_per_dim: int = 20, dimensions: int = 2) -> pd.DataFrame:
    """Generate uniform grid data using VectorSampler."""
    if dimensions == 2:
        center = [0.0, 0.0]
    else:  # 3D
        center = [0.0, 0.0, 0.0]

    sampler = VectorSampler(
        center=center,
        delta_x=1,
        num_points_per_dim=n_per_dim,
        distribution="uniform",
    )
    points = sampler.sample()

    if dimensions == 2:
        df = pd.DataFrame({"x": points[:, 0], "y": points[:, 1]})
    else:
        df = pd.DataFrame({"x": points[:, 0], "y": points[:, 1], "z": points[:, 2]})

    return df


def generate_sample_csv(n_per_dim: int, dimensions: int):
    """Generate sample CSV and return as downloadable file."""
    df = generate_uniform_data(n_per_dim, dimensions)

    # Save to temp file for download
    temp_path = "/tmp/generated_uniform_data.csv"
    df.to_csv(temp_path, index=False)

    n_points = len(df)
    cols = list(df.columns)
    preview = df.head(10).to_string()

    return (
        temp_path,
        f"Generated {n_points} points with columns: {cols}\n\nPreview:\n{preview}",
        df,
    )


def load_csv_file(file):
    """Load uploaded CSV file."""
    if file is None:
        return None, "No file uploaded", None

    df = pd.read_csv(file.name)
    n_points = len(df)
    cols = list(df.columns)
    preview = df.head(10).to_string()

    return (
        file.name,
        f"Loaded {n_points} points with columns: {cols}\n\nPreview:\n{preview}",
        df,
    )


def run_transformation(
    df_state,
    columns_str: str,
    sigma: float,
    max_iterations: int,
    progress=gr.Progress(),
):
    """Run the LM optimization and return results."""
    if df_state is None:
        return (
            None,
            None,
            None,
            "Error: No data loaded. Please upload or generate data first.",
        )

    df = df_state

    # Parse columns
    columns = [c.strip() for c in columns_str.split(",")]

    # Validate columns exist
    missing = [c for c in columns if c not in df.columns]
    if missing:
        return (
            None,
            None,
            None,
            f"Error: Columns not found: {missing}. Available: {list(df.columns)}",
        )

    # Progress callback for the transformer
    def progress_callback(iteration, max_iter, det_val, entropy_val):
        progress(
            iteration / max_iter,
            desc=f"Iter {iteration}/{max_iter} | Det: {det_val:.2e} | H: {entropy_val:.4f}",
        )

    # Create transformer with progress callback
    transformer = DataFrameTransformer(
        sigma=sigma,
        max_iterations=max_iterations,
        verbose=False,
        progress_callback=progress_callback,
    )

    # Run transformation
    df_transformed = transformer.fit_transform(df, columns=columns)

    # Get entropy comparison
    entropy = transformer.get_entropy_comparison(df, df_transformed)
    target_entropy = entropy["original"]["uniform_entropy"]

    # Create plots
    fig_scatter = create_scatter_plot(df, df_transformed, columns)
    fig_hist = create_histogram_plot(df, df_transformed, columns)
    fig_history = create_history_plot(transformer.history_, target_entropy=target_entropy)

    # Create results text
    results_text = format_results(entropy, transformer.history_)

    return fig_scatter, fig_hist, fig_history, results_text


def create_scatter_plot(df_orig, df_trans, columns):
    """Create before/after scatter plot."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    if len(columns) >= 2:
        x_col, y_col = columns[0], columns[1]

        axes[0].scatter(df_orig[x_col], df_orig[y_col], c="blue", alpha=0.5, s=10)
        axes[0].set_xlabel(x_col)
        axes[0].set_ylabel(y_col)
        axes[0].set_title("Original Distribution")
        axes[0].set_aspect("equal")
        axes[0].grid(True, alpha=0.3)

        axes[1].scatter(df_trans[x_col], df_trans[y_col], c="red", alpha=0.5, s=10)
        axes[1].set_xlabel(x_col)
        axes[1].set_ylabel(y_col)
        axes[1].set_title("Transformed (Towards Gaussian)")
        axes[1].set_aspect("equal")
        axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_histogram_plot(df_orig, df_trans, columns):
    """Create marginal histogram plots."""
    n_cols = min(len(columns), 3)
    fig, axes = plt.subplots(n_cols, 2, figsize=(12, 4 * n_cols))

    if n_cols == 1:
        axes = axes.reshape(1, -1)

    for i, col in enumerate(columns[:n_cols]):
        # Original
        axes[i, 0].hist(df_orig[col], bins=30, density=True, alpha=0.7, color="blue")
        axes[i, 0].set_xlabel(col)
        axes[i, 0].set_ylabel("Density")
        axes[i, 0].set_title(f"Original {col} Marginal")

        # Transformed with Gaussian overlay
        axes[i, 1].hist(df_trans[col], bins=30, density=True, alpha=0.7, color="red")
        x_range = np.linspace(df_trans[col].min(), df_trans[col].max(), 100)
        mu = df_trans[col].mean()
        std = df_trans[col].std()
        gaussian = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(
            -0.5 * ((x_range - mu) / std) ** 2
        )
        axes[i, 1].plot(x_range, gaussian, "k--", linewidth=2, label="Gaussian fit")
        axes[i, 1].set_xlabel(col)
        axes[i, 1].set_ylabel("Density")
        axes[i, 1].set_title(f"Transformed {col} Marginal")
        axes[i, 1].legend()

    plt.tight_layout()
    return fig


def create_history_plot(history, target_entropy=None):
    """Create optimization history plot."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Determinant
    axes[0].semilogy(history["iteration"], history["determinant"], "b-o", markersize=4)
    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Covariance Determinant")
    axes[0].set_title("Determinant Minimization")
    axes[0].grid(True, alpha=0.3)

    # Gaussian entropy
    axes[1].plot(history["iteration"], history["gaussian_entropy"], "r-o", markersize=4)
    if target_entropy is not None:
        axes[1].axhline(
            target_entropy,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Target H(uniform) = {target_entropy:.4f}",
        )
        axes[1].legend()
    axes[1].set_xlabel("Iteration")
    axes[1].set_ylabel("H(Gaussian)")
    axes[1].set_title("Gaussian Entropy → Target Uniform Entropy")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def format_results(entropy, history):
    """Format results as text."""
    det_reduction = (
        entropy["original"]["determinant"] / entropy["transformed"]["determinant"]
    )
    target_entropy = entropy["original"]["uniform_entropy"]
    final_entropy = entropy["transformed"]["gaussian_entropy"]
    entropy_gap = final_entropy - target_entropy

    text = f"""
TRANSFORMATION RESULTS
{'=' * 50}

Target Entropy (Uniform Distribution):
  H(uniform) = {target_entropy:.6f} nats

  This is the true entropy we want to reach.

Gaussian Entropy of Transformed Data:
  H(Gaussian) = {final_entropy:.6f} nats

  This assumes the transformed data is Gaussian with the
  current covariance. When H(Gaussian) = H(uniform), the
  distribution is perfectly Gaussian.

Gap to Target:
  H(Gaussian) - H(uniform) = {entropy_gap:.6f} nats
  (Should approach 0 for perfect Gaussianization)

Covariance Determinant:
  Original:    {entropy['original']['determinant']:.6e}
  Transformed: {entropy['transformed']['determinant']:.6e}
  Reduction:   {det_reduction:.2f}x

Optimization:
  Iterations with improvement: {len(history['iteration'])}
  Final determinant: {history['determinant'][-1]:.6e}
  Final H(Gaussian): {history['gaussian_entropy'][-1]:.6f}
"""
    return text


# Markdown explanation of Levenberg-Marquardt
LM_EXPLANATION = """
## How the Levenberg-Marquardt Algorithm Works

The **Levenberg-Marquardt (LM) algorithm** is used to minimize the covariance determinant. Unlike gradient descent, **LM has no learning rate** - here's why:

### The Key Insight

LM is designed for **least-squares problems** where you minimize a sum of squared residuals. Instead of taking steps proportional to the gradient (like gradient descent), LM solves a **local linear approximation** of the problem at each step.

### How It Works

1. **Compute the Jacobian** `J` - the matrix of partial derivatives of residuals with respect to parameters

2. **Solve the normal equations**:
   ```
   (J^T J + λI) δ = -J^T r
   ```
   where `r` is the residual vector and `λ` is a damping parameter

3. **The damping parameter λ replaces the learning rate**:
   - When `λ` is **large**: The step is small and in the gradient direction (like gradient descent with small learning rate)
   - When `λ` is **small**: The step approaches the Gauss-Newton step (a direct jump to the local minimum of the quadratic approximation)

4. **Adaptive adjustment**:
   - If a step **decreases** the objective: Accept it and **decrease λ** (take bigger steps)
   - If a step **increases** the objective: Reject it and **increase λ** (take smaller, safer steps)

### Why No Learning Rate?

The LM algorithm **automatically adapts** its step size through the damping parameter λ:
- It starts cautious (large λ, small steps)
- As it finds a good direction, it becomes more aggressive (small λ, large steps)
- If it overshoots, it backs off automatically

This makes LM much more robust than gradient descent - you don't need to tune a learning rate!

### In This Application

We minimize `log(det(Cov))` where `Cov` is the covariance matrix of the transformed points. The transformation is parameterized by coefficients of divergence-free basis functions, ensuring the transformation is **volume-preserving** and thus **entropy-conserving**.
"""

THEORY_EXPLANATION = """
## Theoretical Background

### Maximum Entropy Principle

A fundamental theorem states: **Among all distributions with a given covariance matrix, the Gaussian has maximum entropy.**

This means for any distribution with entropy `H₀` and covariance `Σ`:
- The Gaussian with the same covariance has entropy `H_Gaussian(Σ) ≥ H₀`
- Equality holds only when the distribution is Gaussian

### The Key Insight

If we apply a **volume-preserving transformation**:
1. The entropy stays fixed at `H₀` (entropy is conserved)
2. But the covariance changes

By **minimizing the covariance determinant** while preserving entropy:
- We reduce `H_Gaussian(Σ)` (the Gaussian entropy bound)
- When `H_Gaussian(Σ) = H₀`, the distribution must be Gaussian!

### Why Divergence-Free?

Divergence-free vector fields define **volume-preserving** transformations:
- The Jacobian determinant equals 1 everywhere
- Total probability volume is conserved
- **Entropy is conserved** under the transformation

This is the incompressibility condition from fluid dynamics: `∇·v = 0`

### The Operator

We construct divergence-free basis functions using Lowitzsch's operator:

**Ô = -I∇² + ∇∇ᵀ**

Applied to Gaussian RBFs, this produces matrix-valued functions where each column is a divergence-free vector field.
"""


def create_app():
    """Create the Gradio interface."""
    with gr.Blocks(
        title="Entropy-Conserving Transformations", theme=gr.themes.Soft()
    ) as app:
        gr.Markdown(
            """
        # Entropy-Conserving Transformations Using Divergence-Free Vector Fields

        Transform arbitrary distributions towards Gaussian form while **conserving entropy**.

        This demo uses divergence-free basis functions to create volume-preserving transformations,
        then minimizes the covariance determinant using the Levenberg-Marquardt algorithm.
        """
        )

        # State to hold the dataframe
        df_state = gr.State(None)

        with gr.Tabs():
            with gr.Tab("Transform Data"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Step 1: Load or Generate Data")

                        gr.Markdown(
                            """
**No CSV file?** Use "Generate Sample Data" below to create a uniform grid.

**Have your own CSV?** Format requirements:
- Header row with column names
- Numeric columns for coordinates (e.g., `x`, `y`, `z`)
- Example:
```
x,y
-9.5,-9.5
-9.5,-8.5
...
```
"""
                        )

                        with gr.Accordion(
                            "Generate Sample Data (no CSV needed)", open=True
                        ):
                            gr.Markdown(
                                "*Creates a uniform grid using VectorSampler - perfect for testing*"
                            )
                            n_per_dim = gr.Slider(
                                minimum=5,
                                maximum=500,
                                value=20,
                                step=1,
                                label="Points per dimension",
                            )
                            dimensions = gr.Radio(
                                choices=[2, 3], value=2, label="Dimensions"
                            )
                            generate_btn = gr.Button(
                                "Generate Uniform Distribution",
                                variant="primary",
                            )
                            download_file = gr.File(label="Download generated CSV")

                        with gr.Accordion("Upload Your Own CSV", open=False):
                            file_upload = gr.File(
                                label="Upload CSV file", file_types=[".csv"]
                            )
                            upload_btn = gr.Button("Load CSV", variant="secondary")

                        data_info = gr.Textbox(
                            label="Data Info", lines=8, interactive=False
                        )

                        gr.Markdown("### Step 2: Configure Transformation")

                        columns_input = gr.Textbox(
                            value="x, y",
                            label="Columns to transform (comma-separated)",
                            lines=3,
                        )
                        sigma = gr.Slider(
                            minimum=0.1,
                            maximum=200.0,
                            value=5.0,
                            step=0.1,
                            label="Sigma (RBF width)",
                        )
                        max_iterations = gr.Slider(
                            minimum=10,
                            maximum=5000,
                            value=100,
                            step=10,
                            label="Max iterations",
                        )

                        transform_btn = gr.Button(
                            "Run Transformation", variant="primary", size="lg"
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("### Results")

                        results_text = gr.Textbox(
                            label="Transformation Results",
                            lines=20,
                            interactive=False,
                        )

                        with gr.Row():
                            scatter_plot = gr.Plot(label="Before/After Scatter")

                        with gr.Row():
                            hist_plot = gr.Plot(label="Marginal Distributions")

                        with gr.Row():
                            history_plot = gr.Plot(label="Optimization History")

            with gr.Tab("How LM Works"):
                gr.Markdown(LM_EXPLANATION)

            with gr.Tab("Theory"):
                gr.Markdown(THEORY_EXPLANATION)

        # Event handlers
        def on_generate(n, dims):
            path, info, df = generate_sample_csv(n, dims)
            return path, info, df

        def on_upload(file):
            path, info, df = load_csv_file(file)
            return info, df

        generate_btn.click(
            fn=on_generate,
            inputs=[n_per_dim, dimensions],
            outputs=[download_file, data_info, df_state],
        )

        upload_btn.click(
            fn=on_upload, inputs=[file_upload], outputs=[data_info, df_state]
        )

        transform_btn.click(
            fn=run_transformation,
            inputs=[
                df_state,
                columns_input,
                sigma,
                max_iterations,
            ],
            outputs=[scatter_plot, hist_plot, history_plot, results_text],
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()
