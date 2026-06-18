from dataclasses import dataclass
from typing import Optional
from src.domain.value_objects import Year, Prevalence, Population, Percentage, CountryCode

@dataclass
class Pais:
    nombre: str
    codigo: CountryCode
    id: Optional[int] = None

@dataclass
class RegistroDiabetes:
    pais_id: int
    ano: Year
    prevalencia: Prevalence
    poblacion: Population
    gasto_salud_pib: Percentage
    casos_estimados: int
    id: Optional[int] = None

    @classmethod
    def crear_y_calcular(
        cls,
        pais_id: int,
        ano: Year,
        prevalencia: Prevalence,
        poblacion: Population,
        gasto_salud_pib: Percentage,
        id: Optional[int] = None
    ):
        """Método de fábrica del dominio para calcular los casos estimados automáticamente."""
        casos = int(poblacion.value * (prevalencia.value / 100.0))
        return cls(
            id=id,
            pais_id=pais_id,
            ano=ano,
            prevalencia=prevalencia,
            poblacion=poblacion,
            gasto_salud_pib=gasto_salud_pib,
            casos_estimados=casos
        )

    def actualizar_mediciones(self, prevalencia: Prevalence, poblacion: Population, gasto_salud_pib: Percentage):
        """Actualiza las mediciones recalculando los casos estimados."""
        self.prevalencia = prevalencia
        self.poblacion = poblacion
        self.gasto_salud_pib = gasto_salud_pib
        self.casos_estimados = int(poblacion.value * (prevalencia.value / 100.0))
