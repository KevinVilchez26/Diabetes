import unittest
import sqlite3
import os
from typing import List

from src.domain.exceptions import DatabaseError, ValidationError
from src.domain.entities import Pais, RegistroDiabetes
from src.domain.value_objects import Year, Prevalence, Population, Percentage, CountryCode
from src.domain.events import DomainEvent, RegistroCreado, PrevalenciaActualizada
from src.ports.event_publisher import EventPublisherPort
from src.ports.api import DiabetesApiPort
from src.ports.uow import UnitOfWorkPort
from src.adapters.api.world_bank_adapter import WorldBankApiAdapter
from src.adapters.persistence.sqlite_repository import (
    SQLitePaisRepository,
    SQLiteRegistroDiabetesRepository,
    SQLiteAuditLogRepository
)
from src.adapters.persistence.sqlite_uow import SQLiteUnitOfWork
from src.application.services import ObtenerDatosDiabetesUseCase, ObtenerLogsAuditoriaUseCase


# Mock del publicador de eventos para probar DIP
class MockEventPublisher(EventPublisherPort):
    def __init__(self):
        self.published_events = []

    def publish(self, event: DomainEvent) -> None:
        self.published_events.append(event)


# Mock del puerto API para probar el Caso de Uso de forma aislada
class MockDiabetesApiAdapter(DiabetesApiPort):
    def __init__(self, data: List[dict]):
        self.data = data

    def fetch_data(self) -> List[dict]:
        return self.data


class TestSOLIDRefactoring(unittest.TestCase):
    def setUp(self):
        # Crear base de datos SQLite en memoria para pruebas
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Crear esquema básico necesario para los repositorios
        self.conn.execute("""
            CREATE TABLE paises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                codigo TEXT UNIQUE NOT NULL
            )
        """)
        self.conn.execute("""
            CREATE TABLE registros_diabetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pais_id INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                prevalencia REAL,
                poblacion INTEGER,
                gasto_salud_pib REAL,
                casos_estimados INTEGER,
                FOREIGN KEY (pais_id) REFERENCES paises(id) ON DELETE CASCADE,
                UNIQUE(pais_id, ano)
            )
        """)
        self.conn.execute("""
            CREATE TABLE log_actualizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registro_id INTEGER,
                pais_codigo TEXT NOT NULL,
                ano INTEGER NOT NULL,
                fecha TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (registro_id) REFERENCES registros_diabetes(id) ON DELETE SET NULL
            )
        """)
        self.conn.commit()

        # Instanciar repositorios
        self.pais_repo = SQLitePaisRepository(self.conn)
        self.registro_repo = SQLiteRegistroDiabetesRepository(self.conn)
        self.audit_repo = SQLiteAuditLogRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_srp_repository_counts(self):
        """Verifica que cada repositorio cuente sus propias filas independientemente (SRP/ISP)."""
        # Insertar algunos datos de prueba
        self.pais_repo.save(Pais(nombre="Nicaragua", codigo=CountryCode("NIC")))
        self.pais_repo.save(Pais(nombre="Costa Rica", codigo=CountryCode("CRI")))
        
        # Guardar registros de diabetes (requiere pais_id existentes)
        nic = self.pais_repo.get_by_codigo(CountryCode("NIC"))
        cri = self.pais_repo.get_by_codigo(CountryCode("CRI"))
        
        self.registro_repo.save(RegistroDiabetes.crear_y_calcular(
            pais_id=nic.id, ano=Year(2021), prevalencia=Prevalence(8.5),
            poblacion=Population(6000000), gasto_salud_pib=Percentage(5.2)
        ))
        self.registro_repo.save(RegistroDiabetes.crear_y_calcular(
            pais_id=cri.id, ano=Year(2021), prevalencia=Prevalence(7.2),
            poblacion=Population(5000000), gasto_salud_pib=Percentage(6.1)
        ))

        # Insertar logs directamente
        self.conn.execute(
            "INSERT INTO log_actualizaciones (registro_id, pais_codigo, ano) VALUES (1, 'NIC', 2021)"
        )
        self.conn.commit()

        # Verificar conteos aislados
        self.assertEqual(self.pais_repo.count(), 2)
        self.assertEqual(self.registro_repo.count(), 2)
        self.assertEqual(self.audit_repo.count(), 1)

    def test_dip_event_publishing(self):
        """Verifica que el caso de uso dependa de EventPublisherPort y lo invoque correctamente (DIP)."""
        # Crear dependencias
        mock_api_data = [
            {
                "pais": "Nicaragua",
                "codigo_pais": "NIC",
                "ano": 2021,
                "prevalencia": 8.5,
                "poblacion": 6000000,
                "gasto_salud_pib": 5.2
            }
        ]
        api = MockDiabetesApiAdapter(mock_api_data)
        
        # Creamos un UOW usando una base de datos temporal
        temp_db = "temp_test_dip.db"
        # Limpiar si existe
        if os.path.exists(temp_db):
            os.remove(temp_db)
            
        uow = SQLiteUnitOfWork(temp_db)
        
        # Ejecutar migraciones en la base de datos temporal
        from src.adapters.persistence.migration_runner import MigrationRunner
        MigrationRunner(temp_db).run()
        
        mock_publisher = MockEventPublisher()
        
        use_case = ObtenerDatosDiabetesUseCase(api, uow, mock_publisher)
        registros, paises, status = use_case.execute()
        
        # Verificar que se publicó el evento de RegistroCreado
        self.assertEqual(len(mock_publisher.published_events), 1)
        event = mock_publisher.published_events[0]
        self.assertTrue(isinstance(event, RegistroCreado))
        self.assertEqual(event.pais_id, paises[0].id)
        self.assertEqual(event.ano, 2021)
        
        # Limpiar
        uow = None
        # Pequeño truco para forzar el cierre de la conexión de SQLite en UOW antes de borrar
        import gc
        gc.collect()
        try:
            if os.path.exists(temp_db):
                os.remove(temp_db)
        except Exception:
            pass

    def test_ocp_world_bank_adapter_config(self):
        """Verifica que la configuración del adaptador API esté abierta para extensión (OCP)."""
        adapter_default = WorldBankApiAdapter()
        self.assertEqual(adapter_default.base_url, "http://api.worldbank.org/v2")
        self.assertEqual(adapter_default.countries, "NIC;CRI;HND;GTM;SLV;PAN")
        
        adapter_custom = WorldBankApiAdapter(
            base_url="https://api.mockbank.org/v3",
            countries="NIC;PAN"
        )
        self.assertEqual(adapter_custom.base_url, "https://api.mockbank.org/v3")
        self.assertEqual(adapter_custom.countries, "NIC;PAN")

    def test_lsp_database_error_translation(self):
        """Verifica que los repositorios capturen sqlite3.Error y lo propaguen como DatabaseError (LSP/DIP)."""
        # Cerrar conexión para forzar un error al operar
        self.conn.close()
        
        with self.assertRaises(DatabaseError):
            self.pais_repo.list_all()
            
        with self.assertRaises(DatabaseError):
            self.registro_repo.list_active()
            
        with self.assertRaises(DatabaseError):
            self.audit_repo.list_logs()

if __name__ == "__main__":
    unittest.main()
