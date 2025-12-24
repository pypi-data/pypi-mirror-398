# Migrations

FastDjango uses Aerich for database migrations with Tortoise ORM.

## Setup

Migrations are configured automatically based on your `DATABASES` setting:

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "asyncpg",  # or aiosqlite, asyncmy
        "NAME": "mydb",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
    }
}
```

## Commands

### Initialize Migrations

```bash
fastdjango migrate --init
```

Creates the migrations directory and initial schema.

### Create Migrations

```bash
fastdjango makemigrations
fastdjango makemigrations --name "add_user_avatar"
```

Generates migration files based on model changes.

### Apply Migrations

```bash
fastdjango migrate
```

Applies all pending migrations.

### Show Migration Status

```bash
fastdjango showmigrations
```

Lists all migrations and their status.

### Rollback

```bash
fastdjango migrate --rollback
fastdjango migrate --rollback 2  # Rollback 2 steps
```

## Programmatic Usage

```python
from fastdjango.db.migrations import (
    makemigrations,
    migrate,
    rollback,
    showmigrations,
)

# Create migrations
created = await makemigrations(name="add_fields")

# Apply migrations
applied = await migrate()

# Rollback one step
rolled_back = await rollback(steps=1)

# Show status
status = await showmigrations()
```

## Migration Files

Migrations are stored in the `migrations/` directory:

```
migrations/
├── models/
│   ├── 0_20240101120000_init.py
│   ├── 1_20240102150000_add_user_avatar.py
│   └── 2_20240103100000_update.py
└── __init__.py
```

Each migration file contains:

```python
from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD COLUMN "avatar" VARCHAR(255);
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "avatar";
    """
```

## Database Support

### SQLite

```python
DATABASES = {
    "default": {
        "ENGINE": "aiosqlite",
        "NAME": "db.sqlite3",
    }
}
```

### PostgreSQL

```python
DATABASES = {
    "default": {
        "ENGINE": "asyncpg",
        "NAME": "mydb",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": 5432,
    }
}
```

### MySQL

```python
DATABASES = {
    "default": {
        "ENGINE": "asyncmy",
        "NAME": "mydb",
        "USER": "root",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": 3306,
    }
}
```

## MigrationExecutor

For advanced usage:

```python
from fastdjango.db.migrations import MigrationExecutor

executor = MigrationExecutor()

# Initialize
await executor.init()

# Create migration
files = await executor.migrate(name="update")

# Apply migrations
applied = await executor.upgrade()

# Rollback
rolled = await executor.downgrade(version=-1)

# Show history
history = await executor.history()

# Show heads
heads = await executor.heads()
```

## MigrationRecorder

Track applied migrations:

```python
from fastdjango.db.migrations import MigrationRecorder

recorder = MigrationRecorder()

# Get applied migrations
applied = await recorder.applied_migrations()

# Record as applied
await recorder.record_applied("0001_initial")

# Record as unapplied
await recorder.record_unapplied("0001_initial")
```

## Best Practices

1. **Always review migrations** before applying
2. **Backup database** before running migrations in production
3. **Test migrations** on a copy of production data
4. **Use descriptive names** for migrations
5. **Keep migrations small** - one logical change per migration
6. **Don't modify applied migrations** - create new ones instead

## Common Issues

### "No changes detected"

- Ensure models are imported in `models/__init__.py`
- Check that models are in `INSTALLED_APPS`

### Migration conflicts

- Delete conflicting migration files
- Re-run `makemigrations`

### Database locked

- Close all database connections
- Restart the application
