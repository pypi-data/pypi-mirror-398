"""MLflow experiment tracking wrapper."""

import logging
from typing import Any

import mlflow
import mlflow.sklearn  # type: ignore[reportPrivateImportUsage]
from mlflow.tracking import MlflowClient

# Silence noise
logging.getLogger("matplotlib").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """Standalone MLflow experiment tracking wrapper."""

    def __init__(self, experiment_name: str, tracking_uri: str = "http://127.0.0.1:5000"):
        """Initialize the tracker with experiment name and URI.

        Args:
            experiment_name: Name of the MLflow experiment
            tracking_uri: URI of the MLflow tracking server

        """
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri=tracking_uri)
        self.experiment_name = experiment_name

        try:
            self.experiment = self.client.get_experiment_by_name(experiment_name)
        except Exception as e:
            logger.error(f"Failed to set experiment: {e}")
            raise

    def find_run_by_tags(self, tags: dict[str, str]) -> str | None:
        """Find an existing finished run with matching tags."""
        filter_string = " AND ".join([f"tags.{k} = '{v}'" for k, v in tags.items()])
        if self.experiment:
            runs = self.client.search_runs(
                experiment_ids=[self.experiment.experiment_id],
                filter_string=f"{filter_string} AND attribute.status = 'FINISHED'",
                max_results=1,
            )
            return runs[0].info.run_id if runs else None
        logger.warning("Experiment not found when searching for runs.")
        return None

    def start_run(self, run_name: str, tags: dict[str, str] | None = None) -> str:
        """Start a new MLflow run.

        Args:
            run_name: Name of the run
            tags: Dictionary of tags to attach to the run

        Returns:
            The run ID of the started run

        """
        mlflow.set_experiment(self.experiment_name)
        mlflow.start_run(run_name=run_name, tags=tags or {})
        active_run = mlflow.active_run()
        return active_run.info.run_id if active_run else ""

    def log_params(self, params: dict[str, Any]) -> None:
        """Log parameters to MLflow."""
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log metrics to MLflow."""
        mlflow.log_metrics(metrics, step=step)

    def log_model(self, model: Any, name: str) -> None:
        """Log a scikit-learn model to MLflow."""
        mlflow.sklearn.log_model(sk_model=model, artifact_path=name)  # type: ignore[reportPrivateImportUsage]

    def log_artifact(self, local_path: str, artifact_path: str | None = None) -> None:
        """Log an artifact to MLflow."""
        mlflow.log_artifact(local_path, artifact_path=artifact_path)

    def log_dataset(
        self,
        df: Any,
        name: str,
        context: str = "training",
        source: str | None = None,
        targets: str | None = None,
    ) -> None:
        """Log dataset metadata to MLflow with source and target info."""
        try:
            # MLflow 3.x+ uses source parameter in from_pandas
            dataset = mlflow.data.from_pandas(  # type: ignore[reportPrivateImportUsage]
                df, name=name, source=source, targets=targets
            )
            mlflow.log_input(dataset, context=context)
        except Exception as e:
            logger.warning(f"Failed to log dataset to MLflow: {e}")

    def end_run(self, status: str = "FINISHED") -> None:
        """End the current MLflow run."""
        mlflow.end_run(status=status)
