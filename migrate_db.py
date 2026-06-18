import sqlite3

from src.adapters.migration_runner import MigrationRunner

def migrate():
    print("Ejecutando migraciones limpias a través de MigrationRunner...")
    runner = MigrationRunner("diabetes.db")
    runner.run()

if __name__ == "__main__":
    migrate()
