"""
Output formatters for model summaries.
"""

from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TextIO

from .inspector import LayerInfo, MLXInspector


class OutputFormat(Enum):
    """Available output formats."""

    TABLE = "table"
    TREE = "tree"
    JSON = "json"
    MARKDOWN = "markdown"
    MINIMAL = "minimal"


@dataclass
class FormatterOptions:
    """Options for controlling formatter output."""

    show_shapes: bool = True
    show_trainable: bool = False
    show_frozen: bool = False
    max_depth: int | None = None
    max_rows: int | None = None
    include_zero_param: bool = True
    width: int = 125
    indent: int = 2
    colorize: bool = False


class BaseFormatter(ABC):
    """Base class for output formatters."""

    def __init__(self, inspector: MLXInspector, options: FormatterOptions | None = None):
        self.inspector = inspector
        self.options = options or FormatterOptions()

    @abstractmethod
    def format(self) -> str:
        """Generate formatted output string."""
        pass

    def write(self, file: TextIO = sys.stdout) -> None:
        """Write formatted output to a file."""
        file.write(self.format())
        file.write("\n")

    def _filter_layers(self, layers: list[LayerInfo]) -> list[LayerInfo]:
        """Apply filtering options to layers."""
        result = []

        for layer in layers:
            # Skip root layer - it's not shown in summaries
            if layer.is_root:
                continue

            # Depth filter
            if self.options.max_depth is not None:
                if layer.depth > self.options.max_depth:
                    continue

            # Zero param filter
            if not self.options.include_zero_param:
                if layer.total_params == 0:
                    continue

            result.append(layer)

            # Max rows
            if self.options.max_rows is not None:
                if len(result) >= self.options.max_rows:
                    break

        return result

    def _format_params(self, count: int) -> str:
        """Format parameter count with commas."""
        return f"{count:,}"

    def _format_shape_info(self, layer: LayerInfo) -> str:
        """Format layer shape information."""
        info = layer.extra_info

        if "in_features" in info:
            return f"({info['in_features']} → {info['out_features']})"
        elif "num_embeddings" in info:
            return f"({info['num_embeddings']} × {info['embedding_dim']})"
        elif "num_heads" in info:
            return f"(heads={info['num_heads']}, dim={info.get('dims', '?')})"
        elif "in_channels" in info:
            return f"({info['in_channels']} → {info['out_channels']}, k={info.get('kernel_size', '?')})"
        elif "normalized_shape" in info:
            return f"({info['normalized_shape']})"
        elif "num_layers" in info:
            return f"({info['num_layers']} layers)"

        return ""


class TableFormatter(BaseFormatter):
    """Format model summary as a table."""

    def format(self) -> str:
        layers = self._filter_layers(self.inspector.get_layers())
        stats = self.inspector.get_stats()
        model_name = type(self.inspector.model).__name__

        # Calculate column widths
        w = self.options.width
        path_width = min(45, w)
        type_width = 20
        param_width = 14
        details_width = 18

        lines = []

        # Header
        lines.append("=" * w)
        lines.append(f" Model Summary: {model_name}")
        lines.append("=" * w)

        # Column headers
        header_parts = [
            f"{'Layer':<{path_width}}",
            f"{'Type':<{type_width}}",
            f"{'Params':>{param_width}}",
        ]
        if self.options.show_shapes:
            header_parts.append(f"{'Details':<{details_width}}")
        if self.options.show_trainable:
            header_parts.append(f"{'Trainable':>{param_width}}")

        lines.append(" ".join(header_parts))
        lines.append("-" * w)

        # Layers
        for layer in layers:
            path = layer.path
            if len(path) > path_width - 2:
                path = path[: path_width - 4] + ".."

            row_parts = [
                f"{path:<{path_width}}",
                f"{layer.layer_type:<{type_width}}",
                f"{self._format_params(layer.total_params):>{param_width}}",
            ]

            if self.options.show_shapes:
                shape_info = self._format_shape_info(layer)
                row_parts.append(f"{shape_info:<{details_width}}")

            if self.options.show_trainable:
                row_parts.append(f"{self._format_params(layer.trainable_params):>{param_width}}")

            lines.append(" ".join(row_parts))

        # Footer
        lines.append("-" * w)
        lines.append(
            f"{'Total Parameters:':<{path_width + type_width + 1}} {self._format_params(stats.total_params):>{param_width}}"
        )

        if self.options.show_trainable:
            lines.append(
                f"{'Trainable Parameters:':<{path_width + type_width + 1}} {self._format_params(stats.trainable_params):>{param_width}}"
            )

        if self.options.show_frozen and stats.frozen_params > 0:
            lines.append(
                f"{'Frozen Parameters:':<{path_width + type_width + 1}} {self._format_params(stats.frozen_params):>{param_width}}"
            )

        lines.append("=" * w)

        return "\n".join(lines)


