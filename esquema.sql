PRAGMA foreign_keys = ON;

-- Tabla para almacenar los países
CREATE TABLE IF NOT EXISTS paises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    codigo TEXT UNIQUE NOT NULL
);

-- Tabla para almacenar los registros de indicadores anuales por país
CREATE TABLE IF NOT EXISTS registros_diabetes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pais_id INTEGER NOT NULL,
    ano INTEGER NOT NULL,
    prevalencia REAL,
    poblacion INTEGER,
    gasto_salud_pib REAL,
    casos_estimados INTEGER,
    FOREIGN KEY (pais_id) REFERENCES paises(id) ON DELETE CASCADE,
    UNIQUE(pais_id, ano)
);

-- Tabla para auditoría/log de nuevas inserciones
CREATE TABLE IF NOT EXISTS log_actualizaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registro_id INTEGER,
    pais_codigo TEXT NOT NULL,
    ano INTEGER NOT NULL,
    fecha TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (registro_id) REFERENCES registros_diabetes(id) ON DELETE SET NULL
);

-- Índices para optimizar las consultas y uniones frecuentes
CREATE INDEX IF NOT EXISTS idx_paises_nombre ON paises (nombre);
CREATE INDEX IF NOT EXISTS idx_registros_pais_ano ON registros_diabetes (pais_id, ano);

-- Vista que consolida toda la información para facilitar consultas desde la aplicación
CREATE VIEW IF NOT EXISTS vista_diabetes_completa AS
SELECT 
    r.id AS registro_id,
    p.nombre AS pais,
    p.codigo AS codigo_pais,
    r.ano,
    r.prevalencia,
    r.poblacion,
    r.gasto_salud_pib,
    r.casos_estimados
FROM registros_diabetes r
JOIN paises p ON r.pais_id = p.id;

-- Trigger para registrar la auditoría cuando se inserta un nuevo registro
DROP TRIGGER IF EXISTS trg_log_nuevo_registro;
CREATE TRIGGER trg_log_nuevo_registro
AFTER INSERT ON registros_diabetes
FOR EACH ROW
BEGIN
    INSERT INTO log_actualizaciones (registro_id, pais_codigo, ano)
    VALUES (
        NEW.id,
        (SELECT codigo FROM paises WHERE id = NEW.pais_id),
        NEW.ano
    );
END;
