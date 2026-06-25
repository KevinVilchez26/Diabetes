import sqlite3
from typing import List, Optional
from src.ports.repositories import PaisRepository, RegistroDiabetesRepository, AuditLogRepository
from src.domain.entities import Pais, RegistroDiabetes
from src.domain.value_objects import Year, Prevalence, Population, Percentage, CountryCode
from src.domain.exceptions import DatabaseError

class SQLitePaisRepository(PaisRepository):
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def get_by_id(self, id_: int) -> Optional[Pais]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, nombre, codigo 
                FROM paises 
                WHERE id = ?
            """, (id_,))
            row = cursor.fetchone()
            if not row:
                return None
            return Pais(
                id=row[0],
                nombre=row[1],
                codigo=CountryCode(row[2])
            )
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al obtener país por ID: {e}")

    def get_by_codigo(self, codigo: CountryCode) -> Optional[Pais]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, nombre, codigo 
                FROM paises 
                WHERE codigo = ?
            """, (codigo.value,))
            row = cursor.fetchone()
            if not row:
                return None
            return Pais(
                id=row[0],
                nombre=row[1],
                codigo=CountryCode(row[2])
            )
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al obtener país por código: {e}")

    def save(self, pais: Pais) -> None:
        try:
            cursor = self.conn.cursor()
            if pais.id is None:
                cursor.execute("""
                    INSERT INTO paises (nombre, codigo) 
                    VALUES (?, ?)
                """, (pais.nombre, pais.codigo.value))
                pais.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE paises 
                    SET nombre = ?, codigo = ? 
                    WHERE id = ?
                """, (pais.nombre, pais.codigo.value, pais.id))
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al guardar país: {e}")

    def list_all(self) -> List[Pais]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, nombre, codigo 
                FROM paises
            """)
            results = []
            for row in cursor.fetchall():
                results.append(Pais(
                    id=row[0],
                    nombre=row[1],
                    codigo=CountryCode(row[2])
                ))
            return results
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al listar países: {e}")

    def count(self) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM paises")
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al contar países: {e}")


class SQLiteRegistroDiabetesRepository(RegistroDiabetesRepository):
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def get_by_pais_y_ano(self, pais_id: int, ano: Year) -> Optional[RegistroDiabetes]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, pais_id, ano, prevalencia, poblacion, gasto_salud_pib, casos_estimados 
                FROM registros_diabetes 
                WHERE pais_id = ? AND ano = ?
            """, (pais_id, ano.value))
            row = cursor.fetchone()
            if not row:
                return None
            return RegistroDiabetes(
                id=row[0],
                pais_id=row[1],
                ano=Year(row[2]),
                prevalencia=Prevalence(row[3]),
                poblacion=Population(row[4]),
                gasto_salud_pib=Percentage(row[5]),
                casos_estimados=row[6]
            )
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al obtener registro de diabetes: {e}")

    def save(self, registro: RegistroDiabetes) -> None:
        try:
            cursor = self.conn.cursor()
            
            # Verificar si ya existe por el par único (pais_id, ano)
            cursor.execute("""
                SELECT id 
                FROM registros_diabetes 
                WHERE pais_id = ? AND ano = ?
            """, (registro.pais_id, registro.ano.value))
            row = cursor.fetchone()
            
            if row:
                registro.id = row[0]
                cursor.execute("""
                    UPDATE registros_diabetes 
                    SET prevalencia = ?, poblacion = ?, gasto_salud_pib = ?, casos_estimados = ?
                    WHERE id = ?
                """, (
                    registro.prevalencia.value, 
                    registro.poblacion.value, 
                    registro.gasto_salud_pib.value, 
                    registro.casos_estimados, 
                    registro.id
                ))
            else:
                cursor.execute("""
                    INSERT INTO registros_diabetes (pais_id, ano, prevalencia, poblacion, gasto_salud_pib, casos_estimados) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    registro.pais_id, 
                    registro.ano.value, 
                    registro.prevalencia.value, 
                    registro.poblacion.value, 
                    registro.gasto_salud_pib.value, 
                    registro.casos_estimados
                ))
                registro.id = cursor.lastrowid
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al guardar registro de diabetes: {e}")

    def list_active(self) -> List[RegistroDiabetes]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, pais_id, ano, prevalencia, poblacion, gasto_salud_pib, casos_estimados 
                FROM registros_diabetes
            """)
            results = []
            for row in cursor.fetchall():
                results.append(RegistroDiabetes(
                    id=row[0],
                    pais_id=row[1],
                    ano=Year(row[2]),
                    prevalencia=Prevalence(row[3]),
                    poblacion=Population(row[4]),
                    gasto_salud_pib=Percentage(row[5]),
                    casos_estimados=row[6]
                ))
            return results
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al listar registros de diabetes: {e}")

    def count(self) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registros_diabetes")
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al contar registros de diabetes: {e}")


class SQLiteAuditLogRepository(AuditLogRepository):
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def list_logs(self, limit: int = 10) -> List[dict]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    l.id AS log_id,
                    l.registro_id,
                    l.pais_codigo,
                    p.nombre AS pais_nombre,
                    l.ano,
                    l.fecha
                FROM log_actualizaciones l
                LEFT JOIN paises p ON l.pais_codigo = p.codigo
                ORDER BY l.id DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "ID Log": row[0],
                    "ID Registro": row[1],
                    "Código País": row[2],
                    "País": row[3],
                    "Año": row[4],
                    "Fecha/Hora": row[5]
                })
            return results
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al listar logs de auditoría: {e}")

    def count(self) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM log_actualizaciones")
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise DatabaseError(f"Error de base de datos al contar logs de auditoría: {e}")
