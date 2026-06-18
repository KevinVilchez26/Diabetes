from dataclasses import dataclass
from typing import List, Callable, Dict, Type

@dataclass
class DomainEvent:
    pass

@dataclass
class RegistroCreado(DomainEvent):
    registro_id: int
    pais_id: int
    ano: int
    prevalencia: float

@dataclass
class PrevalenciaActualizada(DomainEvent):
    registro_id: int
    pais_id: int
    ano: int
    nueva_prevalencia: float

@dataclass
class RegistroEliminado(DomainEvent):
    registro_id: int
    pais_id: int
    ano: int

class EventDispatcher:
    _listeners: Dict[Type[DomainEvent], List[Callable]] = {}

    @classmethod
    def clear(cls):
        cls._listeners = {}

    @classmethod
    def register(cls, event_type: Type[DomainEvent], listener: Callable):
        if event_type not in cls._listeners:
            cls._listeners[event_type] = []
        cls._listeners[event_type].append(listener)

    @classmethod
    def dispatch(cls, event: DomainEvent):
        event_type = type(event)
        if event_type in cls._listeners:
            for listener in cls._listeners[event_type]:
                try:
                    listener(event)
                except Exception as e:
                    # En producción se registraría en logs, mantenemos simple
                    print(f"Error en listener de evento {event_type.__name__}: {e}")
