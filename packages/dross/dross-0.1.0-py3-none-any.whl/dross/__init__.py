"""Dross: ML pipeline framework for Kaggle projects.

A reusable framework built on medallion architecture, MLflow tracking,
and Unity Catalog integration.
"""

from dross.data import MedallionPipeline
from dross.models import BaseModel, get_model
from dross.tracking import ExperimentTracker, UCClient
from dross.utilities import TfidfVectorizer

__version__ = "0.1.0"

__all__ = [
    "MedallionPipeline",
    "ExperimentTracker",
    "UCClient",
    "BaseModel",
    "get_model",
    "TfidfVectorizer",
]
