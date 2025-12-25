# infrastructure/exceptions.py

class InfraestructureError(Exception):
    """Excepción base para errores técnicos (base de datos, red, etc)."""
    pass


class RepositoryError(InfraestructureError):
    """Error genérico del repositorio (fallo al leer/escribir)."""
    pass


class ConnectionDataBaseError(InfraestructureError):
    """No se pudo conectar a la base de datos."""
    pass


class TransactionError(InfraestructureError):
    """Error al manejar una transacción."""
    pass


class SerializationError(InfraestructureError):
    """Error al serializar/deserializar datos."""
    pass