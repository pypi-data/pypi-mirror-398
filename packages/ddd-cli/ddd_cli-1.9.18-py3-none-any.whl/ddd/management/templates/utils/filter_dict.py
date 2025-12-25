def clean_dict_of_keys(data: dict, keys=(), exclude_none=False) -> dict:
    """
    Limpia un diccionario eliminando claves específicas o valores None.

    Args:
        data (dict): El diccionario a limpiar.
        keys (list): Lista de claves a eliminar del diccionario.
        exclude_none (bool): Si es True, también elimina pares clave-valor donde el valor es None.

    Returns:
        dict: Un nuevo diccionario sin las claves especificadas.
    """
    return {k: v for k, v in data.items() if k not in keys and (v is not None or not exclude_none)}


def filter_dict_by_keys(data: dict, keys: set, exclude_none=False) -> dict:
    """
    Filtra un diccionario para incluir solo las claves especificadas y valores no None.
    
    Args:
        data (dict): Diccionario de entrada.
        keys (set): Conjunto de claves permitidas.
        exclude_none (bool): Si es True, excluye pares clave-valor donde el valor es None.
        
    Returns:
        dict: Nuevo diccionario con solo las claves permitidas.
    """
    return {k: v for k, v in data.items() if k in keys and (v is not None or not exclude_none)}
