"""
CSV Transform Configuration Dataclass

Defines the typed configuration schema for CSV transformation demo.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Data:
    """Data source configuration."""

    csv_path: Optional[str] = None  # None = generate synthetic data
    dimension: int = 2  # 2 or 3
    num_points_per_dim: int = 20  # For synthetic data generation


@dataclass
class Transform:
    """Transformation parameters."""

    sigma: float = 4.0  # Optimized value from sweep
    stage1_max_iterations: int = 1000
    stage1_tolerance: float = 1e-12
    stage2_n_outer: int = 5
    stage2_max_iterations: int = 1000
    stage2_tolerance: float = 1e-10


@dataclass
class Output:
    """Output settings."""

    save_csv: bool = True
    save_plots: bool = True
    output_dir: str = "results"
    verbose: bool = True


@dataclass
class scenario_csv_transform:
    """Root configuration for CSV transformation."""

    data: Data = field(default_factory=Data)
    transform: Transform = field(default_factory=Transform)
    output: Output = field(default_factory=Output)
