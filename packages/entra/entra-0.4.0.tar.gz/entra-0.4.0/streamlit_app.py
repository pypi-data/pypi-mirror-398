"""
Streamlit App for Entropy-Conserving Transformations

This app demonstrates how divergence-free vector fields can transform
arbitrary distributions towards Gaussian form while conserving entropy.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from entra import DataFrameTransformer, VectorSampler

# Page config
st.set_page_config(
    page_title="Entropy-Conserving Transformations",
    page_icon="🔄",
    layout="wide",
)

# Title
st.title("Entropy-Conserving Transformations")
st.markdown(
    """
    Transform arbitrary distributions towards Gaussian form while **conserving entropy**.

    This demo uses divergence-free basis functions to create volume-preserving transformations,
    then minimizes the covariance determinant using the Levenberg-Marquardt algorithm.
    """
)

# Sidebar for configuration
st.sidebar.header("Configuration")

# Data source selection
data_source = st.sidebar.radio(
    "Data Source",
    ["Generate Sample Data", "Upload CSV"],
    help="Generate a uniform grid or upload your own CSV file",
)

df = None

if data_source == "Generate Sample Data":
    st.sidebar.markdown("*Creates a uniform grid using VectorSampler - perfect for testing*")

    n_per_dim = st.sidebar.slider(
        "Points per dimension",
        min_value=5,
        max_value=500,
        value=20,
        step=1,
    )

    dimensions = st.sidebar.radio("Dimensions", [2, 3], index=0)

    if st.sidebar.button("Generate Uniform Distribution", type="primary"):
        # Generate using VectorSampler
        if dimensions == 2:
            center = [0.0, 0.0]
        else:
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

        st.session_state["df"] = df
        st.session_state["columns"] = list(df.columns)
        st.sidebar.success(f"Generated {len(df)} points")

else:  # Upload CSV
    st.sidebar.markdown(
        """
        **CSV Format:**
        - Header row with column names
        - Numeric columns for coordinates

        Example:
        ```
        x,y
        -9.5,-9.5
        -9.5,-8.5
        ...
        ```
        """
    )

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state["df"] = df
        st.session_state["columns"] = list(df.columns)
        st.sidebar.success(f"Loaded {len(df)} points")

# Get df from session state if available
if "df" in st.session_state:
    df = st.session_state["df"]

# Transformation settings
st.sidebar.markdown("---")
st.sidebar.header("Transformation Settings")

columns_str = st.sidebar.text_area(
    "Columns to transform (comma-separated)",
    value="x, y",
    height=80,
)

sigma = st.sidebar.slider(
    "Sigma (RBF width)",
    min_value=0.1,
    max_value=200.0,
    value=5.0,
    step=0.1,
)

max_iterations = st.sidebar.slider(
    "Max iterations",
    min_value=10,
    max_value=5000,
    value=100,
    step=10,
)

# Main content
if df is not None:
    st.subheader("Data Preview")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.write(f"**Shape:** {df.shape}")
        st.write(f"**Columns:** {list(df.columns)}")
        st.dataframe(df.head(10), use_container_width=True)

    with col2:
        # Quick scatter plot of data
        columns = [c.strip() for c in columns_str.split(",")]
        if len(columns) >= 2 and all(c in df.columns for c in columns[:2]):
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.scatter(df[columns[0]], df[columns[1]], alpha=0.5, s=10)
            ax.set_xlabel(columns[0])
            ax.set_ylabel(columns[1])
            ax.set_title("Original Data")
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()

    # Run transformation button
    if st.sidebar.button("Run Transformation", type="primary"):
        columns = [c.strip() for c in columns_str.split(",")]

        # Validate columns
        missing = [c for c in columns if c not in df.columns]
        if missing:
            st.error(f"Columns not found: {missing}. Available: {list(df.columns)}")
        else:
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            def progress_callback(iteration, max_iter, det_val, entropy_val):
                progress = iteration / max_iter
                progress_bar.progress(progress)
                status_text.text(
                    f"Iter {iteration}/{max_iter} | Det: {det_val:.2e} | H(Gaussian): {entropy_val:.4f}"
                )

            # Run transformation
            transformer = DataFrameTransformer(
                sigma=sigma,
                max_iterations=max_iterations,
                verbose=False,
                progress_callback=progress_callback,
            )

            df_transformed = transformer.fit_transform(df, columns=columns)

            # Get entropy comparison
            entropy = transformer.get_entropy_comparison(df, df_transformed)
            target_entropy = entropy["original"]["uniform_entropy"]
            final_entropy = entropy["transformed"]["gaussian_entropy"]

            progress_bar.progress(1.0)
            status_text.text("Transformation complete!")

            # Store results in session state
            st.session_state["df_transformed"] = df_transformed
            st.session_state["entropy"] = entropy
            st.session_state["history"] = transformer.history_
            st.session_state["columns_used"] = columns

# Display results if available
if "df_transformed" in st.session_state:
    st.markdown("---")
    st.header("Results")

    entropy = st.session_state["entropy"]
    history = st.session_state["history"]
    columns = st.session_state["columns_used"]
    df_orig = st.session_state["df"]
    df_trans = st.session_state["df_transformed"]

    target_entropy = entropy["original"]["uniform_entropy"]
    final_entropy = entropy["transformed"]["gaussian_entropy"]
    entropy_gap = final_entropy - target_entropy
    det_reduction = entropy["original"]["determinant"] / entropy["transformed"]["determinant"]

    # Results summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Target H(uniform)", f"{target_entropy:.4f} nats")
    with col2:
        st.metric("Final H(Gaussian)", f"{final_entropy:.4f} nats")
    with col3:
        st.metric("Gap to Target", f"{entropy_gap:.4f} nats")
    with col4:
        st.metric("Determinant Reduction", f"{det_reduction:.2f}x")

    # Plots
    st.subheader("Visualizations")

    # Scatter plots
    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(df_orig[columns[0]], df_orig[columns[1]], alpha=0.5, s=10, c="blue")
        ax.set_xlabel(columns[0])
        ax.set_ylabel(columns[1])
        ax.set_title("Original Distribution")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(df_trans[columns[0]], df_trans[columns[1]], alpha=0.5, s=10, c="red")
        ax.set_xlabel(columns[0])
        ax.set_ylabel(columns[1])
        ax.set_title("Transformed (Towards Gaussian)")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    # Optimization history
    st.subheader("Optimization History")
    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.semilogy(history["iteration"], history["determinant"], "b-o", markersize=4)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Covariance Determinant")
        ax.set_title("Determinant Minimization")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(history["iteration"], history["gaussian_entropy"], "r-o", markersize=4, label="H(Gaussian)")
        ax.axhline(target_entropy, color="green", linestyle="--", linewidth=2,
                   label=f"Target H(uniform) = {target_entropy:.4f}")
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Entropy (nats)")
        ax.set_title("H(Gaussian) → Target H(uniform)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    # Marginal distributions
    st.subheader("Marginal Distributions")

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
        gaussian = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mu) / std) ** 2)
        axes[i, 1].plot(x_range, gaussian, "k--", linewidth=2, label="Gaussian fit")
        axes[i, 1].set_xlabel(col)
        axes[i, 1].set_ylabel("Density")
        axes[i, 1].set_title(f"Transformed {col} Marginal")
        axes[i, 1].legend()

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# Theory tabs at the bottom
st.markdown("---")

tab1, tab2 = st.tabs(["How LM Works", "Theory"])

with tab1:
    st.markdown(
        """
        ## How the Levenberg-Marquardt Algorithm Works

        The **Levenberg-Marquardt (LM) algorithm** is used to minimize the covariance determinant.
        Unlike gradient descent, **LM has no learning rate** - here's why:

        ### The Key Insight

        LM is designed for **least-squares problems** where you minimize a sum of squared residuals.
        Instead of taking steps proportional to the gradient (like gradient descent), LM solves a
        **local linear approximation** of the problem at each step.

        ### How It Works

        1. **Compute the Jacobian** `J` - the matrix of partial derivatives of residuals with respect to parameters

        2. **Solve the normal equations**:
           ```
           (J^T J + λI) δ = -J^T r
           ```
           where `r` is the residual vector and `λ` is a damping parameter

        3. **The damping parameter λ replaces the learning rate**:
           - When `λ` is **large**: The step is small and in the gradient direction
           - When `λ` is **small**: The step approaches the Gauss-Newton step

        4. **Adaptive adjustment**:
           - If a step **decreases** the objective: Accept it and **decrease λ**
           - If a step **increases** the objective: Reject it and **increase λ**

        ### Why No Learning Rate?

        The LM algorithm **automatically adapts** its step size through the damping parameter λ.
        This makes LM much more robust than gradient descent - you don't need to tune a learning rate!
        """
    )

with tab2:
    st.markdown(
        """
        ## Theoretical Background

        ### Maximum Entropy Principle

        A fundamental theorem states: **Among all distributions with a given covariance matrix,
        the Gaussian has maximum entropy.**

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

        Applied to Gaussian RBFs, this produces matrix-valued functions where each column
        is a divergence-free vector field.
        """
    )
