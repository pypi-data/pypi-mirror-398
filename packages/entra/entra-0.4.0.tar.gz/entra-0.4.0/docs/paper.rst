====================================================================================
Entropy-Conserving Transformations Using Divergence-Free Vector Fields
====================================================================================

:Author: Varun Kapoor
:Affiliation: Kapoorlabs, Paris, France; Universität Osnabrück, Osnabrück, Germany
:Code: https://github.com/Kapoorlabs-CAPED/entra

Abstract
========

We present a method for transforming arbitrary probability distributions towards Gaussian form using divergence-free vector fields constructed from radial basis functions. Our approach exploits the maximum entropy property of Gaussian distributions: among all distributions with a given covariance matrix, the Gaussian has maximum entropy. By iteratively minimizing the covariance determinant using volume-preserving (divergence-free) transformations, we reshape distributions while conserving their fundamental entropy. The divergence-free basis functions are constructed using a differential operator applied to Gaussian radial basis functions, following the methodology of Lowitzsch [1].

Introduction
============

The Gaussian distribution holds a special place in probability theory and information theory. A fundamental theorem states that:

    **Among all probability distributions with a given mean and covariance matrix, the Gaussian distribution has the maximum differential entropy.**

This maximum entropy principle has profound implications. Consider a distribution with entropy :math:`H_0` and covariance :math:`\Sigma`. Since the Gaussian with the same covariance has entropy :math:`H_{Gaussian}(\Sigma) \geq H_0`, with equality only when the distribution is Gaussian. If we apply a **volume-preserving transformation**, the entropy remains fixed at :math:`H_0`, but the covariance changes. By **minimizing the covariance determinant**, we reduce :math:`H_{Gaussian}(\Sigma)` until it equals :math:`H_0`, at which point the distribution must be Gaussian.

The key insight of our method is that **divergence-free vector fields define volume-preserving transformations**. By constructing transformations as linear combinations of divergence-free basis functions, we guarantee that:

1. The Jacobian determinant of the transformation equals 1 everywhere
2. Total probability volume is conserved
3. Differential entropy is conserved under the transformation

This allows us to iteratively minimize the covariance determinant while keeping entropy fixed, driving the distribution towards Gaussian form.

Theoretical Background
======================

Maximum Entropy Property of Gaussians
-------------------------------------

For a D-dimensional random variable with mean :math:`\mu` and covariance matrix :math:`\Sigma`, the differential entropy is bounded by:

.. math::

    H(X) \leq \frac{D}{2}\left(1 + \ln(2\pi)\right) + \frac{1}{2}\ln\det(\Sigma)

with equality if and only if X is Gaussian. The right-hand side is the entropy of a Gaussian with covariance :math:`\Sigma`, denoted :math:`H_{Gaussian}(\Sigma)`.

**Corollary**: If we have a distribution with fixed entropy :math:`H_0`, and we apply volume-preserving transformations that minimize :math:`\det(\Sigma)`, the Gaussian entropy bound :math:`H_{Gaussian}(\Sigma)` decreases. When :math:`H_{Gaussian}(\Sigma) = H_0`, the inequality becomes an equality, meaning the distribution has become Gaussian.

Volume-Preserving Transformations
---------------------------------

A transformation :math:`y = T(x)` is volume-preserving if its Jacobian determinant satisfies:

.. math::

    \det\left(\frac{\partial T}{\partial x}\right) = 1

For infinitesimal transformations of the form :math:`y = x + \varepsilon v(x)`, this condition becomes:

.. math::

    \nabla \cdot v = 0

That is, the velocity field :math:`v` must be **divergence-free**. This is the incompressibility condition from fluid dynamics.

Entropy Conservation and Volume Preservation: The Complete Derivation
----------------------------------------------------------------------

We now derive the fundamental connection between entropy conservation and volume preservation, showing that **volume preservation is both necessary and sufficient for entropy conservation**.

**The Change of Variables Formula for Entropy**

Consider a random variable :math:`X` with probability density :math:`p_X(x)`. Under a smooth invertible transformation :math:`Y = T(X)`, the density of :math:`Y` is given by:

.. math::

    p_Y(y) = \frac{p_X(T^{-1}(y))}{|\det(J_T(T^{-1}(y)))|)

