"""Common CLI commands for Flask applications."""

import importlib
import json
import os
from pathlib import Path

import click
from flask import Flask, current_app, has_app_context
from flask.cli import with_appcontext
from flask_migrate import init, migrate, upgrade
from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError

from zecmf.extensions.database import db
from zecmf.migrations import setup_migrations


def setup_db_impl() -> None:
    """Implement database setup logic."""
    click.echo("Setting up database...")

    # Get database connection
    inspector = inspect(db.engine)

    # Check if tables already exist
    existing_tables = inspector.get_table_names()

    # Check if migrations directory exists
    app_root = current_app.root_path
    migrations_dir = os.path.join(os.path.dirname(app_root), "migrations")
    migrations_dir_exists = os.path.exists(migrations_dir)
    migrations_versions_dir = os.path.join(migrations_dir, "versions")
    has_migration_versions = (
        os.path.exists(migrations_versions_dir)
        and len(os.listdir(migrations_versions_dir)) > 0
    )

    # Initialize migrations directory if it doesn't exist
    if not migrations_dir_exists:
        click.echo("Initializing migrations directory...")
        init()
        # Create initial migration if needed
        if not existing_tables:
            click.echo("Creating initial migration...")
            migrate(message="Initial migration")

    # Try to apply migrations
    try:
        click.echo("Applying migrations...")
        upgrade()
        click.echo("Migrations applied successfully!")
    except ProgrammingError as e:
        click.echo(f"Migration error: {e!s}")

        # If migrations exist but failed, and we have no tables, create tables directly
        if has_migration_versions and not existing_tables:
            click.echo("Falling back to direct table creation...")
            db.create_all()
            click.echo("Tables created directly.")
        else:
            click.echo(
                "Could not apply migrations. Please check your database configuration."
            )
            raise

    click.echo("Database setup complete!")


def health_check_impl() -> None:
    """Implement health check logic."""
    click.echo("Checking application health...")

    # Check database connection
    try:
        # Use text() to wrap SQL string for proper typing
        db.session.execute(text("SELECT 1"))
        click.echo("Database connection: OK")
    except Exception as e:
        click.echo(f"Database connection: FAILED ({e!s})")
        return

    click.echo("All systems operational!")


def init_migrations_impl(models_module: list[str]) -> None:
    """Implement migrations initialization logic.

    Args:
        models_module: Modules containing models to import (e.g., app.models.user)

    """
    # Determine base directory for migrations (app root if available, else cwd)
    if has_app_context():
        base_dir = os.path.dirname(current_app.root_path)
    else:
        base_dir = os.path.dirname(os.getcwd())
    migrations_dir = os.path.join(base_dir, "migrations")

    # Generate import statements
    model_imports = []
    for module_name in models_module:
        try:
            module = importlib.import_module(module_name)
            # Get model classes from the module
            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(module, attr_name)
                if hasattr(attr, "__tablename__"):
                    model_imports.append(f"from {module_name} import {attr_name}")
        except ImportError:
            click.echo(f"Warning: Could not import module {module_name}")

    # Add import statements for the models
    click.echo(f"Setting up migrations in {migrations_dir}")
    setup_migrations(
        destination_dir=migrations_dir,
        models_import_statements=model_imports if model_imports else None,
    )
    click.echo("Migrations directory initialized successfully.")
    click.echo("\nNext steps:")
    click.echo("1. Review the generated files")
    click.echo("2. Run 'flask db init' to initialize Alembic")
    click.echo(
        "3. Run 'flask db migrate -m \"Initial migration\"' to create your first migration"
    )
    click.echo("4. Run 'flask db upgrade' to apply the migration")


@click.command("setup-db")
@with_appcontext
def setup_db() -> None:
    """Set up database migrations and apply them.

    This command:
    1. Initializes the migrations directory if it doesn't exist
    2. Applies all existing migrations to a fresh database
    3. Creates tables directly if migration fails
    """
    setup_db_impl()


@click.command("health-check")
@with_appcontext
def health_check() -> None:
    """Check the health of the application and its dependencies."""
    health_check_impl()


@click.command("init-migrations")
@click.option(
    "--models-module",
    "-m",
    multiple=True,
    help="Modules containing models to import (format: app.models.user)",
)
def init_migrations(models_module: list[str]) -> None:
    """Initialize migrations directory with templates from the framework.

    This creates a migrations directory with the standard Alembic files,
    configured to work with the application's models.

    Args:
        models_module: Modules containing models to import (e.g., app.models.user)

    """
    init_migrations_impl(models_module)


def extract_swagger_impl(output: str, pretty: bool) -> None:
    """Implement swagger extraction logic.

    Args:
        output: Output file path for swagger.json
        pretty: Whether to format the JSON output

    """
    click.echo("Extracting swagger.json from current application...")

    # Access the API instance directly from Flask extensions
    # ZecMF stores the Flask-RESTX Api instance in app.extensions
    api = current_app.extensions.get("restx/api")

    if api is None:
        click.echo(
            "Error: Flask-RESTX API not found in app extensions",
            err=True,
        )
        click.echo(
            f"Available extensions: {list(current_app.extensions.keys())}",
            err=True,
        )
        raise click.Abort()

    # Get the schema directly without making HTTP requests
    #
    # Flask-RESTX relies on ``url_for`` when generating the schema.  When
    # called outside of an active request context this results in
    # ``RuntimeError: Unable to build URLs outside an active request``.
    #
    # The CLI runs within an application context only, so we temporarily push
    # a request context while accessing ``api.__schema__``.  This mirrors what
    # happens during a real HTTP request and allows ``url_for`` to build URLs
    # without needing ``SERVER_NAME`` to be configured.
    try:
        with current_app.test_request_context():
            swagger_data = api.__schema__
    except Exception as e:
        click.echo(f"Error: Failed to access API schema: {e}", err=True)
        raise click.Abort() from e

    if not swagger_data:
        click.echo("Error: Empty swagger schema returned", err=True)
        raise click.Abort()

    # Write to output file
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(swagger_data, f, indent=2)
        else:
            json.dump(swagger_data, f)

    click.echo(f"Successfully extracted swagger.json to '{output_path}'")
    click.echo(f"API Title: {swagger_data.get('info', {}).get('title', 'Unknown')}")
    click.echo(f"API Version: {swagger_data.get('info', {}).get('version', 'Unknown')}")
    click.echo(f"Number of paths: {len(swagger_data.get('paths', {}))}")


@click.command("extract-swagger")
@click.option(
    "--output",
    "-o",
    default="swagger.json",
    help="Output file path for swagger.json (default: swagger.json)",
)
@click.option(
    "--pretty",
    "-p",
    is_flag=True,
    help="Pretty print the JSON output with indentation",
)
@with_appcontext
def extract_swagger(output: str, pretty: bool) -> None:
    r"""Extract swagger.json from the current Flask application.

    This command extracts the OpenAPI/Swagger specification directly from the
    Flask-RESTX API instance, without making HTTP requests.

    \b
    Examples:
        flask extract-swagger
        flask extract-swagger -o api-spec.json
        flask extract-swagger --output docs/swagger.json --pretty
    """
    extract_swagger_impl(output, pretty)


def register_commands(app: Flask) -> None:
    """Register custom Flask CLI commands.

    Args:
        app: The Flask application.

    """
    app.cli.add_command(setup_db)
    app.cli.add_command(health_check)
    app.cli.add_command(init_migrations)
    app.cli.add_command(extract_swagger)
