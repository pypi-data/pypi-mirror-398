==================================
Mathematical Formulation
==================================

This document describes the mathematical foundations of the divergence-free
tensor basis function approach implemented in the ``entra`` package.

.. contents:: Table of Contents
   :depth: 2
   :local:

Overview
--------

The goal is to construct a set of **divergence-free vector basis functions**
that can be used to represent incompressible vector fields. We achieve this by
applying a specific differential operator to scalar Gaussian radial basis
functions (RBFs).


1. Grid Sampling
----------------

We sample evaluation points on a regular D-dimensional grid centered at
:math:`\mathbf{x}_{\text{center}}` with spacing :math:`\delta x` in each dimension.

Grid Point Formula
~~~~~~~~~~~~~~~~~~

For a grid with :math:`n` points per dimension, the grid points are:

.. math::

   \mathbf{x}_{i_1, i_2, \ldots, i_D} = \mathbf{x}_{\text{center}} +
   \begin{pmatrix}
   (i_1 - \frac{n-1}{2}) \cdot \delta x_1 \\
   (i_2 - \frac{n-1}{2}) \cdot \delta x_2 \\
   \vdots \\
   (i_D - \frac{n-1}{2}) \cdot \delta x_D
   \end{pmatrix}

where :math:`i_d \in \{0, 1, \ldots, n_d - 1\}` for each dimension :math:`d`.

The total number of grid points is:

.. math::

   J = \prod_{d=1}^{D} n_d


2. Scalar Basis Functions
-------------------------

We use Gaussian radial basis functions (RBFs) centered at :math:`L` chosen
center points :math:`\{\mathbf{c}_1, \mathbf{c}_2, \ldots, \mathbf{c}_L\}`.

Isotropic Gaussian RBF
~~~~~~~~~~~~~~~~~~~~~~

For a single width parameter :math:`\sigma`:

.. math::

   \phi_l(\mathbf{x}) = \exp\left( -\frac{\|\mathbf{x} - \mathbf{c}_l\|^2}{2\sigma^2} \right)

where :math:`\|\mathbf{x} - \mathbf{c}_l\|^2 = \sum_{d=1}^{D} (x_d - c_{l,d})^2`.

Anisotropic Gaussian RBF
~~~~~~~~~~~~~~~~~~~~~~~~

For dimension-specific width parameters :math:`\boldsymbol{\sigma} = (\sigma_1, \sigma_2, \ldots, \sigma_D)`:

.. math::

   \phi_l(\mathbf{x}) = \exp\left( -\sum_{d=1}^{D} \frac{(x_d - c_{l,d})^2}{2\sigma_d^2} \right)

Width Parameter Selection
~~~~~~~~~~~~~~~~~~~~~~~~~

The width parameter is typically chosen as a fraction of the grid spacing:

.. math::

   \sigma = \alpha \cdot \delta x

where :math:`\alpha = 0.7` is the default ``sigma_factor``.


3. Tensor Operator
------------------

The key insight is that applying the operator :math:`\hat{O}` to any scalar
function produces a **divergence-free** vector field.

Operator Definition
~~~~~~~~~~~~~~~~~~~

The tensor operator is defined as:

.. math::

   \hat{O} = -\mathbf{I} \nabla^2 + \nabla \nabla^T

where:

- :math:`\mathbf{I}` is the :math:`D \times D` identity matrix
- :math:`\nabla^2` is the Laplacian operator
- :math:`\nabla \nabla^T` is the outer product of the gradient with itself (Hessian structure)

Component Form
~~~~~~~~~~~~~~

In component notation, for a scalar function :math:`\phi`:

.. math::

   [\hat{O} \phi]_{ij} = -\delta_{ij} \nabla^2 \phi + \frac{\partial^2 \phi}{\partial x_i \partial x_j}

where :math:`\delta_{ij}` is the Kronecker delta.


4. Tensor Basis Functions
-------------------------

Applying :math:`\hat{O}` to the Gaussian RBF :math:`\phi_l` yields a
:math:`D \times D` matrix-valued function.

Analytical Formula
~~~~~~~~~~~~~~~~~~

For a Gaussian RBF with center :math:`\mathbf{c}_l` and width :math:`\sigma`:

.. math::

   \Phi_l(\mathbf{x}) = \hat{O} \phi_l(\mathbf{x})

The explicit formula is:

.. math::

   \Phi_l(\mathbf{x}) = \left[ \frac{D-1}{\sigma^2} - \frac{\|\mathbf{x} - \mathbf{c}_l\|^2}{\sigma^4} \right] \mathbf{I}_D \cdot \phi_l(\mathbf{x}) + \frac{(\mathbf{x} - \mathbf{c}_l)(\mathbf{x} - \mathbf{c}_l)^T}{\sigma^4} \cdot \phi_l(\mathbf{x})

Derivation
~~~~~~~~~~

Starting from :math:`\phi_l(\mathbf{x}) = \exp\left( -\frac{r^2}{2\sigma^2} \right)`
where :math:`r^2 = \|\mathbf{x} - \mathbf{c}_l\|^2`:

**First derivatives:**

.. math::

   \frac{\partial \phi_l}{\partial x_i} = -\frac{(x_i - c_{l,i})}{\sigma^2} \phi_l

**Second derivatives:**

