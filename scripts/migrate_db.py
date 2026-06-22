import os
import sys
import sqlite3

# Añadir el directorio raíz al path de Python para poder importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.adapters.persistence.migration_runner import MigrationRunner

def migrate():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "diabetes.db"))
    print(f"Ejecutando migraciones limpias en {db_path} a través de MigrationRunner...")
    runner = MigrationRunner(db_path)
    runner.run()

if __name__ == "__main__":
    migrate()
