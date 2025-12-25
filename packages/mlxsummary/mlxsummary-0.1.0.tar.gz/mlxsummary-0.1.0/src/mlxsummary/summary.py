"""
High-level summary API for MLX models.
"""

from __future__ import annotations

import sys
from typing import Any, TextIO

import mlx.nn as nn

from .formatters import (
    FormatterOptions,
    OutputFormat,
    get_formatter,
)
from .inspector import LayerInfo, MLXInspector, ModelStats


def summary(
    model: nn.Module,
    *,
    format: OutputFormat | str = "table",
    show_shapes: bool = True,
    show_trainable: bool = False,
    show_frozen: bool = False,
    max_depth: int | None = None,
    max_rows: int | None = None,
    include_zero_param: bool = True,
    width: int = 125,
    print_output: bool = True,
    file: TextIO = sys.stdout,
) -> str:
    """
    Generate and optionally print a summary of an MLX model.

    This is the main entry point for generating model summaries.

    Args:
        model: The MLX nn.Module to summarize.
        format: Output format - "table", "tree", "json", "markdown", or "minimal".
        show_shapes: Include layer shape information (default: True).
        show_trainable: Show trainable parameter counts (default: True).
        show_frozen: Show frozen parameter counts (default: False).
        max_depth: Maximum layer depth to show (None for all).
        max_rows: Maximum number of rows to display (None for all).
        include_zero_param: Include layers with zero parameters (default: True).
        width: Output width for table format (default: 100).
        print_output: Whether to print the output (default: True).
        file: File to write output to (default: stdout).

    Returns:
        The formatted summary string.

    Example:
        >>> import mlx.nn as nn
        >>> from mlxsummary import summary
        >>>
        >>> model = nn.Sequential(
        ...     nn.Linear(784, 256),
        ...     nn.ReLU(),
        ...     nn.Linear(256, 10)
        ... )
        >>> summary(model)

        >>> # Get JSON output without printing
        >>> json_str = summary(model, format="json", print_output=False)
    """
    inspector = MLXInspector(model)

    options = FormatterOptions(
        show_shapes=show_shapes,
        show_trainable=show_trainable,
        show_frozen=show_frozen,
        max_depth=max_depth,
        max_rows=max_rows,
        include_zero_param=include_zero_param,
        width=width,
    )

    formatter = get_formatter(inspector, format, options)
    output = formatter.format()

    if print_output:
        print(output, file=file)

    return output


def inspect(model: nn.Module) -> MLXInspector:
    """
    Create an inspector for detailed model analysis.

    Use this when you need programmatic access to layer information
    rather than just a printed summary.

    Args:
        model: The MLX nn.Module to inspect.

    Returns:
        An MLXInspector instance.

    Example:
        >>> from mlxsummary import inspect
        >>>
        >>> inspector = inspect(model)
        >>> layers = inspector.get_layers()
        >>> stats = inspector.get_stats()
        >>> linear_layers = inspector.find_layers(nn.Linear)
    """
    return MLXInspector(model)


def count_params(model: nn.Module, trainable_only: bool = False) -> int:
    """
    Count the number of parameters in a model.

    Args:
        model: The MLX nn.Module to count parameters for.
        trainable_only: If True, only count trainable parameters.

    Returns:
        The parameter count.

    Example:
        >>> total = count_params(model)
        >>> trainable = count_params(model, trainable_only=True)
    """
    inspector = MLXInspector(model)
    stats = inspector.get_stats()

    if trainable_only:
        return stats.trainable_params
    return stats.total_params


def get_layers(
    model: nn.Module,
    layer_type: type[nn.Module] | None = None,
    name_pattern: str | None = None,
) -> list[LayerInfo]:
    """
    Get a list of layers from a model.

    Args:
        model: The MLX nn.Module to get layers from.
        layer_type: Optional filter by layer type (e.g., nn.Linear).
        name_pattern: Optional filter by name pattern.

    Returns:
        List of LayerInfo objects.

    Example:
        >>> all_layers = get_layers(model)
        >>> linear_layers = get_layers(model, layer_type=nn.Linear)
        >>> attention = get_layers(model, name_pattern="attention")
    """
    inspector = MLXInspector(model)

    if layer_type is None and name_pattern is None:
        return inspector.get_layers()

    return inspector.find_layers(layer_type=layer_type, name_pattern=name_pattern)


def get_stats(model: nn.Module) -> ModelStats:
    """
    Get aggregate statistics about a model.

    Args:
        model: The MLX nn.Module to analyze.

    Returns:
        ModelStats object with aggregate information.

    Example:
        >>> stats = get_stats(model)
        >>> print(f"Total: {stats.total_params:,}")
        >>> print(f"Trainable: {stats.trainable_params:,}")
        >>> print(f"Layer types: {stats.layer_type_counts}")
    """
    inspector = MLXInspector(model)
    return inspector.get_stats()


def to_dict(model: nn.Module) -> dict[str, Any]:
    """
    Export model structure to a dictionary.

    Useful for serialization, logging, or further processing.

    Args:
        model: The MLX nn.Module to export.

    Returns:
        Dictionary with model structure and statistics.

    Example:
        >>> import json
        >>> data = to_dict(model)
        >>> json.dump(data, open("model_info.json", "w"))
    """
    inspector = MLXInspector(model)
    return inspector.to_dict()


# Convenience aliases
def tree(model, **kwargs):
    return summary(model, format="tree", **kwargs)
def table(model, **kwargs):
    return summary(model, format="table", **kwargs)


__all__ = [
    "summary",
    "inspect",
    "count_params",
    "get_layers",
    "get_stats",
    "to_dict",
    "tree",
    "table",
    "MLXInspector",
    "LayerInfo",
    "ModelStats",
    "OutputFormat",
    "FormatterOptions",
]