where :math:`J_T = \frac{\partial T}{\partial x}` is the Jacobian matrix of the transformation.

**Derivation of Entropy Change**

The differential entropy of :math:`Y` is:

.. math::

    H(Y) = -\int p_Y(y) \ln p_Y(y) \, dy

Substituting the density transformation formula:

.. math::

    H(Y) = -\int \frac{p_X(T^{-1}(y))}{|\det(J_T)|} \ln\left(\frac{p_X(T^{-1}(y))}{|\det(J_T)|}\right) dy

Applying the change of variables :math:`y = T(x)`, so :math:`dy = |\det(J_T)| dx`:

.. math::

    H(Y) = -\int p_X(x) \ln\left(\frac{p_X(x)}{|\det(J_T(x))|}\right) dx

Expanding the logarithm:

.. math::

    H(Y) = -\int p_X(x) \ln p_X(x) \, dx + \int p_X(x) \ln|\det(J_T(x))| \, dx

This gives us the **fundamental entropy transformation law**:

.. math::

    (H(Y) = H(X) + E_X\left[\ln|\det(J_T(X))|\right])

**The Entropy Conservation Condition**

For entropy to be conserved (:math:`H(Y) = H(X)`), we require:

.. math::

    E_X\left[\ln|\det(J_T(X))|\right] = 0

**Volume Preservation Implies Entropy Conservation**

If the transformation is volume-preserving, meaning :math:`|\det(J_T(x))| = 1` for all :math:`x`, then:

.. math::

    \ln|\det(J_T(x))| = \ln(1) = 0

and therefore:

.. math::

    E_X\left[\ln|\det(J_T(X))|\right] = 0

Thus volume preservation is a **sufficient condition** for entropy conservation.

**Divergence-Free Fields Generate Volume-Preserving Flows**

Consider a velocity field :math:`v(x)` and the flow it generates:

.. math::

    \frac{dx}{dt} = v(x)

Let :math:`\Phi_t(x_0)` denote the position at time :math:`t` of a particle starting at :math:`x_0`. The Jacobian determinant of this flow map evolves according to **Liouville's equation**:

.. math::

    \frac{d}{dt}\det(J_{\Phi_t}) = \det(J_{\Phi_t}) \cdot (\nabla \cdot v)

Taking the logarithm:

.. math::

    \frac{d}{dt}\ln|\det(J_{\Phi_t})| = \nabla \cdot v

**The Divergence-Free Condition**

If the vector field is divergence-free (:math:`\nabla \cdot v = 0`), then:

.. math::

    \frac{d}{dt}\ln|\det(J_{\Phi_t})| = 0

This means :math:`\ln|\det(J_{\Phi_t})|` is constant along the flow. Since at :math:`t=0` we have :math:`\Phi_0(x) = x` (identity map), the Jacobian is :math:`J_{\Phi_0} = I` and :math:`\det(J_{\Phi_0}) = 1`.

Therefore, for all :math:`t`:

.. math::

    |\det(J_{\Phi_t})| = 1

**The Complete Chain of Implications**

We have established:

.. math::

    \nabla \cdot v = 0 \Rightarrow |\det(J)| = 1 \Rightarrow H(Y) = H(X)

In words:

1. **Divergence-free vector field** :math:`\Rightarrow` **Volume-preserving transformation**
2. **Volume-preserving transformation** :math:`\Rightarrow` **Entropy conservation**

This is why we construct our transformations from divergence-free basis functions: it guarantees entropy conservation by construction, allowing us to minimize the covariance determinant while keeping entropy fixed.

Divergence-Free Basis Functions
===============================

Construction via Differential Operator
--------------------------------------

Following Lowitzsch [1]_, we construct divergence-free vector fields by applying the differential operator:

.. math::

    \hat{O} = -I\nabla^2 + \nabla\nabla^T

to scalar radial basis functions. For a Gaussian RBF centered at :math:`c_l`:

.. math::

    \phi_l(x) = \exp\left(-\frac{\|x - c_l\|^2}{2\sigma^2}\right)

the operator produces a :math:`D \times D` matrix-valued function:

.. math::

    \Phi_l(x) = \hat{O}\phi_l(x)