.. math::

   \frac{\partial^2 \phi_l}{\partial x_i \partial x_j} = \left[ \frac{(x_i - c_{l,i})(x_j - c_{l,j})}{\sigma^4} - \frac{\delta_{ij}}{\sigma^2} \right] \phi_l

**Laplacian:**

.. math::

   \nabla^2 \phi_l = \sum_{i=1}^{D} \frac{\partial^2 \phi_l}{\partial x_i^2} = \left[ \frac{r^2}{\sigma^4} - \frac{D}{\sigma^2} \right] \phi_l

**Applying the operator:**

.. math::

   [\hat{O} \phi_l]_{ij} = -\delta_{ij} \nabla^2 \phi_l + \frac{\partial^2 \phi_l}{\partial x_i \partial x_j}

Substituting:

.. math::

   [\hat{O} \phi_l]_{ij} = \left[ \frac{D-1}{\sigma^2} - \frac{r^2}{\sigma^4} \right] \delta_{ij} \phi_l + \frac{(x_i - c_{l,i})(x_j - c_{l,j})}{\sigma^4} \phi_l


5. Divergence-Free Property
---------------------------

Each column of the matrix :math:`\Phi_l(\mathbf{x})` forms a **divergence-free
vector field**.

Column Vector Fields
~~~~~~~~~~~~~~~~~~~~

For a :math:`D \times D` matrix :math:`\Phi`, the :math:`d`-th column is a vector field:

.. math::

   \mathbf{V}_d = \Phi_{:,d} = \begin{pmatrix} \Phi_{1d} \\ \Phi_{2d} \\ \vdots \\ \Phi_{Dd} \end{pmatrix}

Divergence Computation
~~~~~~~~~~~~~~~~~~~~~~

The divergence of a vector field :math:`\mathbf{V} = (V_1, V_2, \ldots, V_D)` is:

.. math::

   \text{div}(\mathbf{V}) = \nabla \cdot \mathbf{V} = \sum_{i=1}^{D} \frac{\partial V_i}{\partial x_i}

For column :math:`d` of :math:`\Phi_l`:

.. math::

   \text{div}(\mathbf{V}_d) = \sum_{i=1}^{D} \frac{\partial \Phi_{id}}{\partial x_i}

Proof of Divergence-Free
~~~~~~~~~~~~~~~~~~~~~~~~

The operator :math:`\hat{O} = -\mathbf{I}\nabla^2 + \nabla\nabla^T` produces
divergence-free fields because:

.. math::

   \text{div}([\hat{O}\phi]_{:,d}) = -\frac{\partial}{\partial x_d}(\nabla^2 \phi) + \sum_{i=1}^{D} \frac{\partial^3 \phi}{\partial x_i^2 \partial x_d} = 0

This holds because:

.. math::

   \sum_{i=1}^{D} \frac{\partial^3 \phi}{\partial x_i^2 \partial x_d} = \frac{\partial}{\partial x_d} \left( \sum_{i=1}^{D} \frac{\partial^2 \phi}{\partial x_i^2} \right) = \frac{\partial}{\partial x_d}(\nabla^2 \phi)


6. Discrete Divergence
----------------------

In the discrete setting, we compute divergence using finite differences on the
grid points.

Central Difference
~~~~~~~~~~~~~~~~~~

For interior points, the partial derivative is approximated by:

.. math::

   \frac{\partial V_i}{\partial x_i} \approx \frac{V_i(\mathbf{x} + \delta x_i \mathbf{e}_i) - V_i(\mathbf{x} - \delta x_i \mathbf{e}_i)}{2 \delta x_i}

where :math:`\mathbf{e}_i` is the unit vector in direction :math:`i`.

Discrete Divergence
~~~~~~~~~~~~~~~~~~~

The discrete divergence at grid point :math:`\mathbf{x}_j` is:

.. math::

   (\text{div } \mathbf{V})_j = \sum_{i=1}^{D} \frac{V_i(\mathbf{x}_{j+\mathbf{e}_i}) - V_i(\mathbf{x}_{j-\mathbf{e}_i})}{2 \delta x_i}


7. Output Array Shapes
----------------------

The implementation uses consistent array shapes throughout:

+-------------------+-------------------------+----------------------------------+
| Object            | Shape                   | Description                      |
+===================+=========================+==================================+
| Evaluation points | :math:`(J, D)`          | J grid points in D dimensions    |
+-------------------+-------------------------+----------------------------------+
| Centers           | :math:`(L, D)`          | L center points in D dimensions  |
+-------------------+-------------------------+----------------------------------+
| Scalar basis      | :math:`(J, L)`          | L basis values at J points       |
+-------------------+-------------------------+----------------------------------+
| Tensor basis      | :math:`(J, L, D, D)`    | L matrices at J points           |
+-------------------+-------------------------+----------------------------------+
| Column divergence | :math:`(J, L, D)`       | Divergence of D columns          |
+-------------------+-------------------------+----------------------------------+


References
----------

1. Lowitzsch, S. (2005). Matrix-valued radial basis functions: stability
   estimates and applications. *Advances in Computational Mathematics*,
   23(3), 299-315.

2. Wendland, H. (2004). *Scattered Data Approximation*. Cambridge University
   Press.

3. Narcowich, F. J., & Ward, J. D. (1994). Generalized Hermite interpolation
   via matrix-valued conditionally positive definite functions. *Mathematics
   of Computation*, 63(208), 661-687.
