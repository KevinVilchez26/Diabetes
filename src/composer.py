from src.adapters.api.world_bank_adapter import WorldBankApiAdapter
from src.adapters.persistence.sqlite_uow import SQLiteUnitOfWork
from src.application.services import ObtenerDatosDiabetesUseCase, ObtenerLogsAuditoriaUseCase
from src.domain.events import EventDispatcher, RegistroCreado, PrevalenciaActualizada

# Handlers para eventos de dominio
def log_registro_creado(event: RegistroCreado):
    print(f"[DOMINIO EVENTO] Registro Creado - ID: {event.registro_id}, País ID: {event.pais_id}, Año: {event.ano}, Prevalencia: {event.prevalencia}%")

def log_prevalencia_actualizada(event: PrevalenciaActualizada):
    print(f"[DOMINIO EVENTO] Prevalencia Actualizada - ID: {event.registro_id}, País ID: {event.pais_id}, Año: {event.ano}, Nueva Prevalencia: {event.nueva_prevalencia}%")

# Registrar listeners en el despachador de eventos del dominio
EventDispatcher.clear()
EventDispatcher.register(RegistroCreado, log_registro_creado)
EventDispatcher.register(PrevalenciaActualizada, log_prevalencia_actualizada)

def get_obtener_datos_diabetes_use_case(db_path: str = "diabetes.db") -> ObtenerDatosDiabetesUseCase:
    """Fábrica que compone el caso de uso para sincronizar y obtener datos de diabetes con sus dependencias."""
    api = WorldBankApiAdapter()
    uow = SQLiteUnitOfWork(db_path)
    return ObtenerDatosDiabetesUseCase(api, uow)

def get_obtener_logs_auditoria_use_case(db_path: str = "diabetes.db") -> ObtenerLogsAuditoriaUseCase:
    """Fábrica que compone el caso de uso para obtener los logs de auditoría."""
    uow = SQLiteUnitOfWork(db_path)
    return ObtenerLogsAuditoriaUseCase(uow)
