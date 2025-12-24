# Installation

## Requirements

- Python 3.11 or higher
- pip or pipx

## Install from PyPI

```bash
pip install django-fastapi-async
```

## Install from Source

```bash
git clone https://github.com/TWFBusiness/fastdjango.git
cd fastdjango
pip install -e .
```

## Development Installation

```bash
git clone https://github.com/TWFBusiness/fastdjango.git
cd fastdjango
pip install -e ".[dev]"
```

## Verify Installation

```bash
fastdjango --help
```

You should see:

```
Usage: fastdjango [OPTIONS] COMMAND [ARGS]...

  FastDjango - Django-like framework built on FastAPI

Options:
  --help  Show this message and exit.

Commands:
  collectstatic    Collect static files into STATIC_ROOT.
  createsuperuser  Create a superuser account.
  makemigrations   Create new migrations based on model changes.
  migrate          Run database migrations.
  runserver        Run the development server.
  shell            Start an interactive Python shell with FastDjango...
  startapp         Create a new FastDjango app.
  startproject     Create a new FastDjango project.
```

## Database Drivers

FastDjango supports multiple databases. Install the appropriate driver:

### SQLite (default)
```bash
pip install aiosqlite
```

### PostgreSQL
```bash
pip install asyncpg
```

### MySQL
```bash
pip install asyncmy
```

## Optional Dependencies

### IPython Shell
```bash
pip install ipython
```

### Argon2 Password Hasher
```bash
pip install argon2-cffi
```
