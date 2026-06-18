from dataclasses import dataclass
from src.domain.exceptions import ValidationError

@dataclass(frozen=True)
class Year:
    value: int

    def __post_init__(self):
        if not isinstance(self.value, int):
            try:
                object.__setattr__(self, 'value', int(self.value))
            except:
                raise ValidationError("El año debe ser un número entero.")
        if not (1900 <= self.value <= 2100):
            raise ValidationError(f"El año {self.value} está fuera del rango permitido (1900-2100).")

@dataclass(frozen=True)
class Prevalence:
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            try:
                object.__setattr__(self, 'value', float(self.value))
            except:
                raise ValidationError("La prevalencia debe ser un número decimal.")
        if not (0.0 <= self.value <= 100.0):
            raise ValidationError(f"La prevalencia ({self.value}%) debe estar entre 0% y 100%.")

@dataclass(frozen=True)
class Population:
    value: int

    def __post_init__(self):
        if not isinstance(self.value, int):
            try:
                object.__setattr__(self, 'value', int(self.value))
            except:
                raise ValidationError("La población debe ser un número entero.")
        if self.value <= 0:
            raise ValidationError(f"La población ({self.value}) debe ser un entero positivo mayor que cero.")

@dataclass(frozen=True)
class Percentage:
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            try:
                object.__setattr__(self, 'value', float(self.value))
            except:
                raise ValidationError("El porcentaje debe ser un valor decimal.")
        if self.value < 0.0:
            raise ValidationError(f"El porcentaje ({self.value}%) no puede ser negativo.")

@dataclass(frozen=True)
class CountryCode:
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise ValidationError("El código de país debe ser una cadena de texto.")
        val_clean = self.value.strip().upper()
        object.__setattr__(self, 'value', val_clean)
        if len(val_clean) != 3 or not val_clean.isalpha():
            raise ValidationError(f"El código de país '{self.value}' debe constar de exactamente 3 letras (formato ISO-3).")
