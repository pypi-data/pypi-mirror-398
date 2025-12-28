"""
lite-cli - Developer Tools for lite_model

Commands:
  init          Initialize a new lite_model project
  make:model    Generate a new model file
  db:migrate    Run pending migrations
  db:status     Show migration status
"""

import argparse
import os
import sys
from typing import Optional


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="lite_model Developer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init
    parser_init = subparsers.add_parser("init", help="Initialize project")

    # make:model
    parser_make = subparsers.add_parser("make:model", help="Create a new model")
    parser_make.add_argument("name", help="Model name (e.g. User)")

    # db:migrate
    parser_migrate = subparsers.add_parser("db:migrate", help="Run migrations")

    # db:makemigrations
    parser_makemigrations = subparsers.add_parser(
        "db:makemigrations", help="Create new migrations"
    )
    parser_makemigrations.add_argument(
        "-m", "--message", help="Migration message", default="auto"
    )

    args = parser.parse_args()

    if args.command == "init":
        handle_init()
    elif args.command == "make:model":
        handle_make_model(args.name)
    elif args.command == "db:migrate":
        handle_migrate()
    elif args.command == "db:makemigrations":
        handle_makemigrations(args.message)
    else:
        parser.print_help()


def handle_init() -> None:
    """Initialize project structure."""
    if not os.path.exists("models"):
        os.makedirs("models")
        with open("models/__init__.py", "w") as f:
            f.write("# Models package\n")

    if not os.path.exists("migrations"):
        os.makedirs("migrations")

    print("✓ Project initialized")
    print("  - Created models/ directory")
    print("  - Created migrations/ directory")


def handle_make_model(name: str) -> None:
    """Generate model file.
    
    Args:
        name: Model class name
    """
    filename = f"models/{name.lower()}.py"
    if os.path.exists(filename):
        print(f"Error: {filename} already exists")
        return

    content = f"""from lite_model import Model, IntegerField, TextField

class {name}(Model):
    name = TextField()
    created_at = TextField()  # Use DateTimeField in production
"""

    with open(filename, "w") as f:
        f.write(content)

    print(f"✓ Created model: {filename}")


def handle_migrate() -> None:
    """Run pending migrations."""
    # We need to load the app context/DB here.
    # For CLI, we assume a 'db.sqlite' in CWD or config.
    from lite_model import Database, MigrationManager

    db = Database("db.sqlite")
    db.connect()

    try:
        manager = MigrationManager(db)
        manager.apply_migrations()
    finally:
        db.close()


def handle_makemigrations(message: str) -> None:
    """Create migrations.
    
    Args:
        message: Migration message/description
    """
    # We need to load all models to diff them
    # This implies importing everything in 'models/'
    import importlib.util
    import glob

    # Import all models in models/ directory
    model_files = glob.glob("models/*.py")
    for filepath in model_files:
        module_name = os.path.basename(filepath)[:-3]
        if module_name == "__init__":
            continue

        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

    from lite_model import Database, MigrationManager

    db = Database("db.sqlite")
    db.connect()

    try:
        manager = MigrationManager(db)
        manager.create_migration(message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
