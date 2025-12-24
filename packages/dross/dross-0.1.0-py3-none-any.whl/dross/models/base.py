"""Base model interface for modular training."""

from abc import ABC, abstractmethod
from typing import Any


class BaseModel(ABC):
    """Abstract base class for all ML models."""

    def __init__(self, config: Any):
        """Initialize the model with configuration.

        Args:
            config: Model-specific configuration dictionary

        """
        self.config = config
        self.model: Any = None

    @abstractmethod
    def build(self):
        """Initialize the model instance."""
        pass

    def fit(self, X: Any, y: Any):
        """Train the model."""
        if self.model is None:
            self.build()
        self.model.fit(X, y)

    def predict(self, X: Any):
        """Run inference."""
        return self.model.predict(X)

    def predict_proba(self, X: Any):
        """Run probability inference."""
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return None

    @property
    def params(self) -> dict:
        """Return model parameters for tracking."""
        return self.config or {}
