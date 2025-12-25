# utils/mappers.py
import uuid
import json
import decimal
from datetime import datetime, date, time
from uuid import UUID
from decimal import Decimal
from enum import Enum
from datetime import datetime, date
from dataclasses import asdict, fields
from typing import Type, TypeVar, Any
from django.db import models
from django.db.models import JSONField, ManyToManyField, ForeignKey

from ..domain.[[ entity_name.lower() ]]_exceptions import [[ entity_name|capitalize_first ]]ValueError

T = TypeVar("T")

def is_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False

def make_json_safe(value):
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [make_json_safe(v) for v in value]
    elif isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, set):
        return list(value)
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore')
    else:
        return value            

class Mapper:
    
    @staticmethod
    def model_to_entity(model_instance: models.Model, entity_class: Type[T]) -> T:
        """Convierte modelo Django → entidad Dataclass con validación de tipos y manejo especial de campos."""

        if not model_instance:
            raise [[ entity_name|capitalize_first ]]ValueError("Model_instance_cannot_be_None_Cannot_convert_None_to_entity")

        entity_field_names = {f.name for f in fields(entity_class)}

        data = {}
        for field_name in entity_field_names:
            if not hasattr(model_instance, field_name):
                continue
            
            try:
                value = getattr(model_instance, field_name)
            except AttributeError:
                continue
            
            #mostrar el tipo de campo
            field_object = model_instance._meta.get_field(field_name)

            # Manejo especial para diferentes tipos de campo
            if isinstance(value, models.Manager):
                # Para relaciones ManyToMany o reverse FK
                value = list(value.values_list('pk', flat=True)) if value else []

            elif isinstance(value, uuid.UUID):
                # Dejar tal cual; que la entidad lo maneje
                pass

            elif isinstance(value, (datetime, date)):
                # Dejar tal cual; que la entidad lo maneje
                pass

            elif isinstance(value, decimal.Decimal):
                value = float(value)  # o dejar como Decimal si tu entidad lo acepta            

            elif isinstance(value, dict) or isinstance(value, list):
                # JSONField ya devuelve dict/list, dejar intacto
                pass

            elif hasattr(value, 'pk'):
                # Es una relación ForeignKey/OneToOne -> extraer ID
                value = value.pk if value else None
                
            elif isinstance(field_object, (models.FileField, models.ImageField)):
                try:
                    if value and value.name and value.url:
                        value = {"file_name": value.name, "url": value.url} # Esto lanza una excepción si el archivo no existe
                    else:
                        value = None
                except ValueError:
                    value = None
                    
            else:
                # Otros tipos (CharField, IntegerField, BooleanField, etc.) se dejan tal cual
                pass

            # Añadir al diccionario solo si es válido
            data[field_name] = value

        return entity_class(**data)
    
    @staticmethod
    def update_model_from_entity(instance, entity, excluded_fields=None):
        """
        Actualiza una instancia de modelo Django desde una entidad de dominio.
        
        :param instance: Instancia del modelo Django a actualizar.
        :param entity: Entidad de dominio con los nuevos datos.
        :param excluded_fields: Lista de campos a excluir de la actualización.
        :return: Instancia del modelo Django actualizada y un dict con datos ManyToMany para actualizar luego.
        
        características:
        - Ignora campos 'id' y 'uuid'.
        - Maneja ForeignKey (terminan en '_id').
        - Maneja JSONField con serialización segura.
        - Maneja ManyToManyField (devuelve datos para actualizar luego).
        - Actualiza campos normales directamente.
        """
        excluded_fields = excluded_fields or []
        model_fields = {field.name for field in instance._meta.get_fields()}
        many_to_many_data = {}

        for key, value in entity.to_dict().items():
            if ((key is not None) and (key not in excluded_fields)):
                
                if key in model_fields:
                    model_field = instance._meta.get_field(key)
                else:
                    model_field = None

                # id y uuid se ignoran
                if key in ['id', 'uuid']:
                    continue  # no se actualizan identificadores
                
                # ForeignKey (ej: company_id → company)
                elif key.endswith("_id"):
                    setattr(instance, key, value)

                # JSONField
                elif model_field and isinstance(model_field, JSONField):
                    if isinstance(value, dict) and is_json_serializable(make_json_safe(value)):
                        setattr(instance, key, make_json_safe(value))

                # ManyToMany (ej: branches, categories)
                elif model_field and isinstance(model_field, ManyToManyField):
                    # Se actualiza con .set() después de guardar la instancia
                    many_to_many_data[key] = value # Guardar para actualizar luego

                # Campo normal
                else:
                    setattr(instance, key, value)  
                    
        return instance, many_to_many_data       
    
    @staticmethod
    def entity_to_dict(entity_instance: Any) -> dict:
        """Convierte una entidad en un diccionario que contiene solo sus propios campos"""
        # Convertir la entidad a diccionario directamente con asdict (solo los campos de la entidad)
        return asdict(entity_instance)
    
    @staticmethod
    def model_to_dict(model_instance: models.Model) -> dict:
        """
        Convierte un modelo Django a diccionario usando sus campos reales.
        Alternativa segura a asdict().
        """
        data = {}
        for field in model_instance._meta.get_fields():
            try:
                value = getattr(model_instance, field.name)
                
                if isinstance(field, models.ManyToManyField):
                    data[field.name] = list(value.values_list('pk', flat=True))
                elif isinstance(field, models.ForeignKey) and value:
                    data[field.name] = value.pk
                elif isinstance(value, uuid.UUID):
                    data[field.name] = str(value)
                elif isinstance(value, (datetime, date)):
                    data[field.name] = value
                else:
                    data[field.name] = value
            except AttributeError:
                continue  # Algunos campos virtuales pueden no estar disponibles
        return data
    