Each column of this matrix is a divergence-free vector field.

Explicit Form for Gaussian RBFs
-------------------------------

For a Gaussian RBF, the components of the tensor basis are:

.. math::

    \Phi_{ij}(x) = \left[-\delta_{ij}\nabla^2 + \frac{\partial^2}{\partial x_i \partial x_j}\right]\phi(x)

where:

.. math::

    \nabla^2\phi = \frac{1}{\sigma^4}\left(\|x-c\|^2 - D\sigma^2\right)\phi

.. math::

    \frac{\partial^2\phi}{\partial x_i \partial x_j} = \frac{1}{\sigma^4}\left[(x_i-c_i)(x_j-c_j) - \delta_{ij}\sigma^2\right]\phi

Algorithm
=========

The algorithm proceeds in two stages:

Stage 1: Initial Optimization
-----------------------------

1. Sample J points from the initial distribution on a regular grid
2. Place L centers for the divergence-free basis functions
3. Construct the tensor basis :math:`\Phi` of shape (J, L, D, D)
4. Define transformation: :math:`y' = y + \sum_l \Phi_l(y) c_l` with coefficients :math:`c` of shape (L, D)
5. Minimize :math:`\det(\mathrm{Cov}(y'))` using Levenberg-Marquardt optimization
6. Compute the effective basis: :math:`V_l = \Phi_l \cdot c_l`

Stage 2: Iterative Refinement (Outer Loop)
------------------------------------------

After Stage 1, the tensor basis (J, L, D, D) with coefficients (L, D) collapses to an effective basis (J, L, D) representing L vector fields.

For each outer iteration:

1. Create transformation: :math:`y' = y + \sum_l c_l V_l` with L scalar coefficients
2. Minimize :math:`\det(\mathrm{Cov}(y'))` over the L scalar coefficients
3. Update the basis: :math:`V_l \leftarrow c_l V_l`
4. Transform points: :math:`y \leftarrow y'`
5. Repeat until convergence

Entropy Verification
====================

To verify entropy conservation, we employ multiple entropy estimators:

Parametric Estimators
---------------------

**Uniform distribution** (initial):

.. math::

    H_{uniform} = \ln(V)

where V is the volume of the support.

**Gaussian distribution** (after transformation):

.. math::

    H_{Gaussian} = \frac{D}{2}\left(1 + \ln(2\pi)\right) + \frac{1}{2}\ln\det(\Sigma)

Non-parametric Estimator
------------------------

The Kozachenko-Leonenko k-NN estimator provides a distribution-free entropy estimate:

.. math::

    \hat{H} = \frac{D}{N}\sum_{i=1}^{N}\ln(2\rho_{k,i}) + \ln(V_D) + \psi(N) - \psi(k)

where :math:`\rho_{k,i}` is the distance to the k-th nearest neighbor of point i, :math:`V_D` is the volume of the unit ball in D dimensions, and :math:`\psi` is the digamma function.

For a truly volume-preserving transformation, the k-NN entropy estimate should remain constant before and after transformation.

Results
=======

The algorithm successfully transforms uniform distributions towards Gaussian form:

- The covariance determinant decreases monotonically
- 2D projections of 3D distributions show transformation from rectangular (uniform) to elliptical (Gaussian) shapes
- The k-NN entropy estimate remains approximately constant, confirming volume preservation

Conclusion
==========

We have demonstrated a principled method for transforming arbitrary distributions towards Gaussian form using divergence-free vector fields. The key theoretical insights are:

1. Volume-preserving (divergence-free) transformations conserve entropy
2. For any distribution, the Gaussian with the same covariance has higher or equal entropy
3. Minimizing the covariance determinant while preserving entropy reduces the gap between the distribution's entropy and the Gaussian bound, until they become equal

When the distribution's entropy equals the Gaussian entropy bound for its covariance, the distribution must be Gaussian. The divergence-free basis functions constructed from Gaussian RBFs provide a flexible and computationally tractable framework for implementing these entropy-conserving, covariance-minimizing transformations.

References
==========

.. [1] S. Lowitzsch, *Approximation and Interpolation Employing Divergence-Free Radial Basis Functions With Applications*, PhD thesis, Department of Mathematics, Texas A&M University, 2002.
