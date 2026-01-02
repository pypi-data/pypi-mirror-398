"""
Entra Configuration Dataclass

Defines the typed configuration schema for covariance optimization.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Sampling:
    """Data sampling parameters."""
    dimension: int = 2
    num_points_per_dim: int = 20
    delta_x: float = 1.0
    center: List[float] = field(default_factory=lambda: [0.0, 0.0])
    distribution: str = "uniform"


@dataclass
class Stage1:
    """Stage 1: TensorBasis optimization parameters."""
    max_iterations: int = 1000
    tolerance: float = 1e-12
    print_every: int = 5


@dataclass
class Stage2:
    """Stage 2: Outer loop refinement parameters."""
    n_outer: int = 5
    max_iterations: int = 1000
    tolerance: float = 1e-10


@dataclass
class Sweep:
    """Sigma sweep configuration."""
    enabled: bool = True
    sigmas: List[float] = field(default_factory=lambda: [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 100])
    description: str = ""


@dataclass
class Single:
    """Single run configuration (when sweep is disabled)."""
    sigma: float = 5.0


@dataclass
class Output:
    """Output settings."""
    save_csv: bool = True
    save_plots: bool = False
    verbose: bool = True


@dataclass
class scenario_entra:
    """Root configuration for entra covariance optimization."""
    sampling: Sampling = field(default_factory=Sampling)
    stage1: Stage1 = field(default_factory=Stage1)
    stage2: Stage2 = field(default_factory=Stage2)
    sweep: Sweep = field(default_factory=Sweep)
    single: Single = field(default_factory=Single)
    output: Output = field(default_factory=Output)
