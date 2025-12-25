
# domain/exceptions.py

class Entity1Error(Exception):
    """Excepción base para errores relacionados con el dominio Entity1."""
    pass


class Entity1ValueError(Entity1Error):
    """Error de valor en atributos de la entidad Entity1."""
    def __init__(self, detail: str, field: str = "value"):
        self.field = field
        self.detail = detail
        if field == "value":
            super().__init__(f"Value error: {detail}.")
        else:
            super().__init__(f"Field error in '{field}': {detail}.")


class Entity1ValidationError(Entity1Error):
    """Errores de validación de datos antes de guardar el modelo."""
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Validation in Entity1 failed.")

class Entity1AlreadyExistsError(Entity1Error):
    """Cuando se intenta crear una Entity1 que ya existe."""
    def __init__(self, detail: str, field: str = "value"):
        self.field = field        
        self.detail = detail
        super().__init__(f"Entity1 already exists.")

class Entity1NotFoundError(Entity1Error):
    """Cuando se intenta acceder a una Entity1 inexistente."""
    def __init__(self, id):
        self.id = id
        super().__init__(f"Entity1 with ID {id} not found.")

class Entity1OperationNotAllowedError(Entity1Error):
    """Cuando se intenta realizar una operación no permitida."""
    def __init__(self, operation_name: str):
        super().__init__(f"Operation '{operation_name}' not allowed in Entity1.")        


class Entity1PermissionError(Entity1Error):
    """Cuando el usuario no tiene permisos para modificar o acceder."""
    def __init__(self):
        super().__init__("Permission not allowed in Entity1.")      
