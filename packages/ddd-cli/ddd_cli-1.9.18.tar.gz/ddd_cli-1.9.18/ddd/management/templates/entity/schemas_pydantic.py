from abc import ABC, abstractmethod
from pydantic import BaseModel, model_validator
from typing import Self, Dict, Any, Optional
from typing import Dict, Any, Optional

class FileData(BaseModel):
    file_name: Optional[str] = None
    url: Optional[str] = None
    
class BaseEntity(BaseModel):
    """
    Entidad del dominio para promotion.
    Representa la lógica de negocio central y las reglas asociadas.
    """   
    
    @abstractmethod
    @model_validator(mode='after')
    def validate(self) -> Self:
        """Valida reglas de negocio (puedes extender esto)"""
        return self
        
    def update(self, data: Dict[str, Any], add_mode: bool = False, exclude_none: bool = False) -> None:
        """
        Actualiza la entidad con nuevos datos, respetando los campos permitidos.
        """
        valid_data = {}

        for key, value in data.items():
            is_updatable = hasattr(self, key) or add_mode
            if is_updatable:
                valid_data[key] = value

        # Crear copia actualizada (Pydantic valida automáticamente)
        updated = self.model_copy(update=valid_data)

        # Reemplazar atributos actuales con todos los valores, incluidos None
        for field, value in updated.model_dump(exclude_none=exclude_none).items():
            setattr(self, field, value)

        self.validate()

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """Convierte a diccionario (compatible con JSON)"""
        return self.model_dump(exclude_none=exclude_none)

    @classmethod    
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseEntity":
        """Crea una instancia desde un diccionario"""
        return cls(**data)
