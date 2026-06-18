class DomainError(Exception):
    """Clase base para todas las excepciones del dominio."""
    pass

class ValidationError(DomainError):
    """Excepción lanzada cuando falla una regla de validación de un Value Object o Entidad."""
    pass

class ApiCaidaError(DomainError):
    """Excepción lanzada cuando el adaptador de API externa no puede conectarse o responde erróneamente."""
    pass

class DatosNoEncontradosError(DomainError):
    """Excepción lanzada cuando una consulta a la persistencia no retorna resultados esperados."""
    pass
