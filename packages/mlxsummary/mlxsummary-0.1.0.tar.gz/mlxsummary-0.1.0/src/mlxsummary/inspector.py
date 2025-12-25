"""
Core model inspection functionality for MLX models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import mlx.nn as nn
from mlx.utils import tree_flatten


@dataclass
class LayerInfo:
    """Information about a single layer in the model."""

    path: str
    layer_type: str
    total_params: int
    trainable_params: int
    depth: int = 0
    is_root: bool = False
    extra_info: dict[str, Any] = field(default_factory=dict)

    @property
    def frozen_params(self) -> int:
        """Number of frozen (non-trainable) parameters."""
        return self.total_params - self.trainable_params

    @property
    def is_leaf(self) -> bool:
        """Whether this is a leaf module (no children with params)."""
        return self.extra_info.get("is_leaf", False)

    def __repr__(self) -> str:
        return (
            f"LayerInfo(path='{self.path}', type='{self.layer_type}', params={self.total_params:,})"
        )


@dataclass
class ModelStats:
    """Aggregate statistics about a model."""

    total_params: int
    trainable_params: int
    frozen_params: int
    num_layers: int
    num_leaf_layers: int
    layer_type_counts: dict[str, int]
    layer_type_params: dict[str, int]
    max_depth: int

    @property
    def trainable_ratio(self) -> float:
        """Ratio of trainable to total parameters."""
        if self.total_params == 0:
            return 0.0
        return self.trainable_params / self.total_params

    def __repr__(self) -> str:
        return (
            f"ModelStats(total={self.total_params:,}, "
            f"trainable={self.trainable_params:,}, "
            f"layers={self.num_layers})"
        )


class MLXInspector:
    """
    Inspector for MLX neural network models.

    Provides comprehensive introspection capabilities including:
    - Layer enumeration with full paths
    - Parameter counting (total, trainable, frozen)
    - Layer type analysis
    - Model statistics

    Example:
        >>> model = nn.Linear(10, 5)
        >>> inspector = MLXInspector(model)
        >>> print(inspector.summary())
        >>> layers = inspector.get_layers()
    """

    def __init__(self, model: nn.Module):
        """
        Initialize the inspector with an MLX model.

        Args:
            model: An MLX nn.Module instance to inspect.
        """
        self.model = model
        self._layers_cache: list[LayerInfo] | None = None
        self._stats_cache: ModelStats | None = None

    def _count_params(self, module: nn.Module) -> tuple[int, int]:
        """Count total and trainable parameters in a module."""
        all_params = tree_flatten(module.parameters())
        trainable = tree_flatten(module.trainable_parameters())

        total = sum(v.size for _, v in all_params)
        train = sum(v.size for _, v in trainable)
        return total, train

    def _extract_layer_info(self, module: nn.Module) -> dict[str, Any]:
        """Extract layer-specific metadata."""
        info = {}

        if isinstance(module, nn.Linear):
            info["in_features"] = int(module.weight.shape[1])
            info["out_features"] = int(module.weight.shape[0])
            info["bias"] = hasattr(module, "bias") and module.bias is not None

        elif isinstance(module, nn.Embedding):
            info["num_embeddings"] = int(module.weight.shape[0])
            info["embedding_dim"] = int(module.weight.shape[1])

        elif isinstance(module, (nn.LayerNorm, nn.RMSNorm)):
            info["normalized_shape"] = tuple(module.weight.shape)

        elif isinstance(module, nn.MultiHeadAttention):
            info["dims"] = int(module.query_proj.weight.shape[0])
            info["num_heads"] = int(module.num_heads)

        elif isinstance(module, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
            info["in_channels"] = int(module.weight.shape[-1])
            info["out_channels"] = int(module.weight.shape[0])
            info["kernel_size"] = tuple(module.weight.shape[1:-1])

        elif isinstance(module, nn.BatchNorm):
            if hasattr(module, "weight"):
                info["num_features"] = int(module.weight.shape[0])

        elif isinstance(module, nn.Dropout):
            if hasattr(module, "p"):
                info["p"] = module.p

        elif isinstance(module, nn.Sequential):
            info["num_layers"] = len(module.layers)

        return info

    def _compute_depth(self, path: str) -> int:
        """Compute the depth of a layer from its path."""
        if not path or path == "root":
            return 0
        return path.count(".") + 1

    def _get_ordered_modules(self) -> list[tuple[str, nn.Module, bool]]:
        """
        Get modules in declaration order using children().

        Returns a list of (path, module, is_leaf) tuples in the order
        they were declared in the model.
        """

        def traverse(
            module: nn.Module, prefix: str = ""
        ) -> list[tuple[str, nn.Module, bool]]:
            results = []
            children = module.children()
            has_child_modules = False

            for name, child in children.items():
                child_prefix = f"{prefix}.{name}" if prefix else name

                if isinstance(child, nn.Module):
                    has_child_modules = True
                    results.extend(traverse(child, child_prefix))
                elif isinstance(child, list):
                    for i, item in enumerate(child):
                        if isinstance(item, nn.Module):
                            has_child_modules = True
                            results.extend(traverse(item, f"{child_prefix}.{i}"))
                elif isinstance(child, dict):
                    for k, v in child.items():
                        if isinstance(v, nn.Module):
                            has_child_modules = True
                            results.extend(traverse(v, f"{child_prefix}.{k}"))

            is_leaf = not has_child_modules
            return [(prefix, module, is_leaf)] + results

        return traverse(self.model)

    def get_layers(self, refresh: bool = False) -> list[LayerInfo]:
        """
        Get information about all layers in the model.

        Args:
            refresh: If True, recompute layers even if cached.

        Returns:
            List of LayerInfo objects for each module in declaration order.
        """
        if self._layers_cache is not None and not refresh:
            return self._layers_cache

        layers = []
        ordered_modules = self._get_ordered_modules()

        for path, module, is_leaf in ordered_modules:
            total, trainable = self._count_params(module)
            extra = self._extract_layer_info(module)
            extra["is_leaf"] = is_leaf
            is_root = not path

            layers.append(
                LayerInfo(
                    path=path or "root",
                    layer_type=type(module).__name__,
                    total_params=total,
                    trainable_params=trainable,
                    depth=self._compute_depth(path),
                    is_root=is_root,
                    extra_info=extra,
                )
            )

        self._layers_cache = layers
        return layers

    def get_stats(self, refresh: bool = False) -> ModelStats:
        """
        Get aggregate statistics about the model.

        Args:
            refresh: If True, recompute stats even if cached.

        Returns:
            ModelStats object with aggregate information.
        """
        if self._stats_cache is not None and not refresh:
            return self._stats_cache

        layers = self.get_layers(refresh)

        # Root layer has total counts
        root = layers[0] if layers else None
        total_params = root.total_params if root else 0
        trainable_params = root.trainable_params if root else 0

        # Count by layer type (excluding root)
        type_counts: dict[str, int] = {}
        type_params: dict[str, int] = {}
        num_leaf = 0
        max_depth = 0

        for layer in layers[1:]:  # Skip root
            ltype = layer.layer_type
            type_counts[ltype] = type_counts.get(ltype, 0) + 1
            type_params[ltype] = type_params.get(ltype, 0) + layer.total_params

            if layer.is_leaf:
                num_leaf += 1
            max_depth = max(max_depth, layer.depth)

        # Sort by param count descending
        type_counts = dict(
            sorted(type_counts.items(), key=lambda x: type_params.get(x[0], 0), reverse=True)
        )
        type_params = dict(sorted(type_params.items(), key=lambda x: x[1], reverse=True))

        self._stats_cache = ModelStats(
            total_params=total_params,
            trainable_params=trainable_params,
            frozen_params=total_params - trainable_params,
            num_layers=len(layers) - 1,  # Exclude root
            num_leaf_layers=num_leaf,
            layer_type_counts=type_counts,
            layer_type_params=type_params,
            max_depth=max_depth,
        )

        return self._stats_cache

    def find_layers(
        self,
        layer_type: type[nn.Module] | None = None,
        name_pattern: str | None = None,
        min_params: int | None = None,
        max_params: int | None = None,
        trainable_only: bool = False,
    ) -> list[LayerInfo]:
        """
        Find layers matching specified criteria.

        Args:
            layer_type: Filter by module type (e.g., nn.Linear).
            name_pattern: Filter by path containing this string.
            min_params: Minimum parameter count.
            max_params: Maximum parameter count.
            trainable_only: Only include layers with trainable params.

        Returns:
            List of matching LayerInfo objects.
        """
        layers = self.get_layers()
        results = []

        for layer in layers:
            # Skip root for filtering
            if layer.path == "root":
                continue

            # Type filter
            if layer_type is not None:
                if layer.layer_type != layer_type.__name__:
                    continue

            # Name pattern filter
            if name_pattern is not None:
                if name_pattern not in layer.path:
                    continue

            # Param count filters
            if min_params is not None and layer.total_params < min_params:
                continue
            if max_params is not None and layer.total_params > max_params:
                continue

            # Trainable filter
            if trainable_only and layer.trainable_params == 0:
                continue

            results.append(layer)

        return results

    def get_layer(self, path: str) -> LayerInfo | None:
        """
        Get a specific layer by its path.

        Args:
            path: The dot-notation path to the layer.

        Returns:
            LayerInfo if found, None otherwise.
        """
        for layer in self.get_layers():
            if layer.path == path:
                return layer
        return None

    def get_module(self, path: str) -> nn.Module | None:
        """
        Get the actual module instance by path.

        Args:
            path: The dot-notation path to the layer.

        Returns:
            The nn.Module if found, None otherwise.
        """
        search_path = "" if path == "root" else path
        for mod_path, module, _ in self._get_ordered_modules():
            if mod_path == search_path:
                return module
        return None

    def apply(
        self,
        fn: Callable[[str, nn.Module, LayerInfo], None],
        layer_type: type[nn.Module] | None = None,
    ) -> None:
        """
        Apply a function to each layer in the model.

        Args:
            fn: Function taking (path, module, layer_info) as arguments.
            layer_type: Optional filter to only apply to specific layer types.
        """
        layers = self.get_layers()
        modules_dict = {p: m for p, m, _ in self._get_ordered_modules()}

        for layer in layers:
            path = "" if layer.path == "root" else layer.path
            module = modules_dict.get(path)

            if module is None:
                continue

            if layer_type is not None and not isinstance(module, layer_type):
                continue

            fn(layer.path, module, layer)

    def to_dict(self) -> dict[str, Any]:
        """
        Export model information to a dictionary.

        Returns:
            Dictionary with model structure and statistics.
        """
        layers = self.get_layers()
        stats = self.get_stats()

        return {
            "model_type": type(self.model).__name__,
            "stats": {
                "total_params": stats.total_params,
                "trainable_params": stats.trainable_params,
                "frozen_params": stats.frozen_params,
                "num_layers": stats.num_layers,
                "num_leaf_layers": stats.num_leaf_layers,
                "max_depth": stats.max_depth,
                "layer_type_counts": stats.layer_type_counts,
                "layer_type_params": stats.layer_type_params,
            },
            "layers": [
                {
                    "path": l.path,
                    "type": l.layer_type,
                    "depth": l.depth,
                    "total_params": l.total_params,
                    "trainable_params": l.trainable_params,
                    "is_leaf": l.is_leaf,
                    "is_root": l.is_root,
                    "extra": l.extra_info,
                }
                for l in layers
            ],
        }

    def invalidate_cache(self) -> None:
        """Clear cached layer and stats information."""
        self._layers_cache = None
        self._stats_cache = None

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"MLXInspector({type(self.model).__name__}, "
            f"params={stats.total_params:,}, "
            f"layers={stats.num_layers})"
        )
