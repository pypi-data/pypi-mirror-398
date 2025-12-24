"""Dross command-line interface."""

import logging
from pathlib import Path

import click  # type: ignore[reportPrivateImportUsage]
import yaml

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli():
    """Dross: ML pipeline framework for Kaggle projects.

    A reusable framework built on medallion architecture, MLflow tracking,
    and Unity Catalog integration.
    """
    pass


@cli.command()
@click.option(
    "--config",
    default="kef.yaml",
    type=click.Path(exists=True),
    help="Path to kef.yaml config file",
)
def config(config):
    """Validate project kef.yaml configuration.

    Checks for required keys and structure for dross compatibility.
    """
    try:
        config_path = Path(config)
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        click.echo("🔍 Validating kef.yaml...")

        def get_nested(d: dict, path: str) -> str | None:
            """Get nested value from dict using dot notation."""
            keys = path.split(".")
            val: dict | str | None = d
            for k in keys:
                if isinstance(val, dict):
                    val = val.get(k)
                else:
                    return None
            return str(val) if val else None

        required_keys = [
            ("project.name", "project.name"),
            ("unity_catalog.project_name", "unity_catalog.project_name"),
            ("unity_catalog.schema.bronze", "unity_catalog.schema.bronze"),
            ("unity_catalog.schema.silver", "unity_catalog.schema.silver"),
            ("unity_catalog.schema.gold", "unity_catalog.schema.gold"),
            ("mlflow.experiment_name", "mlflow.experiment_name"),
        ]

        all_valid = True
        for key, path in required_keys:
            value = get_nested(cfg, path)
            if value:
                click.echo(f"  ✅ {key}: {value}")
            else:
                click.echo(f"  ❌ {key}: MISSING")
                all_valid = False

        if all_valid:
            click.echo("\n✅ Configuration is valid!")
        else:
            click.echo("\n❌ Configuration has errors. Please fix missing keys.")
            raise click.Exit(1)  # pyright: ignore[reportCallIssue]

    except FileNotFoundError:
        click.echo(f"❌ Config file not found: {config}")
        raise click.Exit(1)  # pyright: ignore[reportCallIssue]
    except yaml.YAMLError as e:
        click.echo(f"❌ YAML parse error: {e}")
        raise click.Exit(1)  # pyright: ignore[reportCallIssue]
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        raise click.Exit(1)  # pyright: ignore[reportCallIssue]


@cli.command()
def schema():
    """Show expected medallion schema structure.

    Displays the recommended Unity Catalog schema layout for dross projects.
    """
    schema_info = """
📊 Dross Medallion Architecture Schema
=====================================

Unity Catalog Structure:
  catalog/
    ├── <project_name>_bronze/
    │   ├── raw (table)
    │   ├── _ingestion_log
    │   └── _quality_log
    ├── <project_name>_silver/
    │   ├── cleaned (table)
    │   └── features
    └── <project_name>_gold/
        ├── dataset (table)
        └── predictions

Storage (Local/S3):
  <storage_base>/
    ├── bronze/
    │   └── raw/
    │       └── data.parquet
    ├── silver/
    │   └── cleaned/
    │       └── data.parquet
    └── gold/
        └── dataset/
            └── data.parquet

Required in kef.yaml:
  unity_catalog:
    project_name: <your_project>
    schema:
      bronze: <project>_bronze
      silver: <project>_silver
      gold: <project>_gold
    storage_base: file:///path/to/storage

  tables:
    bronze:
      raw: raw
      ingestion_log: _ingestion_log
      quality_log: _quality_log
    silver:
      cleaned: cleaned
      features: features
    gold:
      dataset: dataset
      predictions: predictions
"""
    click.echo(schema_info)


if __name__ == "__main__":
    cli()
