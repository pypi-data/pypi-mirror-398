"""Tests for CLI commands."""

import contextlib
import json
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

import click
from flask import Flask
from flask_restx import Api, Resource

from zecmf.cli.commands import (
    extract_swagger_impl,
    health_check_impl,
    register_commands,
)


def test_register_commands() -> None:
    """Test that commands are registered with the app."""
    app = Flask("test")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Reset mocks to ensure clean state
    with patch.object(app.cli, "add_command", MagicMock()) as mock_add_command:
        # Execute the function
        register_commands(app)

        # Get the commands that were registered
        called_with = [args[0] for args, _ in mock_add_command.call_args_list]

        # Verify each command was registered by its name
        command_names = [cmd.name for cmd in called_with]
        assert "setup-db" in command_names
        assert "health-check" in command_names
        assert "init-migrations" in command_names
        assert "extract-swagger" in command_names


def test_health_check_success() -> None:
    """Test health check command when all systems are operational."""
    app = Flask("test")
    db_mock = MagicMock()
    db_mock.session.execute.return_value = "Success"

    with (
        patch("zecmf.cli.commands.db", db_mock),
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
    ):
        # Run the implementation function directly instead of the command
        health_check_impl()

        # Verify outputs
        mock_echo.assert_any_call("Checking application health...")
        mock_echo.assert_any_call("Database connection: OK")
        mock_echo.assert_any_call("All systems operational!")


def test_health_check_database_failure() -> None:
    """Test health check command when database connection fails."""
    app = Flask("test")
    db_mock = MagicMock()
    db_mock.session.execute.side_effect = Exception("Database connection error")

    with (
        patch("zecmf.cli.commands.db", db_mock),
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
    ):
        # Run the implementation function directly
        health_check_impl()

        # Verify outputs
        mock_echo.assert_any_call("Checking application health...")
        mock_echo.assert_any_call(
            "Database connection: FAILED (Database connection error)"
        )


def test_extract_swagger_success() -> None:
    """Test extract swagger command with direct API access."""
    app = Flask("test")
    mock_api = MagicMock()
    mock_api.__schema__ = {
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {"/users": {}},
    }
    app.extensions = {"restx/api": mock_api}

    with (
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        extract_swagger_impl("swagger.json", pretty=False)

        # Verify file was written
        mock_file.assert_called_once_with(Path("swagger.json"), "w", encoding="utf-8")
        handle = mock_file()
        written_data = "".join(call[0][0] for call in handle.write.call_args_list)
        assert json.loads(written_data) == mock_api.__schema__

        # Verify success messages
        mock_echo.assert_any_call("Extracting swagger.json from current application...")
        mock_echo.assert_any_call(
            "Successfully extracted swagger.json to 'swagger.json'"
        )
        mock_echo.assert_any_call("API Title: Test API")
        mock_echo.assert_any_call("API Version: 1.0.0")
        mock_echo.assert_any_call("Number of paths: 1")


def test_extract_swagger_with_custom_output() -> None:
    """Test extract swagger command with custom output path."""
    app = Flask("test")
    mock_api = MagicMock()
    mock_api.__schema__ = {
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    app.extensions = {"restx/api": mock_api}

    with (
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        extract_swagger_impl("custom/path/api.json", pretty=False)

        # Verify custom output path
        mock_file.assert_called_once_with(
            Path("custom/path/api.json"), "w", encoding="utf-8"
        )

        # Verify success message with custom path
        mock_echo.assert_any_call(
            "Successfully extracted swagger.json to 'custom/path/api.json'"
        )


def test_extract_swagger_pretty_print() -> None:
    """Test extract swagger command with pretty print option."""
    app = Flask("test")
    mock_api = MagicMock()
    mock_api.__schema__ = {"info": {"title": "API"}, "paths": {}}
    app.extensions = {"restx/api": mock_api}

    with (
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo"),
        patch("builtins.open", mock_open()) as mock_file,
        patch("json.dump") as mock_json_dump,
    ):
        extract_swagger_impl("pretty.json", pretty=True)

        # Verify JSON was dumped with indentation
        # mock_open() creates a context manager, so we need to access the result
        file_handle = mock_file.return_value.__enter__.return_value
        mock_json_dump.assert_called_once_with(
            {"info": {"title": "API"}, "paths": {}},
            file_handle,
            indent=2,
        )


def test_extract_swagger_no_api() -> None:
    """Test extract swagger command when API is not found."""
    app = Flask("test")
    app.extensions = {}  # No API in extensions

    with (
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
        patch.object(click, "Abort", side_effect=click.exceptions.Abort),
        contextlib.suppress(click.exceptions.Abort),
    ):
        extract_swagger_impl("swagger.json", pretty=False)

        # Verify error messages
        mock_echo.assert_any_call(
            "Error: Flask-RESTX API not found in app extensions",
            err=True,
        )
        mock_echo.assert_any_call(
            "Available extensions: []",
            err=True,
        )


def test_extract_swagger_schema_error() -> None:
    """Test extract swagger command when accessing schema fails."""
    app = Flask("test")
    mock_api = MagicMock()
    # Make __schema__ property raise an exception
    type(mock_api).__schema__ = PropertyMock(
        side_effect=RuntimeError("Schema generation failed")
    )
    app.extensions = {"restx/api": mock_api}

    with (
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
        patch.object(click, "Abort", side_effect=click.exceptions.Abort),
        contextlib.suppress(click.exceptions.Abort),
    ):
        extract_swagger_impl("swagger.json", pretty=False)

        # Verify error message
        mock_echo.assert_any_call(
            "Error: Failed to access API schema: Schema generation failed",
            err=True,
        )


def test_extract_swagger_with_real_api() -> None:
    """Integration test using a real Flask-RESTX Api instance."""
    app = Flask("test")
    # Create an actual Api instance to ensure schema generation works
    api = Api(app, title="Test API", version="1.0")
    # Mimic framework behaviour where the Api instance is stored separately
    app.extensions["restx/api"] = api

    @api.route("/ping")
    class PingResource(Resource):  # type: ignore[misc]
        def get(self) -> dict[str, str]:  # pragma: no cover - simple response
            return {"pong": "pong"}

    with (
        patch("zecmf.cli.commands.current_app", app),
        patch("click.echo") as mock_echo,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        extract_swagger_impl("swagger.json", pretty=False)

        # A file should be written with the schema
        mock_file.assert_called_once_with(Path("swagger.json"), "w", encoding="utf-8")
        # The output should report the correct number of paths
        mock_echo.assert_any_call("Number of paths: 1")
