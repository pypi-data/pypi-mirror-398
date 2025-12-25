"""Migrations initialization module for microservices."""

import os
from importlib import resources


def _copy_template_file(src_path: str, dest_path: str) -> None:
    """Copy a template file from src_path to dest_path."""
    with (
        open(src_path, encoding="utf-8") as src_file,
        open(dest_path, "w", encoding="utf-8") as dest_file,
    ):
        dest_file.write(src_file.read())


def _copy_and_customize_env_py(
    src_path: str, dest_path: str, models_import_statements: list[str] | None
) -> None:
    """Copy env.py template and insert model imports if provided."""
    with open(src_path, encoding="utf-8") as src_file:
        env_template = src_file.read()
    if models_import_statements:
        model_imports = "\n".join(models_import_statements)
        env_template = env_template.replace(
            "# <IMPORT_MODELS_PLACEHOLDER>", model_imports
        )
    else:
        env_template = env_template.replace("# <IMPORT_MODELS_PLACEHOLDER>", "")
    with open(dest_path, "w", encoding="utf-8") as dest_file:
        dest_file.write(env_template)


def _ensure_migration_dirs(destination_dir: str) -> None:
    """Ensure the migrations and versions directories exist."""
    os.makedirs(destination_dir, exist_ok=True)
    versions_dir = os.path.join(destination_dir, "versions")
    os.makedirs(versions_dir, exist_ok=True)


def setup_migrations(
    destination_dir: str, models_import_statements: list[str] | None = None
) -> None:
    """Set up the migrations directory for a microservice.

    This function creates the basic structure for Alembic migrations
    by copying template files from the zecmf package.

    Args:
        destination_dir: The directory where migrations will be set up
        models_import_statements: Optional list of import statements for models
            to be included in the env.py file

    """
    _ensure_migration_dirs(destination_dir)
    package_path = resources.files("zecmf.migrations")
    package_path_str = str(package_path)

    _copy_template_file(
        os.path.join(package_path_str, "alembic.ini.template"),
        os.path.join(destination_dir, "alembic.ini"),
    )
    _copy_template_file(
        os.path.join(package_path_str, "script.py.mako"),
        os.path.join(destination_dir, "script.py.mako"),
    )
    _copy_template_file(
        os.path.join(package_path_str, "README.template"),
        os.path.join(destination_dir, "README"),
    )
    _copy_and_customize_env_py(
        os.path.join(package_path_str, "env.py.template"),
        os.path.join(destination_dir, "env.py"),
        models_import_statements,
    )