class TreeFormatter(BaseFormatter):
    """Format model structure as a tree."""

    def format(self) -> str:
        layers = self._filter_layers(self.inspector.get_layers())
        stats = self.inspector.get_stats()
        model_name = type(self.inspector.model).__name__

        lines = []

        # Tree header from stats
        lines.append(f"📦 {model_name} ({self._format_params(stats.total_params)} params)")

        for layer in layers:
            # Build tree prefix
            depth = layer.depth

            # Simple prefix based on depth
            prefix = "│   " * (depth - 1) + "├── "

            # Get layer name (last part of path)
            name = layer.path.split(".")[-1]

            # Format line
            param_str = self._format_params(layer.total_params)
            type_str = layer.layer_type

            if self.options.show_shapes:
                shape = self._format_shape_info(layer)
                if shape:
                    lines.append(f"{prefix}{name}: {type_str} {shape} [{param_str}]")
                else:
                    lines.append(f"{prefix}{name}: {type_str} [{param_str}]")
            else:
                lines.append(f"{prefix}{name}: {type_str} [{param_str}]")

        return "\n".join(lines)


class JsonFormatter(BaseFormatter):
    """Format model info as JSON."""

    def format(self) -> str:
        data = self.inspector.to_dict()

        # Exclude root layer
        data["layers"] = [l for l in data["layers"] if not l.get("is_root", False)]

        # Apply filters
        if self.options.max_depth is not None:
            data["layers"] = [l for l in data["layers"] if l["depth"] <= self.options.max_depth]

        if not self.options.include_zero_param:
            data["layers"] = [l for l in data["layers"] if l["total_params"] > 0]

        return json.dumps(data, indent=self.options.indent)


class MarkdownFormatter(BaseFormatter):
    """Format model summary as Markdown."""

    def format(self) -> str:
        layers = self._filter_layers(self.inspector.get_layers())
        stats = self.inspector.get_stats()
        model_name = type(self.inspector.model).__name__

        lines = []

        # Title
        lines.append(f"# Model Summary: {model_name}")
        lines.append("")

        # Stats section
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total Parameters:** {self._format_params(stats.total_params)}")
        lines.append(f"- **Trainable Parameters:** {self._format_params(stats.trainable_params)}")
        if stats.frozen_params > 0:
            lines.append(f"- **Frozen Parameters:** {self._format_params(stats.frozen_params)}")
        lines.append(f"- **Number of Layers:** {stats.num_layers}")
        lines.append(f"- **Max Depth:** {stats.max_depth}")
        lines.append("")

        # Layer type breakdown
        lines.append("## Layer Types")
        lines.append("")
        lines.append("| Type | Count | Parameters |")
        lines.append("|------|-------|------------|")
        for ltype, count in stats.layer_type_counts.items():
            params = stats.layer_type_params.get(ltype, 0)
            lines.append(f"| {ltype} | {count} | {self._format_params(params)} |")
        lines.append("")

        # Layer table
        lines.append("## Layers")
        lines.append("")

        header = "| Path | Type | Parameters |"
        if self.options.show_shapes:
            header += " Details |"
        lines.append(header)

        sep = "|------|------|------------|"
        if self.options.show_shapes:
            sep += "---------|"
        lines.append(sep)

        for layer in layers:
            row = f"| `{layer.path}` | {layer.layer_type} | {self._format_params(layer.total_params)} |"
            if self.options.show_shapes:
                row += f" {self._format_shape_info(layer)} |"
            lines.append(row)

        return "\n".join(lines)


class MinimalFormatter(BaseFormatter):
    """Minimal one-line format."""

    def format(self) -> str:
        stats = self.inspector.get_stats()
        model_name = type(self.inspector.model).__name__

        parts = [
            f"{model_name}:",
            f"{self._format_params(stats.total_params)} params",
            f"({stats.num_layers} layers)",
        ]

        if stats.frozen_params > 0:
            ratio = stats.trainable_params / stats.total_params * 100
            parts.append(f"[{ratio:.1f}% trainable]")

        return " ".join(parts)


def get_formatter(
    inspector: MLXInspector,
    format: OutputFormat | str = OutputFormat.TABLE,
    options: FormatterOptions | None = None,
) -> BaseFormatter:
    """
    Get a formatter instance for the specified format.

    Args:
        inspector: The MLXInspector instance.
        format: Output format (table, tree, json, markdown, minimal).
        options: Formatter options.

    Returns:
        A formatter instance.
    """
    if isinstance(format, str):
        format = OutputFormat(format.lower())

    formatters = {
        OutputFormat.TABLE: TableFormatter,
        OutputFormat.TREE: TreeFormatter,
        OutputFormat.JSON: JsonFormatter,
        OutputFormat.MARKDOWN: MarkdownFormatter,
        OutputFormat.MINIMAL: MinimalFormatter,
    }

    formatter_class = formatters.get(format, TableFormatter)
    return formatter_class(inspector, options)
