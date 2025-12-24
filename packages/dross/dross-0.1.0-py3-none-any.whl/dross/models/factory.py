"""Model factory pattern for flexible model creation."""

from typing import Optional

from dross.models.base import BaseModel


def get_model(
    model_type: str,
    config: dict,
    registry: Optional[dict[str, type[BaseModel]]] = None,
) -> BaseModel:
    """Get a model instance by type.

    Args:
        model_type: Type of model to instantiate
        config: Configuration dict for the model
        registry: Optional custom model registry. If not provided,
                 returns an error asking user to register models.

    Returns:
        Instantiated model matching model_type

    Raises:
        ValueError: If model_type not found in registry

    """
    if registry is None:
        registry = {}

    if model_type not in registry:
        available = ", ".join(registry.keys()) if registry else "none registered"
        raise ValueError(
            f"Unsupported model type: {model_type}. "
            f"Available: {available}. "
            f"Register models via registry parameter."
        )

    model_class = registry[model_type]
    return model_class(config)
