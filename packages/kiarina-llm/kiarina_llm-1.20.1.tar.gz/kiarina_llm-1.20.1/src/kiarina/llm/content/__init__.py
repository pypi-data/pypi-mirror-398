import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._models.content_limits import ContentLimits
    from ._models.content_metrics import ContentMetrics
    from ._models.content_scale import ContentScale
    from ._operations.calculate_overflow import calculate_overflow

__all__ = [
    # .models
    "ContentLimits",
    "ContentMetrics",
    "ContentScale",
    # .operations
    "calculate_overflow",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # .models
        "ContentLimits": "._models.content_limits",
        "ContentMetrics": "._models.content_metrics",
        "ContentScale": "._models.content_scale",
        # .operations
        "calculate_overflow": "._operations.calculate_overflow",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
