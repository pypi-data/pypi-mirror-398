from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q
from django.forms import ValidationError

# importa las entidades utilizadas aqui
from ..models import [[ entity_name|capitalize_first ]]
from .mappers import Mapper
from ..utils.filter_dict import clean_dict_of_keys
from ..utils.is_integer import is_integer
from ..utils.is_uuid import is_uuid
from ..domain.[[ entity_name.lower() ]]_entity import [[ entity_name|capitalize_first ]]Entity

# importa las excepciones personalizadas
from ..domain.[[ entity_name.lower() ]]_exceptions import (
    [[ entity_name|capitalize_first ]]ValueError,
    [[ entity_name|capitalize_first ]]ValidationError,
    [[ entity_name|capitalize_first ]]AlreadyExistsError,
    [[ entity_name|capitalize_first ]]NotFoundError,
    [[ entity_name|capitalize_first ]]OperationNotAllowedError,
    [[ entity_name|capitalize_first ]]PermissionError
)

# importa las excepciones de repositorio
from .exceptions import (
    ConnectionDataBaseError,
    RepositoryError
)


class [[ entity_name|capitalize_first ]]Repository:
    """
    Repositorio para manejar la persistencia de datos de la entidad: [[ entity_name|decapitalize_first ]].
    
    Este repositorio incluye:
    - Validación de existencia de registros.
    - Control de unicidad.
    - Métodos básicos.
    """

    # Campos de la entidad no persistibles en el repositorio (para lógica de actualización)
    # Los campos no persistibles son aquellos que tienen una forma especial de ser guardados como: photo, password, etc.
    ENTITY_NOT_PERSISTIBLE_FIELDS = {
        'photo', 'password'
    }    

    @staticmethod
    def get_all(filters: Optional[dict] = None) -> List[ [[ entity_name|capitalize_first ]]Entity ]:
        """
        Obtiene todos los registros de la entidad.

        params:
            filters (dict, optional): Filtros a aplicar en la consulta.
        returns: 
            List[ [[ entity_name|capitalize_first ]]Entity ]: Lista de entidades recuperadas.
        raises:
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            ConnectionDataBaseError: Si hay un error al conectar a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).
        """

        try:
            instance_list = [[ entity_name|capitalize_first ]].objects.all()    

            # Aplicar filtros si se proporcionan
            if filters is not None:
                if not isinstance(filters, dict):
                    raise [[ entity_name|capitalize_first ]]ValueError(field="filters", detail="filters must be a dict or None")
                if "nombre" in filters and filters["nombre"].strip():
                    instance_list = instance_list.filter(nombre__icontains=filters["nombre"])      
                    
            # Tener en cuenta los campos reales que se necesitan en el listado
            instance_list = instance_list.only("id", "nombre", "created_at")

            # Convertir a entidades usando el Mapper genérico
            return [Mapper.model_to_entity(instance, [[ entity_name|capitalize_first ]]Entity) for instance in instance_list]        

        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e
        except Exception as e:
            raise RepositoryError(f"Error fetching registers: {str(e)}") from e


    @staticmethod
    def get_by_id(id = None, uuid = None) -> Optional[ [[ entity_name|capitalize_first ]]Entity ]:
        """
        Obtiene un registro por su ID o UUID.
        
        params:
            id: ID del registro a recuperar.
            uuid: UUID del registro a recuperar.
        returns: 
            El entidad encontrada o None si no existe.
        raises:
            [[ entity_name|capitalize_first ]]ValueError: Si el valor de entrada no es válido.        
            [[ entity_name|capitalize_first ]]NotFoundError: Si no existe el registro con el ID dado.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).
        """

        # Validar que el ID sea un entero o el UUID sea un UUID válido
        if id is not None: 
            if not is_integer(id):
                raise [[ entity_name|capitalize_first ]]ValueError(field="id", detail="ID must be integer.")
        elif uuid is not None:
            if not is_uuid(uuid):
                raise [[ entity_name|capitalize_first ]]ValueError(field="uuid", detail="UUID must be valid.")
        else:
            raise [[ entity_name|capitalize_first ]]ValueError(field="id/uuid", detail="Either id or uuid must be provided.")

        try:
            if id is not None:
                instance = [[ entity_name|capitalize_first ]].objects.get(id=id)
            else:
                instance = [[ entity_name|capitalize_first ]].objects.get(uuid=uuid)

            return Mapper.model_to_entity(instance, [[ entity_name|capitalize_first ]]Entity)

        except [[ entity_name|capitalize_first ]].DoesNotExist as e:
            raise [[ entity_name|capitalize_first ]]NotFoundError(id=id) from e
        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e    
        except Exception as e:
            raise RepositoryError(f"Error fetching registers with ID {id}: {str(e)}") from e            
     

    @staticmethod
    def exists_by_field(field_name, value) -> bool:
        """
        Verifica si existe un registro con un valor específico para un campo dado.

        params: 
            field_name: Nombre del campo a buscar.
            value: Valor del campo a verificar.
        returns:
            True si existe un registro con el valor dado, False en caso contrario.
        raises:
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).
        """
        
        # Lista de campos en los que se permite verificar existencia
        ALLOWED_FIELDS = ['id', 'uuid', 'nombre', 'email', 'ruc', 'codigo']  # define según tu entidad
        
        if field_name not in ALLOWED_FIELDS:
            raise [[ entity_name|capitalize_first ]]ValueError(field=field_name, detail=f"El campo '{field_name}' no es válido para verificar existencia.")

        try:
            return [[ entity_name|capitalize_first ]].objects.filter(**{field_name: value}).exists()

        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e
        except Exception as e:
            raise RepositoryError(f"Error verifying field {field_name} with value {value}: {str(e)}") from e            


    @staticmethod
    def count_all(filters: Optional[dict] = None) -> int:
        """
        Cuenta registros que cumplen con ciertas condiciones.

        params: 
            filters: Condiciones de filtro como clave-valor.
        returns:
            Número de registros que cumplen las condiciones.
        raises: 
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.       
            RepositoryError: Si ocurre un error inesperado (interno del sistema). 
        """     

        try:
            instance_list = [[ entity_name|capitalize_first ]].objects.all()    

            # Aplicar filtros si se proporcionan
            if filters is not None:
                if not isinstance(filters, dict):
                    raise [[ entity_name|capitalize_first ]]ValueError(field="filters", detail="filters must be dict or None")               
                if "nombre" in filters and filters["nombre"].strip():
                    instance_list = instance_list.filter(nombre__icontains=filters["nombre"])            

            return instance_list.count()            

        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e            
        except Exception as e:
            raise RepositoryError(f"Error counting registers: {str(e)}") from e


    @staticmethod
    def create(entity: [[ entity_name|capitalize_first ]]Entity, external_id: Optional[int], externals: Optional[List[int]], adicionalData=None) -> [[ entity_name|capitalize_first ]]Entity:
        """
        Crea un nuevo registro.

        params: 
            entity: Entidad con los datos necesarios para crear el registro.
            external_id: ID del padre si es necesario (opcional).
            externals: Lista de IDs de entidades relacionadas (opcional).
            adicionalData: Datos adicionales a incluir en la creación.
        returns: 
            La entidad creada.
        raises:
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            [[ entity_name|capitalize_first ]]ValidationError: Si los datos no son válidos.
            [[ entity_name|capitalize_first ]]AlreadyExistsError: Si ya existe un registro con el mismo nombre.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.   
            RepositoryError: Si ocurre un error inesperado (interno del sistema).     
        """

        # Validar la entidad de entrada
        if not entity or not hasattr(entity, "to_dict"):
            raise [[ entity_name|capitalize_first ]]ValueError(field="[[ entity_name|capitalize_first ]]", detail="Entity null or without methond 'to_dict'")

        try:
            # Crear el registro a partir de los campos presentes en la 'entity'
            instance = [[ entity_name|capitalize_first ]]()
            Mapper.update_model_from_entity(instance, entity, excluded_fields=[[ entity_name|capitalize_first ]]Repository.ENTITY_NOT_PERSISTIBLE_FIELDS) 

            with transaction.atomic():
                # Asegurar que todas las operaciones se realicen en una transacción
                # Esto garantiza que si algo falla, no se guarden cambios parciales               

                # Si se proporciona un ID de otra entidad, actualizarlo
                # django crea el campo 'external_id' automáticamente si la relación es ForeignKey => otherEntity
                if external_id is not None:
                    instance.external_id = external_id

                # Si adicionalData, agregar datos adicionales que no sean relaciones
                if adicionalData:
                    # Aquí puedes agregar lógica para manejar datos adicionales específicos
                    # Por ejemplo, guardar una foto, un password, o cualquier otro campo especial
                    pass

                # Validar y guardar
                instance.full_clean()  # Validaciones del modelo
                instance.save()

                # Si se proporcionan IDs de entidades relacionadas, agregarlos
                if externals is not None:
                    # Asignar directamente los IDs
                    instance.externals.set(externals)                

        except (TypeError, ValueError) as e:
            raise [[ entity_name|capitalize_first ]]ValueError(field="data", detail=f"Error in the data structure: {str(e)}") from e
        except ValidationError as e:
            raise [[ entity_name|capitalize_first ]]ValidationError(f"Validation error: {e.message_dict}") from e
        except IntegrityError as e:
            if 'duplicate' in str(e).lower() or 'unique constraint' in str(e).lower():
                raise [[ entity_name|capitalize_first ]]AlreadyExistsError(field='attributeName', detail=instance.attributeName)  # Ajusta según el campo único
            # Otro error de integridad → regla de negocio?
            raise [[ entity_name|capitalize_first ]]ValidationError({"integrity": "Duplicated or inconsistent data"})            
        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e
        except Exception as e:
            raise RepositoryError(f"Error creating register: {str(e)}") from e
        
        return Mapper.model_to_entity(instance, [[ entity_name|capitalize_first ]]Entity)


    @staticmethod
    def update(entity: [[ entity_name|capitalize_first ]]Entity, external_id: Optional[int], externals: Optional[List[int]], adicionalData=None) -> [[ entity_name|capitalize_first ]]Entity:
        """
        Guarda los cambios en una entidad existente.

        params: 
            entity: Entidad con los datos a actualizar (debe traer el id en los campos).
            external_id: ID del padre si es necesario (opcional).
            externals: Lista de IDs de entidades relacionadas (opcional).
            adicionalData: Datos adicionales a incluir en la actualización.
        returns:
            La entidad guardada.
        raises: 
            [[ entity_name|capitalize_first ]]NotFoundError: Si no existe el registro con el ID dado.
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            [[ entity_name|capitalize_first ]]ValidationError: Si los datos no son válidos.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.   
            RepositoryError: Si ocurre un error inesperado (interno del sistema).     
        """    

        # Validar la entidad de entrada
        if not entity or not hasattr(entity, "to_dict"):
            raise [[ entity_name|capitalize_first ]]ValueError(field="[[ entity_name|capitalize_first ]]", detail="Entity null or without method 'to_dict'")

        # Validar que tenga el id o uuid
        if not entity.id and not entity.uuid:
            raise [[ entity_name|capitalize_first ]]ValueError(field="id/uuid", detail="The id or uuid field is required")

        # validar el id
        if not entity.id or not is_integer(entity.id):
            raise [[ entity_name|capitalize_first ]]ValueError(field="id", detail="Id must be integer.")

        # validar el uuid
        if entity.uuid and not is_uuid(entity.uuid):
            raise [[ entity_name|capitalize_first ]]ValueError(field="uuid", detail="UUID must be valid.")

        try:
            if entity.id:
                instance = [[ entity_name|capitalize_first ]].objects.get(id=entity.id)
            else:
                instance = [[ entity_name|capitalize_first ]].objects.get(uuid=entity.uuid)

            with transaction.atomic():
                # Asegurar que todas las operaciones se realicen en una transacción
                # Esto garantiza que si algo falla, no se guarden cambios parciales     
                
                # Actualizar cada campo de la entidad en el modelo
                Mapper.update_model_from_entity(instance, entity, excluded_fields=[[ entity_name|capitalize_first ]]Repository.ENTITY_NOT_PERSISTIBLE_FIELDS)              

                # Si se proporciona un ID de otra entidad, actualizarlo
                if external_id is not None:
                    instance.external_id = external_id

                # Si adicionalData, agregar datos adicionales que no sean relaciones
                if adicionalData:
                    # Aquí puedes agregar lógica para manejar datos adicionales específicos
                    # Por ejemplo, guardar una foto, un password, o cualquier otro campo especial
                    pass

                instance.full_clean()  # Validaciones del modelo Django
                instance.save() 

                # Si se proporcionan IDs de entidades relacionadas, actualizarlos
                if externals is not None:
                    # Asignar directamente los IDs
                    instance.externals.set(externals)                
            
            # Convertir el modelo actualizado de vuelta a una entidad
            return Mapper.model_to_entity(instance, [[ entity_name|capitalize_first ]]Entity)

        except [[ entity_name|capitalize_first ]].DoesNotExist as e:
            raise [[ entity_name|capitalize_first ]]NotFoundError(id=entity.id) from e
        except (TypeError, ValueError) as e:
            raise [[ entity_name|capitalize_first ]]ValueError(field="data", detail=f"Error inthe data structure: {str(e)}") from e
        except ValidationError as e:
            raise [[ entity_name|capitalize_first ]]ValidationError(f"Validation error: {e.message_dict}") from e
        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e            
        except Exception as e:
            raise RepositoryError(f"Error updating register: {str(e)}") from e


    @staticmethod
    def delete(id=None, uuid=None) -> bool:
        """
        Elimina un registro por su ID o UUID.

        params: 
            id: ID del registro a eliminar.
            uuid: UUID del registro a eliminar.
        raises: 
            [[ entity_name|capitalize_first ]]NotFoundError: Si no existe el registro con el ID dado.
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            [[ entity_name|capitalize_first ]]ValidationError: Si los datos no son válidos
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.      
            RepositoryError: Si ocurre un error inesperado (interno del sistema).  
        returns: 
            True si la eliminación fue exitosa
        """

        # Validar que haya un id o uuid
        if id is None and uuid is None:
            raise [[ entity_name|capitalize_first ]]ValueError(field="id/uuid", detail="The id or uuid field is required")

        # validar el id
        if id is not None and not is_integer(id):
            raise [[ entity_name|capitalize_first ]]ValueError(field="id", detail="El ID debe ser un entero.")

        # validar el uuid
        if uuid is not None and not is_uuid(uuid):
            raise [[ entity_name|capitalize_first ]]ValueError(field="uuid", detail="El UUID debe ser válido.")

        try:
            if id is not None:
                instance = [[ entity_name|capitalize_first ]].objects.get(id=id)
            else:
                instance = [[ entity_name|capitalize_first ]].objects.get(uuid=uuid)
    
            instance.delete()
            return True

        except [[ entity_name|capitalize_first ]].DoesNotExist as e:
            raise [[ entity_name|capitalize_first ]]NotFoundError(id=id) from e
        except ValidationError as e:
            raise [[ entity_name|capitalize_first ]]ValidationError(f"Validation error occurred: {e.message_dict}") from e
        except DatabaseError as e:
            raise ConnectionDataBaseError("Data base access error") from e            
        except Exception as e:
            raise RepositoryError(f"Error deleting register: {str(e)}") from e


