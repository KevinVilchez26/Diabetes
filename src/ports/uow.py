from abc import ABC, abstractmethod
from src.ports.repositories import PaisRepository, RegistroDiabetesRepository, AuditLogRepository

class UnitOfWorkPort(ABC):
    paises: PaisRepository
    registros: RegistroDiabetesRepository
    logs: AuditLogRepository

    @abstractmethod
    def __enter__(self) -> 'UnitOfWorkPort':
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass
