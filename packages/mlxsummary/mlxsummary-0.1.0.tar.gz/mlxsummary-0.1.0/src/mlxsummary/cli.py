"""
Command-line interface for mlxsummary.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import mlx.nn as nn

from .summary import summary


def load_model_from_file(filepath: str) -> nn.Module | None:
    """
    Attempt to load a model from a Python file.

    The file should define a `model` variable or a `get_model()` function.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return None

    if not path.suffix == ".py":
        print(f"Error: Expected a .py file, got: {filepath}", file=sys.stderr)
        return None

    try:
        spec = importlib.util.spec_from_file_location("model_module", path)
        if spec is None or spec.loader is None:
            raise ImportError("Could not load module spec")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Try to get model
        if hasattr(module, "model"):
            model = module.model
            if isinstance(model, nn.Module):
                return model

        if hasattr(module, "get_model"):
            model = module.get_model()
            if isinstance(model, nn.Module):
                return model

        # Look for any nn.Module instance
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, nn.Module):
                return obj

        print(f"Error: No nn.Module found in {filepath}", file=sys.stderr)
        print("Define a 'model' variable or 'get_model()' function.", file=sys.stderr)
        return None

    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        return None


def main(args: list | None = None) -> int:
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        prog="mlxsummary",
        description="Summarize MLX neural network models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Summarize a model defined in a file
  mlxsummary model.py

  # Output as tree
  mlxsummary model.py --format tree

  # JSON output
  mlxsummary model.py --format json -o model_info.json

  # Limit depth
  mlxsummary model.py --max-depth 2

  # Programmatic usage in Python:
  from mlxsummary import summary
  summary(model)
        """,
    )

    parser.add_argument(
        "model_file", nargs="?", help="Python file containing the model to summarize"
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["table", "tree", "json", "markdown", "minimal"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "-o", "--output", metavar="FILE", help="Write output to file instead of stdout"
    )

    parser.add_argument("--max-depth", type=int, metavar="N", help="Maximum layer depth to display")

    parser.add_argument(
        "--max-rows", type=int, metavar="N", help="Maximum number of rows to display"
    )

    parser.add_argument(
        "--width",
        type=int,
        default=125,
        metavar="N",
        help="Output width for table format (default: 100)",
    )

    parser.add_argument("--no-shapes", action="store_true", help="Hide layer shape information")

    parser.add_argument(
        "--no-trainable", action="store_true", help="Hide trainable parameter counts"
    )

    parser.add_argument("--show-frozen", action="store_true", help="Show frozen parameter counts")

    parser.add_argument("--hide-zero", action="store_true", help="Hide layers with zero parameters")

    parser.add_argument("-V", "--version", action="version", version="%(prog)s 0.1.0")

    parser.add_argument("--demo", action="store_true", help="Run with a demo model")

    parsed = parser.parse_args(args)

    # Get the model
    if parsed.demo:
        # Create a demo model
        model = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )
        print("# Demo model: Simple MLP\n", file=sys.stderr)
    elif parsed.model_file:
        model = load_model_from_file(parsed.model_file)
        if model is None:
            return 1
    else:
        parser.print_help()
        return 0

    # Determine output file
    output_file = sys.stdout
    if parsed.output:
        try:
            output_file = open(parsed.output, "w")
        except OSError as e:
            print(f"Error opening output file: {e}", file=sys.stderr)
            return 1

    try:
        # Generate summary
        summary(
            model,
            format=parsed.format,
            show_shapes=not parsed.no_shapes,
            show_trainable=not parsed.no_trainable,
            show_frozen=parsed.show_frozen,
            max_depth=parsed.max_depth,
            max_rows=parsed.max_rows,
            include_zero_param=not parsed.hide_zero,
            width=parsed.width,
            file=output_file,
        )
    finally:
        if output_file is not sys.stdout:
            output_file.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