'''
En Django ORM los campos de relación se definen como ForeignKey, ManyToManyField o OneToOneField.
Para la traduccion de relaciones entre entidades, se pueden utilizar los siguientes campos:

- `external_id`: 
    Para relaciones de clave externa (ForeignKey) o uno a uno (OneToOneField)
        ej: external = models.ForeignKey(OtherEntity, on_delete=models.CASCADE, related_name='related_entities')
        o    ej: external = models.OneToOneField(OtherEntity, on_delete=models.CASCADE, related_name='related_entity')
            
    el model de Django crea automáticamente el campo `external_id` este campo es accesible como un atributo de la entidad.

- `external_uuid`: Para relaciones basadas en un UUID adicional aparte del ID.
        ej: external = models.UUIDField(default=uuid.uuid4, editable=False)
     es necesario definir en el model de Django una propiedad 'external_uuid' que retorne el UUID relacionado.
    @property
    def external_uuid(self):
        return str(self.external.uuid) if self.external else None

- `externals`: Para relaciones de muchos a muchos (ManyToManyField).
    Para relaciones de muchos a muchos:
        ej: externals = models.ManyToManyField(OtherEntity, related_name='related_entities')

- `externals_uuids`: Para relaciones de muchos a muchos basadas en UUID adicional aparte del ID.
        ej: externals = models.ManyToManyField(OtherEntity, related_name='related_entities')
    es necesario definir en el model de Django una propiedad 'external_uuids' que retorne una lista de UUIDs relacionados.
    @property
    def externals_uuids(self):
        return list(self.externals.values_list('uuid', flat=True))
'''

