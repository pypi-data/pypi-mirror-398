"""
TUI Admin Dashboard - Mission Control for lite_model

Interactive terminal interface for managing the database.
"""

import os
import sys
import time
from .database import Database
from .migrations import MigrationManager


class TUI:
    """Terminal User Interface"""

    def __init__(self, db_path="db.sqlite"):
        self.db_path = db_path
        self.db = Database(db_path)
        self.db.connect()
        self.migration_manager = MigrationManager(self.db)

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        print("=" * 60)
        print("🚀 lite_model MISSION CONTROL")
        print(f"   Database: {self.db_path}")
        print("=" * 60)

    def print_menu(self):
        print("\n1. 📊 System Overview")
        print("2. 📜 Query Log (Last 10)")
        print("3. 📦 Migrations")
        print("4. 💻 SQL Console")
        print("5. 🚪 Exit")

    def run(self):
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            try:
                choice = input("\nSelect option: ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if choice == "1":
                self.show_overview()
            elif choice == "2":
                self.show_query_log()
            elif choice == "3":
                self.manage_migrations()
            elif choice == "4":
                self.sql_console()
            elif choice in ["5", "q", "exit"]:
                print("\nGoodbye!")
                break
            else:
                input("\nInvalid option. Press Enter to continue...")

    def show_overview(self):
        self.clear_screen()
        self.print_header()
        print("\n📊 SYSTEM OVERVIEW")
        print("-" * 30)

        # Cache Stats
        stats = self.db.get_cache_stats()
        print(f"\n[Cache Performance]")
        print(f"   Hits:      {stats.get('hits', 0)}")
        print(f"   Misses:    {stats.get('misses', 0)}")
        print(f"   Hit Rate:  {stats.get('hit_rate', 0):.1f}%")
        print(f"   Type:      {stats.get('type', 'memory')}")

        # Table Stats
        print(f"\n[Database Stats]")
        cursor = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        print(f"   Tables:    {len(tables)}")

        from .sql_utils import sanitize_identifier, quote_identifier
        for table in tables:
            sanitize_identifier(table)  # Validate identifier
            count = self.db.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}").fetchone()[0]
            print(f"   - {table}: {count} records")

        input("\nPress Enter to return...")

    def show_query_log(self):
        self.clear_screen()
        self.print_header()
        print("\n📜 QUERY LOG (Not implemented in DB yet)")
        print("-" * 30)
        print("To enable query logging, we need to attach a logger to Database.")
        input("\nPress Enter to return...")

    def manage_migrations(self):
        self.clear_screen()
        self.print_header()
        print("\n📦 MIGRATIONS")
        print("-" * 30)

        applied = self.migration_manager.get_applied_migrations()
        print(f"Applied: {len(applied)}")

        # List files
        if not os.path.exists("migrations"):
            print("No migrations directory found.")
        else:
            files = sorted([f for f in os.listdir("migrations") if f.endswith(".json")])
            for f in files:
                mig_id = f.replace(".json", "")
                status = "✓" if mig_id in applied else "Pending"
                print(f"   [{status}] {mig_id}")

        print("\nOptions:")
        print("   a. Apply Pending")
        print("   b. Back")

        choice = input("\nSelect: ").strip().lower()
        if choice == "a":
            self.migration_manager.apply_migrations()
            input("\nDone. Press Enter...")

    def sql_console(self):
        self.clear_screen()
        self.print_header()
        print("\n💻 SQL CONSOLE")
        print("-" * 30)
        print("Type 'exit' to return.")

        while True:
            sql = input("\nSQL> ").strip()
            if sql.lower() in ["exit", "quit"]:
                break
            if not sql:
                continue

            try:
                start = time.time()
                cursor = self.db.execute(sql)
                duration = time.time() - start

                if sql.lower().startswith("select"):
                    rows = cursor.fetchall()
                    print(f"\nResult ({len(rows)} rows, {duration:.3f}s):")
                    if rows:
                        # Print headers
                        headers = rows[0].keys()
                        print(" | ".join(headers))
                        print("-" * (len(headers) * 10))
                        # Print rows (limit 10)
                        for row in rows[:10]:
                            print(" | ".join(str(val) for val in row))
                        if len(rows) > 10:
                            print(f"... and {len(rows)-10} more")
                else:
                    print(f"\nExecuted in {duration:.3f}s")

            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "db.sqlite"
    tui = TUI(path)
    tui.run()
