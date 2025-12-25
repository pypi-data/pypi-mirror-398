# Zecure Microservices Framework (ZecMF)

A lightweight framework for building microservices in Python with Flask.

## Features

- **Application Factory**: Streamlined Flask application initialization
- **JWT Authentication**: Built-in JWT authentication with both RS256 and HS256 support
- **API Setup**: Simplified REST API initialization with Flask-RESTX
- **Database**: SQLAlchemy and Alembic integration
- **CLI Commands**: Common CLI commands for microservice management
- **Configuration**: Hierarchical configuration system with framework defaults and app-specific overrides

## Installation

```bash
pip install zecmf
```

## Debugging

If you want to include the code in your application for debugging purposes, you can simply mount it:

```
    volumes:
      - ${HOME}/Repos/Zecure/zecmf/src/zecmf:/home/appuser/.local/lib/python3.12/site-packages/zecmf:ro
```
