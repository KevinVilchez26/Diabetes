import os
from src.adapters.api.world_bank_adapter import WorldBankApiAdapter
from src.adapters.persistence.sqlite_uow import SQLiteUnitOfWork
from src.adapters.persistence.migration_runner import MigrationRunner
from src.application.services import ObtenerDatosDiabetesUseCase, ObtenerLogsAuditoriaUseCase
from src.domain.events import EventDispatcher, RegistroCreado, PrevalenciaActualizada, DomainEvent
from src.ports.event_publisher import EventPublisherPort

# Implementación concreta del puerto del publicador de eventos delegando a EventDispatcher
class EventDispatcherPublisher(EventPublisherPort):
    def publish(self, event: DomainEvent) -> None:
        EventDispatcher.dispatch(event)

# Handlers para eventos de dominio
def log_registro_creado(event: RegistroCreado):
    print(f"[DOMINIO EVENTO] Registro Creado - ID: {event.registro_id}, País ID: {event.pais_id}, Año: {event.ano}, Prevalencia: {event.prevalencia}%")

def log_prevalencia_actualizada(event: PrevalenciaActualizada):
    print(f"[DOMINIO EVENTO] Prevalencia Actualizada - ID: {event.registro_id}, País ID: {event.pais_id}, Año: {event.ano}, Nueva Prevalencia: {event.nueva_prevalencia}%")

# Registrar listeners en el despachador de eventos del dominio
EventDispatcher.clear()
EventDispatcher.register(RegistroCreado, log_registro_creado)
EventDispatcher.register(PrevalenciaActualizada, log_prevalencia_actualizada)

# Estado global para asegurar que las migraciones corran una única vez por base de datos
_migrated_databases = set()

def _ensure_migrations(db_path: str):
    abs_path = os.path.abspath(db_path)
    if abs_path not in _migrated_databases:
        print(f"[COMPOSER] Asegurando migraciones para base de datos en: {abs_path}")
        runner = MigrationRunner(abs_path)
        runner.run()
        _migrated_databases.add(abs_path)

def get_obtener_datos_diabetes_use_case(db_path: str = "diabetes.db") -> ObtenerDatosDiabetesUseCase:
    """Fábrica que compone el caso de uso para sincronizar y obtener datos de diabetes con sus dependencias."""
    _ensure_migrations(db_path)
    api = WorldBankApiAdapter()
    uow = SQLiteUnitOfWork(db_path)
    publisher = EventDispatcherPublisher()
    return ObtenerDatosDiabetesUseCase(api, uow, publisher)

def get_obtener_logs_auditoria_use_case(db_path: str = "diabetes.db") -> ObtenerLogsAuditoriaUseCase:
    """Fábrica que compone el caso de uso para obtener los logs de auditoría."""
    _ensure_migrations(db_path)
    uow = SQLiteUnitOfWork(db_path)
    return ObtenerLogsAuditoriaUseCase(uow)
