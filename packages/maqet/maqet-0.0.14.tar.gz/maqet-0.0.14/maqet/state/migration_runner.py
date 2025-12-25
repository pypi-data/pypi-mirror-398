"""
Migration Runner

Handles database schema migrations for the StateManager.
Responsible for detecting schema version, applying migrations sequentially,
and creating automatic backups before migrations.
"""

import sqlite3
import sys
from typing import TYPE_CHECKING, Callable, Dict

if TYPE_CHECKING:
    from .database_backup import DatabaseBackup

from ..exceptions import MigrationError, StateError
from ..logger import LOG


class MigrationRunner:
    """
    Handles database schema migrations with automatic backup and rollback support.

    This class is responsible for:
    - Detecting current schema version
    - Determining if migrations are needed
    - Creating automatic backups before migrations (via DatabaseBackup)
    - Applying migrations sequentially with transaction safety
    - Providing rollback instructions on failure
    """

    def __init__(
        self,
        get_connection: Callable,
        get_pooled_connection: Callable,
        backup: 'DatabaseBackup',
        migrations: Dict[int, Callable]
    ) -> None:
        """
        Initialize migration runner.

        Args:
            get_connection: Callable that returns a database connection context manager
            get_pooled_connection: Callable that returns a pooled connection context manager
            backup: DatabaseBackup instance for creating backups
            migrations: Dictionary mapping version numbers to migration functions
        """
        self._get_connection = get_connection
        self._get_pooled_connection = get_pooled_connection
        self._backup = backup
        self._migrations = migrations

    def get_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            Current schema version, or 0 if schema_version table doesn't exist
        """
        try:
            with self._get_pooled_connection(readonly=True) as conn:
                result = conn.execute(
                    "SELECT MAX(version) FROM schema_version"
                ).fetchone()
                return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # schema_version table doesn't exist (pre-migration database)
            return 0

    def needs_migration(self) -> bool:
        """
        Check if database needs migration.

        Returns:
            True if there are pending migrations, False otherwise
        """
        current_version = self.get_version()
        target_version = max(self._migrations.keys()) if self._migrations else 1
        return current_version < target_version

    def run_migrations(self) -> None:
        """
        Run all pending database migrations.

        Migrations are applied sequentially from current version to target version.
        Database is automatically backed up before applying migrations.

        Raises:
            StateError: If migration fails
        """
        current_version = self.get_version()
        target_version = max(self._migrations.keys()) if self._migrations else 1

        if current_version >= target_version:
            LOG.debug(
                f"Database schema is up to date (version {current_version})"
            )
            return

        LOG.info(
            f"Migrating database from version {
                current_version} to {target_version}"
        )

        # Backup database before migration
        try:
            backup_path = self._backup.create_auto_backup()
            LOG.info(f"Pre-migration backup created: {backup_path}")
        except Exception as e:
            LOG.error(f"Failed to create backup before migration: {e}")
            raise StateError(
                f"Cannot proceed with migration without backup: {e}"
            )

        # Apply migrations sequentially
        for version in range(current_version + 1, target_version + 1):
            if version in self._migrations:
                try:
                    self._apply_migration(version, self._migrations[version])
                except Exception as e:
                    error_msg = (
                        f"Migration to version {version} failed: {e}\n"
                        f"Database backup is available at: {backup_path}\n"
                        f"To rollback, restore the backup:\n"
                        f"  cp {backup_path} {self._backup.db_path}"
                    )
                    LOG.error(error_msg)
                    raise StateError(error_msg)

        LOG.info(
            f"Database migration completed successfully to version {
                target_version}"
        )

    def auto_migrate(self) -> None:
        """
        Automatically apply pending migrations on startup.

        This method is called during StateManager initialization to ensure
        the database schema is up to date. If migration fails, it exits
        with a user-friendly error message.

        Raises:
            MigrationError: If migration fails (caught and handled with sys.exit)
        """
        try:
            if self.needs_migration():
                LOG.info("Database schema upgrade required. Applying migrations...")
                self._apply_migrations()
                LOG.info("Migration completed successfully.")
        except MigrationError as e:
            LOG.error(f"Migration failed: {e}")
            print("Database migration failed. Your data is safe (backup created).")
            print("To force migration, run: maqet --force-migrate")
            sys.exit(1)

    def _set_version(self, version: int, description: str = "") -> None:
        """
        Set database schema version.

        Args:
            version: Schema version number
            description: Optional description of the schema version
        """
        with self._get_pooled_connection(readonly=False) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO schema_version (version, description, applied_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (version, description),
            )

    def _apply_migration(self, version: int, migration_func: Callable) -> None:
        """
        Apply a single database migration.

        Args:
            version: Target schema version
            migration_func: Migration function to execute

        Raises:
            StateError: If migration fails
        """
        LOG.info(f"Applying migration to version {version}")

        try:
            with self._get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN IMMEDIATE")

                try:
                    # Execute migration function
                    migration_func(conn)

                    # Update schema version
                    conn.execute(
                        """
                        INSERT INTO schema_version (version, description, applied_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        """,
                        (version, f"Migration to version {version}"),
                    )

                    # Commit transaction
                    conn.commit()
                    LOG.info(
                        f"Migration to version {
                            version} completed successfully"
                    )

                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    raise StateError(
                        f"Migration to version {version} failed: {e}"
                    )

        except Exception as e:
            raise StateError(f"Failed to apply migration: {e}")

    def _apply_migrations(self) -> None:
        """
        Apply all pending migrations.

        This is a simplified wrapper around run_migrations() for auto-migration.

        Raises:
            MigrationError: If migration fails
        """
        try:
            self.run_migrations()
        except StateError as e:
            # Convert StateError to MigrationError for consistency
            raise MigrationError(str(e))
