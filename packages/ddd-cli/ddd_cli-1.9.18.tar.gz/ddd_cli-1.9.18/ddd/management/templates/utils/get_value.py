def get_value(objeto, atributo):
    if isinstance(objeto, dict):  # Verifica si es un diccionario
        return objeto.get(atributo, None)  # Devuelve el valor o None si no existe
    elif hasattr(objeto, atributo):  # Verifica si tiene el atributo
        return getattr(objeto, atributo)  # Devuelve el valor del atributo
    else:
        return None  # No es ni dict ni tiene el atributo