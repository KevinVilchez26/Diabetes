from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities import Pais, RegistroDiabetes
from src.domain.value_objects import Year, CountryCode

class PaisRepository(ABC):
    @abstractmethod
    def get_by_id(self, id_: int) -> Optional[Pais]:
        pass

    @abstractmethod
    def get_by_codigo(self, codigo: CountryCode) -> Optional[Pais]:
        pass

    @abstractmethod
    def save(self, pais: Pais) -> None:
        pass

    @abstractmethod
    def list_all(self) -> List[Pais]:
        pass

    @abstractmethod
    def count(self) -> int:
        """Obtiene el número total de países registrados."""
        pass

class RegistroDiabetesRepository(ABC):
    @abstractmethod
    def get_by_pais_y_ano(self, pais_id: int, ano: Year) -> Optional[RegistroDiabetes]:
        pass

    @abstractmethod
    def save(self, registro: RegistroDiabetes) -> None:
        pass

    @abstractmethod
    def list_active(self) -> List[RegistroDiabetes]:
        pass

    @abstractmethod
    def count(self) -> int:
        """Obtiene el número total de registros de diabetes."""
        pass

class AuditLogRepository(ABC):
    @abstractmethod
    def list_logs(self, limit: int = 10) -> List[dict]:
        pass

    @abstractmethod
    def count(self) -> int:
        """Obtiene el número total de eventos en el log de auditoría."""
        pass

