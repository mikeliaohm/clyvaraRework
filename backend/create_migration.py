#!/usr/bin/env python3
"""
Helper script to create and manage database migrations using Alembic.

Usage:
    python create_migration.py init        # Create initial migration
    python create_migration.py auto "msg"  # Create auto-generated migration
    python create_migration.py upgrade     # Apply all pending migrations
    python create_migration.py downgrade   # Rollback one migration
"""

import sys
import os
from alembic.config import Config
from alembic import command

def main():
    # Set up Alembic config
    alembic_cfg = Config("alembic.ini")

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]

    if action == "init":
        # Create initial migration from current models
        print("Creating initial migration from database models...")
        command.revision(alembic_cfg, message="initial schema", autogenerate=True)
        print("✓ Initial migration created!")
        print("\nNext steps:")
        print("1. Review the migration file in alembic/versions/")
        print("2. Run: python create_migration.py upgrade")

    elif action == "auto":
        if len(sys.argv) < 3:
            print("Error: Please provide a message for the migration")
            print("Usage: python create_migration.py auto \"your message here\"")
            sys.exit(1)
        message = sys.argv[2]
        print(f"Creating auto-generated migration: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print("✓ Migration created!")

    elif action == "upgrade":
        print("Applying all pending migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database upgraded successfully!")

    elif action == "downgrade":
        print("Rolling back one migration...")
        command.downgrade(alembic_cfg, "-1")
        print("✓ Rolled back one migration")

    elif action == "history":
        print("Migration history:")
        command.history(alembic_cfg)

    elif action == "current":
        print("Current migration version:")
        command.current(alembic_cfg)

    else:
        print(f"Unknown action: {action}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
