def is_integer(value):
    """
    Verifica si el valor es un entero o una cadena que representa un entero.
    
    Args:
        value: El valor a verificar (puede ser str, int, etc.)
    
    Returns:
        bool: True si es un entero o cadena de entero, False en caso contrario.
    """
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return value.isdigit() or (value.startswith('-') and value[1:].isdigit())
    return False