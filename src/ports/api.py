from abc import ABC, abstractmethod
from typing import List, Dict

class DiabetesApiPort(ABC):
    @abstractmethod
    def fetch_data(self) -> List[Dict]:
        """Obtiene de manera remota los datos de los indicadores de diabetes, población y gasto."""
        pass