'''
### 💡 ¿Por qué ir más allá de los repositorios básicos?
Este repositorio ya implementa una base sólida para DDD en Django: 
mapeo de entidades, validaciones, manejo de relaciones (`external_id`, `externals`) y encapsulación del ORM.  
Sin embargo, a medida que el dominio crezca, 
métodos como `get_all()` o `create()` pueden volverse insuficientes o ineficientes.

En DDD, el repositorio debe hablar el **lenguaje del negocio**, no solo ofrecer operaciones CRUD genéricas.  
Por eso, es valioso **enriquecerlo estratégicamente**, manteniendo la coherencia con esta plantilla.

### 🚀 Cómo enriquecer este repositorio (sin romper su diseño actual)
#### 1. 🗣️ **Métodos específicos orientados al dominio**
    En lugar de exponer solo filtros genéricos por `nombre`, puedes agregar métodos que expresen reglas de negocio:
        @staticmethod
        def get_activos():
            return [[ entity_name|capitalize_first ]].objects.filter(estado='activo')

        @staticmethod
        def find_by_slug(slug: str) -> Optional[[ entity_name|capitalize_first ]]Entity:
            try:
                instance = [[ entity_name|capitalize_first ]].objects.get(slug=slug)
                return Mapper.model_to_entity(instance, [[ entity_name|capitalize_first ]]Entity)
            except [[ entity_name|capitalize_first ]].DoesNotExist:
                return None

    Estos métodos se integran naturalmente con `get_by_id()` y `get_all()`, y evitan que la lógica de negocio se repita en servicios.

#### 2. 🔍 **QuerySets y Managers personalizados**
    Puedes encapsular lógica común (como filtros por estado o relaciones) en un `Manager` personalizado:
        class [[ entity_name|capitalize_first ]]Manager(models.Manager):
            def activos(self):
                return self.filter(estado='activo')
            def con_relacion(self):
                return self.select_related('external').prefetch_related('externals')

        class [[ entity_name|capitalize_first ]](models.Model):
            ...
            objects = [[ entity_name|capitalize_first ]]Manager()

    Luego, en el repositorio:
        @staticmethod
        def get_all(filters=None):
            instance_list = [[ entity_name|capitalize_first ]].objects.activos()  # Usa tu Manager
            if filters and "nombre" in filters:
                instance_list = instance_list.filter(nombre__icontains=filters["nombre"])
            return [Mapper.model_to_entity(inst, [[ entity_name|capitalize_first ]]Entity) for inst in instance_list]

        @staticmethod
        def get_all_with_relations():
            instance_list = [[ entity_name|capitalize_first ]].objects.activos().con_relacion() # Usa tu Manager
            if filters:
                instance_list = instance_list.filter(nombre__icontains=filters["nombre"])
            return [Mapper.model_to_entity(inst, [[ entity_name|capitalize_first ]]Entity) for inst in instance_list]

    Así mantienes el diseño actual, pero con mejor rendimiento y expresividad.

#### 3. 📦 **Paginación + optimización de consultas**
    La plantilla ya usa `.only()` para optimizar carga. Puedes extenderlo con paginación:

        @staticmethod
        def get_paginated(page: int, size: int, filters=None):
            offset = (page - 1) * size
            limit = offset + size
            instance_list = [[ entity_name|capitalize_first ]].objects.all()
            if filters and "nombre" in filters:
                instance_list = instance_list.filter(nombre__icontains=filters["nombre"])
            instance_list = instance_list.only("id", "nombre", "created_at")[offset:limit]
            return [Mapper.model_to_entity(inst, [[ entity_name|capitalize_first ]]Entity) for inst in instance_list]

    Ideal para APIs o listados grandes.

#### 4. 🔄 **Separación de lectura y escritura (CQRS básico)**
    Aunque la plantilla combina lectura y escritura, puedes dividirla cuando el sistema escala:

        class [[ entity_name|capitalize_first ]]ReadRepository:
            @staticmethod
            def get_all(...):  # Igual al actual
            @staticmethod
            def count_all(...):  # Ya implementado

        class [[ entity_name|capitalize_first ]]WriteRepository:
            @staticmethod
            def create(...):   # Usa `adicionalData` para lógica especial
            @staticmethod
            def save(...):     # Con validaciones y relaciones
            @staticmethod
            def delete(...):   # Con manejo de errores

    Esto permite optimizar consultas (lectura) sin afectar la lógica de mutación (escritura).

#### 5. 🧠 **Consultas complejas bien encapsuladas**
    Cuando necesites agregaciones o filtros avanzados, encapsúlalos en métodos del repositorio:

        from django.db.models import Count
        @staticmethod
        def get_con_muchos_externals(min_relaciones=3):
            instances = [[ entity_name|capitalize_first ]].objects.annotate(
                total_externals=Count('externals')
            ).filter(total_externals__gt=min_relaciones)
            return [Mapper.model_to_entity(inst, [[ entity_name|capitalize_first ]]Entity) for inst in instances]

    Así mantienes el mapeo y la coherencia del dominio.

#### 6. **Uso de `select_related` y `prefetch_related`**
    La plantilla no los usa aún, pero son fáciles de integrar en `get_all()` o nuevos métodos:

        @staticmethod
        def get_all_with_relations():
            instance_list = [[ entity_name|capitalize_first ]].objects.select_related('external').prefetch_related('externals')
            if filters:
                instance_list = instance_list.filter(nombre__icontains=filters["nombre"])
            return [Mapper.model_to_entity(inst, [[ entity_name|capitalize_first ]]Entity) for inst in instance_list]

    Evita el problema N+1 cuando accedes a relaciones.

#### 7. **Consultas RAW o expresiones ORM avanzadas**
    Usa `Q`, `F`, `Subquery`, o SQL crudo **dentro del repositorio** cuando el ORM no alcance:

        from django.db.models import Q, 
        @staticmethod
        def search_advanced(query):
            instances = [[ entity_name|capitalize_first ]].objects.filter(
                Q(nombre__icontains=query) | Q(descripcion__icontains=query)
            )
            return [Mapper.model_to_entity(inst, [[ entity_name|capitalize_first ]]Entity) for inst in instances]

        @staticmethod
        def reactivar_registros():
            [[ entity_name|capitalize_first ]].objects.filter(estado='inactivo').update(estado=F('estado_anterior'))

        @staticmethod
        def busqueda_compleja_sql():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM app_[[ entity_name|decapitalize_first ]] WHERE estado = %s", ['activo'])
                rows = cursor.fetchall()
            return [Mapper.model_to_entity(row, [[ entity_name|capitalize_first ]]Entity) for row in rows]

    El repositorio sigue siendo el único punto de acceso al ORM.

#### 8. **Documentación y claridad**
    Los métodos del repositorio deben reflejar intenciones del negocio, no solo operaciones técnicas:
        @staticmethod
        def get_all(filters=None) -> List[[ entity_name|capitalize_first ]]Entity:
            """
            Obtiene todos los [[ entity_name|decapitalize_first ]] que coincidan con los filtros.
            Usa `.only()` para optimizar rendimiento.
            :param filters: Diccionario con filtros (ej. {"nombre": "juan"}).
            :return: Lista de entidades [[ entity_name|capitalize_first ]].
            """
    Esto hace que el repositorio sea autoexplicativo.

#### 9. **Pruebas unitarias y de integración**
    Cada método debe tener pruebas. Ejemplo con `create()`:
        from django.test import TestCase
        from .repositories import UserRepository    

        class UserRepositoryTests(TestCase):
            def setUp(self):
                # Configuración inicial para las pruebas, si es necesario
                pass
        
            def test_create_con_external_y_externals(self):
                entity = [[ entity_name|capitalize_first ]]Entity(nombre="Test")
                created = [[ entity_name|capitalize_first ]]Repository.create(
                    entity=entity,
                    external_id=1,
                    externals=[1, 2],
                    adicionalData={"archivo": "file.pdf"}
                )
                self.assertIsNotNone(created.id)
                self.assertEqual(created.nombre, "Test")

                # Verifica relaciones
                instance = [[ entity_name|capitalize_first ]].objects.get(id=created.id)
                self.assertEqual(instance.external_id, 1)
                self.assertEqual(instance.externals.count(), 2)

    Así aseguras que `external_id`, `externals` y `adicionalData` funcionen como esperas.

### ✅ Conclusión
Esta plantilla ya cumple con lo esencial para DDD en Django.  
Las recomendaciones no son "extras", sino **posibles evoluciones naturales** que puedes aplicar **cuando el dominio lo requiera**.

El repositorio sigue siendo el traductor entre tu modelo de negocio y Django ORM.  
Hazlo más expresivo, no más complejo.
'''