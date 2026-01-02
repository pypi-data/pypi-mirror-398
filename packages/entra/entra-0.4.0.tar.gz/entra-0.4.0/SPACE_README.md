---
title: Entropy-Conserving Transformations
emoji: 🔄
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: bsd-3-clause
---

# Entropy-Conserving Transformations Using Divergence-Free Vector Fields

Transform arbitrary distributions towards Gaussian form while **conserving entropy**.

## What This Does

This app demonstrates a principled method for reshaping probability distributions:

1. **Start** with any distribution (e.g., uniform)
2. **Apply** volume-preserving transformations using divergence-free vector fields
3. **Minimize** the covariance determinant using Levenberg-Marquardt optimization
4. **Result**: Distribution approaches Gaussian form while entropy is conserved

## The Key Insight

- **Gaussian distributions have maximum entropy** for a given covariance matrix
- **Divergence-free transformations are volume-preserving** (entropy-conserving)
- By minimizing covariance determinant while preserving entropy, we drive the distribution towards Gaussian

## How to Use

1. **Load Data**: Upload your own CSV or generate a uniform distribution
2. **Configure**: Set the columns to transform, sigma (RBF width), and other parameters
3. **Transform**: Click "Run Transformation" to start the optimization
4. **Analyze**: View the before/after plots and entropy comparison

## Why Levenberg-Marquardt Has No Learning Rate

Unlike gradient descent, LM automatically adapts its step size through a damping parameter λ:
- Large λ → small, cautious steps (like gradient descent)
- Small λ → large steps towards the local minimum
- λ adjusts automatically based on whether steps improve the objective

See the "How LM Works" tab in the app for more details.

## References

- S. Lowitzsch, *Approximation and Interpolation Employing Divergence-Free Radial Basis Functions With Applications*, PhD thesis, Texas A&M University, 2002.

## Code

Source code: [github.com/Kapoorlabs-CAPED/entra](https://github.com/Kapoorlabs-CAPED/entra)
