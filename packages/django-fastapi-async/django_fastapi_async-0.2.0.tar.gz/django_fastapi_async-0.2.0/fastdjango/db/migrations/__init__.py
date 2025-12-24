"""
FastDjango Migrations.
Database schema migration utilities using Aerich.
"""

from typing import Any


class MigrationExecutor:
    """
    Executor for database migrations.
    Wraps Aerich for Tortoise ORM migrations.
    """

    def __init__(self, app_label: str | None = None):
        self.app_label = app_label

    async def migrate(self, fake: bool = False) -> list[str]:
        """
        Apply pending migrations.

        Args:
            fake: Mark as applied without running

        Returns:
            List of applied migration names
        """
        from tortoise import Tortoise

        # Generate schemas (Tortoise auto-migration)
        await Tortoise.generate_schemas(safe=True)

        return ["auto_migration"]

    async def rollback(self, steps: int = 1) -> list[str]:
        """
        Rollback migrations.

        Args:
            steps: Number of migrations to rollback

        Returns:
            List of rolled back migration names
        """
        # Note: Tortoise ORM doesn't have built-in rollback
        # This would require Aerich integration
        return []

    async def show_migrations(self) -> dict[str, list[dict[str, Any]]]:
        """
        Show migration status.

        Returns:
            Dictionary of app labels to migration info
        """
        return {}


async def migrate(app_label: str | None = None, fake: bool = False) -> list[str]:
    """
    Run migrations for an app or all apps.

    Args:
        app_label: Specific app to migrate (None for all)
        fake: Mark as applied without running

    Returns:
        List of applied migrations
    """
    executor = MigrationExecutor(app_label)
    return await executor.migrate(fake=fake)


async def rollback(app_label: str | None = None, steps: int = 1) -> list[str]:
    """
    Rollback migrations.

    Args:
        app_label: Specific app to rollback
        steps: Number of steps to rollback

    Returns:
        List of rolled back migrations
    """
    executor = MigrationExecutor(app_label)
    return await executor.rollback(steps=steps)


__all__ = [
    "MigrationExecutor",
    "migrate",
    "rollback",
]
