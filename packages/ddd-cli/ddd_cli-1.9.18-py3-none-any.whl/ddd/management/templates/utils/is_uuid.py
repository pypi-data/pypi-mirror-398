from uuid import uuid4, UUID

def is_uuid(value):
    """
    Verifica si el valor es un UUID válido.

    Args:
        value: El valor a verificar (str o UUID)

    Returns:
        bool: True si es un UUID válido, False en caso contrario.
    """
    if isinstance(value, UUID):
        return True
    if isinstance(value, str):
        try:
            UUID(value)
            return True
        except ValueError:
            return False
    return False