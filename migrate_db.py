import sqlite3

def migrate():
    conn = sqlite3.connect("diabetes.db")
    cursor = conn.cursor()
    
    # Enable foreign keys check during the process
    cursor.execute("PRAGMA foreign_keys = OFF") # Turn off temporarily
    
    # 1. Drop ALL legacy views, triggers, and tables first to avoid validation errors during alters
    print("Dropping legacy schema objects first...")
    cursor.execute("DROP VIEW IF EXISTS vista_diabetes_completa")
    cursor.execute("DROP TRIGGER IF EXISTS trg_log_nuevo_registro")
    cursor.execute("DROP TRIGGER IF EXISTS trg_audit_insert")
    cursor.execute("DROP TRIGGER IF EXISTS trg_audit_update")
    cursor.execute("DROP TRIGGER IF EXISTS trg_audit_delete")
    cursor.execute("DROP TABLE IF EXISTS log_actualizaciones")
    
    # 2. Migrate paises
    cursor.execute("PRAGMA table_info(paises)")
    columns = [col[1] for col in cursor.fetchall()]
    if "created_at" not in columns:
        print("Migrating table 'paises'...")
        cursor.execute("ALTER TABLE paises RENAME TO paises_old")
        cursor.execute("""
            CREATE TABLE paises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                codigo TEXT UNIQUE NOT NULL CHECK(length(codigo) = 3),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP NULL
            )
        """)
        cursor.execute("""
            INSERT INTO paises (id, nombre, codigo)
            SELECT id, nombre, codigo FROM paises_old
        """)
        cursor.execute("DROP TABLE paises_old")
        
    # 3. Migrate registros_diabetes
    cursor.execute("PRAGMA table_info(registros_diabetes)")
    columns = [col[1] for col in cursor.fetchall()]
    if "created_at" not in columns:
        print("Migrating table 'registros_diabetes'...")
        cursor.execute("ALTER TABLE registros_diabetes RENAME TO registros_diabetes_old")
        cursor.execute("""
            CREATE TABLE registros_diabetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pais_id INTEGER NOT NULL,
                ano INTEGER NOT NULL CHECK (ano BETWEEN 1900 AND 2100),
                prevalencia REAL NOT NULL CHECK (prevalencia BETWEEN 0.0 AND 100.0),
                poblacion INTEGER NOT NULL CHECK (poblacion > 0),
                gasto_salud_pib REAL NOT NULL DEFAULT 0.0 CHECK (gasto_salud_pib >= 0.0),
                casos_estimados INTEGER NOT NULL CHECK (casos_estimados >= 0),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP NULL,
                FOREIGN KEY (pais_id) REFERENCES paises(id) ON DELETE CASCADE,
                UNIQUE(pais_id, ano)
            )
        """)
        cursor.execute("""
            INSERT INTO registros_diabetes (id, pais_id, ano, prevalencia, poblacion, gasto_salud_pib, casos_estimados)
            SELECT id, pais_id, ano, prevalencia, poblacion, COALESCE(gasto_salud_pib, 0.0), casos_estimados FROM registros_diabetes_old
        """)
        cursor.execute("DROP TABLE registros_diabetes_old")
        
    # Turn foreign keys back on
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 4. Create new log_actualizaciones
    print("Creating new 'log_actualizaciones' table...")
    cursor.execute("""
        CREATE TABLE log_actualizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registro_id INTEGER NOT NULL,
            tipo_operacion TEXT NOT NULL CHECK (tipo_operacion IN ('INSERT', 'UPDATE', 'DELETE')),
            fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (registro_id) REFERENCES registros_diabetes(id) ON DELETE CASCADE
        )
    """)
    
    # 5. Create new Indexes
    print("Creating indexes...")
    cursor.execute("DROP INDEX IF EXISTS idx_paises_nombre")
    cursor.execute("CREATE INDEX idx_paises_nombre ON paises (nombre) WHERE deleted_at IS NULL")
    
    cursor.execute("DROP INDEX IF EXISTS idx_registros_pais_ano")
    cursor.execute("CREATE INDEX idx_registros_pais_ano ON registros_diabetes (pais_id, ano) WHERE deleted_at IS NULL")
    
    cursor.execute("DROP INDEX IF EXISTS idx_log_registro_id")
    cursor.execute("CREATE INDEX idx_log_registro_id ON log_actualizaciones (registro_id)")
    
    cursor.execute("DROP INDEX IF EXISTS idx_log_fecha")
    cursor.execute("CREATE INDEX idx_log_fecha ON log_actualizaciones (fecha)")
    
    # 6. Create new View
    print("Creating new view...")
    cursor.execute("""
        CREATE VIEW vista_diabetes_completa AS
        SELECT 
            r.id AS registro_id,
            p.nombre AS pais,
            p.codigo AS codigo_pais,
            r.ano,
            r.prevalencia,
            r.poblacion,
            r.gasto_salud_pib,
            r.casos_estimados,
            r.created_at,
            r.updated_at
        FROM registros_diabetes r
        JOIN paises p ON r.pais_id = p.id
        WHERE r.deleted_at IS NULL AND p.deleted_at IS NULL
    """)
    
    # 7. Create new Triggers
    print("Creating triggers...")
    cursor.execute("""
        CREATE TRIGGER trg_audit_insert
        AFTER INSERT ON registros_diabetes
        FOR EACH ROW
        BEGIN
            INSERT INTO log_actualizaciones (registro_id, tipo_operacion)
            VALUES (NEW.id, 'INSERT');
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER trg_audit_update
        AFTER UPDATE ON registros_diabetes
        FOR EACH ROW
        WHEN NEW.deleted_at IS NULL AND OLD.deleted_at IS NULL
        BEGIN
            INSERT INTO log_actualizaciones (registro_id, tipo_operacion)
            VALUES (NEW.id, 'UPDATE');
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER trg_audit_delete
        AFTER UPDATE ON registros_diabetes
        FOR EACH ROW
        WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
        BEGIN
            INSERT INTO log_actualizaciones (registro_id, tipo_operacion)
            VALUES (NEW.id, 'DELETE');
        END
    """)
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
