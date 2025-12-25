"""Tests for the application factory."""

import importlib
import sys
from pathlib import Path

import pytest
from flask import Flask

from zecmf import create_app


def test_create_app_basic() -> None:
    """Test that the basic app creation works."""
    app = create_app(
        config_name="testing",
        api_namespaces=[],
        app_config_module="zecmf.config",
    )

    assert isinstance(app, Flask)
    assert "api" in app.blueprints

    assert app.config["TESTING"] is True
    assert app.config["DEBUG"] is False

    assert "flask-jwt-extended" in app.extensions

    routes = [rule.rule for rule in app.url_map.iter_rules()]
    assert "/api/v1/swagger.json" in routes


def test_dotenv_is_loaded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Ensure values from a .env file are applied at startup."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URI", raising=False)
    # Use a valid dummy public key format for testing
    valid_dummy_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
-----END PUBLIC KEY-----"""
    monkeypatch.setenv("JWT_PUBLIC_KEY", valid_dummy_key)

    (tmp_path / "app_config.py").write_text(
        "from zecmf.config.base import BaseDevelopmentConfig as DevelopmentConfig\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(tmp_path)

    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    original = env_path.read_text(encoding="utf-8") if env_path.exists() else None
    env_path.write_text(
        "SECRET_KEY=dotenv-secret\nDATABASE_URI=sqlite:///dotenv.db\n",
        encoding="utf-8",
    )

    try:
        for mod in ["zecmf", "zecmf.app", "zecmf.config", "zecmf.config.base"]:
            sys.modules.pop(mod, None)

        module = importlib.import_module("zecmf")

        app = module.create_app(
            config_name="development",
            api_namespaces=[],
            app_config_module="app_config",
        )

        assert app.config["SECRET_KEY"] == "dotenv-secret"
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///dotenv.db"
    finally:
        if original is None:
            env_path.unlink()
        else:
            env_path.write_text(original, encoding="utf-8")
