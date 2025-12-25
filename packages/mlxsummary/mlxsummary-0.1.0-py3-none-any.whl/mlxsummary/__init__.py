"""
mlxsummary - Model inspection and summary tools for MLX
=======================================================

A library for inspecting and summarizing MLX neural network models.

Quick Start:
    >>> import mlx.nn as nn
    >>> from mlxsummary import summary
    >>>
    >>> model = nn.Sequential(
    ...     nn.Linear(784, 256),
    ...     nn.ReLU(),
    ...     nn.Linear(256, 10)
    ... )
    >>> summary(model)

Available Functions:
    summary     - Generate a formatted model summary
    inspect     - Create an inspector for detailed analysis
    count_params - Count model parameters
    get_layers  - Get list of layer information
    get_stats   - Get aggregate model statistics
    to_dict     - Export model info to dictionary
    tree        - Shortcut for tree format summary
    table       - Shortcut for table format summary

Classes:
    MLXInspector     - Main inspector class
    LayerInfo        - Information about a single layer
    ModelStats       - Aggregate model statistics
    OutputFormat     - Available output formats
    FormatterOptions - Options for formatters
"""

__version__ = "0.1.0"
__author__ = "MLX Summary Contributors"

# Core inspector
# Formatters
from .formatters import (
    BaseFormatter,
    FormatterOptions,
    JsonFormatter,
    MarkdownFormatter,
    MinimalFormatter,
    OutputFormat,
    TableFormatter,
    TreeFormatter,
    get_formatter,
)
from .inspector import (
    LayerInfo,
    MLXInspector,
    ModelStats,
)

# High-level API
from .summary import (
    count_params,
    get_layers,
    get_stats,
    inspect,
    summary,
    table,
    to_dict,
    tree,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "MLXInspector",
    "LayerInfo",
    "ModelStats",
    # Formatters
    "OutputFormat",
    "FormatterOptions",
    "get_formatter",
    "BaseFormatter",
    "TableFormatter",
    "TreeFormatter",
    "JsonFormatter",
    "MarkdownFormatter",
    "MinimalFormatter",
    # High-level API
    "summary",
    "inspect",
    "count_params",
    "get_layers",
    "get_stats",
    "to_dict",
    "tree",
    "table",
]
