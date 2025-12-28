#!/usr/bin/env python
"""
CLI tool for lite_model ORM
"""
import argparse
import sys
import os


def shell(db_path):
    """Launch interactive shell with models loaded"""
    try:
        from lite_model import Database
        import code

        db = Database(db_path)
        db.connect()

        banner = f"""
Lite Model Interactive Shell
Database: {db_path}
Available objects: db

Import your models and start querying!
Example:
  >>> from my_app import User
  >>> User.all(db)
"""
        code.interact(banner=banner, local={"db": db})
        db.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def inspect(db_path):
    """Inspect database schema"""
    try:
        from lite_model import Database

        db = Database(db_path)
        db.connect()

        # Get all tables
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\nDatabase: {db_path}")
        print(f"Tables: {len(tables)}\n")

        for table in tables:
            print(f"Table: {table}")
            cursor = db.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            print()

        db.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Lite Model ORM Management Tool", prog="python -m lite_model"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Shell command
    shell_parser = subparsers.add_parser("shell", help="Launch interactive shell")
    shell_parser.add_argument("db_path", help="Path to SQLite database")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect database schema")
    inspect_parser.add_argument("db_path", help="Path to SQLite database")

    args = parser.parse_args()

    if args.command == "shell":
        shell(args.db_path)
    elif args.command == "inspect":
        inspect(args.db_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
