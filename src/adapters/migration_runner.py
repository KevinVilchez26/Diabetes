import sqlite3
import os
import glob

class MigrationRunner:
    def __init__(self, db_path: str = "diabetes.db", migrations_dir: str = None):
        self.db_path = db_path
        if migrations_dir is None:
            # Ruta relativa al directorio de persistencia/migraciones
            self.migrations_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "persistence", "migrations"
            )
        else:
            self.migrations_dir = migrations_dir

    def run(self):
        print(f"Buscando migraciones en: {self.migrations_dir}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tabla de control de versiones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


        # Obtener archivos de migración (*.sql)
        migration_files = sorted(glob.glob(os.path.join(self.migrations_dir, "*.sql")))
        
        for file_path in migration_files:
            filename = os.path.basename(file_path)
            try:
                version = int(filename.split("_")[0])
            except ValueError:
                print(f"Nombre de archivo de migración inválido: {filename}, omitiendo...")
                continue

            # Verificar si ya fue aplicada
            cursor.execute("SELECT 1 FROM schema_version WHERE version = ?", (version,))
            if cursor.fetchone():
                continue

            print(f"Aplicando migración {version}: {filename}...")
            with open(file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            try:
                # Ejecutar script
                cursor.executescript(sql_script)
                # Registrar versión aplicada
                cursor.execute(
                    "INSERT INTO schema_version (version, filename) VALUES (?, ?)",
                    (version, filename)
                )
                conn.commit()
                print(f"Migración {version} aplicada con éxito.")
            except Exception as e:
                conn.rollback()
                print(f"Error crítico al aplicar la migración {version}: {e}")
                conn.close()
                raise e

        conn.close()
        print("Base de datos actualizada correctamente.")
