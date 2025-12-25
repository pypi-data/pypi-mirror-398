class [[ entity_name|capitalize_first ]]Service:
    """
    Servicio para manejar las operaciones CRUD relacionadas con [[ entity_name|decapitalize_first ]].

    Métodos disponibles:
        - list: Lista todas las instancias de [[ entity_name|decapitalize_first ]].
        - count_all: Cuenta todas las instancias de [[ entity_name|decapitalize_first ]].
        - create: Crea una nueva instancia de [[ entity_name|decapitalize_first ]].
        - retrieve: Recupera una instancia de [[ entity_name|decapitalize_first ]] por ID.
        - update: Actualiza una instancia existente de [[ entity_name|decapitalize_first ]].
        - delete: Elimina una instancia de [[ entity_name|decapitalize_first ]].
    """

    #Si necesitas mantener un estado de lista de entidades
    # [[ entity_name|decapitalize_first ]]_list = []    


    def __init__(self, repository: Optional[ [[ entity_name|capitalize_first ]]Repository ] = None):
        """
        Inicializa el servicio con el repositorio correspondiente.

        params:
            repository: Repositorio que maneja la persistencia de [[ entity_name|decapitalize_first ]].
        """

        self.repository = repository or [[ entity_name|capitalize_first ]]Repository()


    def list(self, filters: Optional[dict] = None) -> List[dict]:
        """
        Lista instancias de [[ entity_name|decapitalize_first ]].

        params:
            filters: Filtros opcionales para la consulta.
        return: 
            Lista de la entidad
        raises:
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            ConnectionDataBaseError: Si hay un error al conectar a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).
        """

        entity_list = self.repository.get_all(filters=filters)

        return [entity.to_dict() for entity in entity_list]      


    def count_all(self, filters: Optional[dict] = None) -> int:
        """
        Cuenta todas las instancias de [[ entity_name|decapitalize_first ]].

        param: 
            filters: Filtros opcionales para la consulta.
        return: 
            Número total de instancias.
        raises: 
            [[ entity_name|capitalize_first ]]ValueError:  Si el valor de entrada no es válido.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.       
            RepositoryError: Si ocurre un error inesperado (interno del sistema).             
        """

        return self.repository.count_all(filters=filters)


    def create(self, data, external_id: Optional[int]=None, externals: Optional[List[int]]=None, adicionalData=None) -> dict:
        """
        Crea una nueva instancia de [[ entity_name|decapitalize_first ]].

        params: 
            data: Diccionario o DTO con los datos necesarios para crear la instancia.
            external_id: ID del padre si es necesario (opcional).
            externals: Lista de IDs de entidades relacionadas (opcional).
            adicionalData: Datos adicionales a incluir en la creación.
        return: 
            La entidad creada.
        raises: 
            [[ entity_name|capitalize_first ]]ValueError: Si el valor de entrada no es válido.
            [[ entity_name|capitalize_first ]]ValidationError: Si los datos no son válidos.
            [[ entity_name|capitalize_first ]]AlreadyExistsError: Si ya existe un registro con el mismo nombre.            
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).            
        """

        # Validación de reglas de negocio (opcional)
        if self.repository.exists_by_field(field_name="attributeName", value=data.get("attributeName")):
            raise [[ entity_name|capitalize_first ]]ValueError(field="attributeName", detail="An instance with this attributeName already exists")

        #crear y validar la entidad
        entity = [[ entity_name|capitalize_first ]]Entity.from_dict(data)
        entity.validate()       

        # Guardar en el repositorio
        saved_entity = self.repository.create(entity=entity, external_id=external_id, externals=externals, adicionalData=adicionalData)

        return saved_entity.to_dict()


    def retrieve(self, entity_id: int = None, entity_uuid: str = None) -> dict:
        """
        Recupera una instancia de [[ entity_name|decapitalize_first ]] por su ID o UUID.

        param: 
            entity_id: ID de la instancia a recuperar.
            entity_uuid: UUID de la instancia a recuperar.
        return: 
            La entidad recuperada.
        raises:
            [[ entity_name|capitalize_first ]]ValueError: Si el valor de entrada no es válido.         
            [[ entity_name|capitalize_first ]]NotFoundError: Si no existe el registro con el ID dado.
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).
        """

        entity = self.repository.get_by_id(id=entity_id, uuid=entity_uuid)

        return entity.to_dict()


    def update(self, entity_id: int = None, entity_uuid: str = None, data = None, external_id: Optional[int]=None, externals: Optional[List[int]]=None, adicionalData=None) -> dict:
        """
        Actualiza una instancia existente de [[ entity_name|decapitalize_first ]].

        params:
            entity_id: ID de la instancia a actualizar.
            entity_uuid: UUID de la instancia a actualizar.
            data: Diccionario o DTO con los datos a actualizar.
            external_id: ID del padre si es necesario (opcional).
            externals: Lista de IDs de entidades relacionadas (opcional).
            adicionalData: Datos adicionales a incluir en la actualización.
        return: 
            La entidad actualizada.
        raises: 
            [[ entity_name|capitalize_first ]]NotFoundError: Si no existe el registro con el ID dado.
            [[ entity_name|capitalize_first ]]ValueError: Si el valor de entrada no es válido.                 
            [[ entity_name|capitalize_first ]]ValidationError: Si los datos no son válidos.            
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).
        """
        # Validación de entrada
        if not entity_id and not entity_uuid:
            raise [[ entity_name|capitalize_first ]]ValueError(field="id/uuid", detail="The id or uuid field is required")
        
        if not data:
            raise [[ entity_name|capitalize_first ]]ValueError(field="data", detail="The data field is required")

        # Recuperar la entidad
        entity = self.repository.get_by_id(id=entity_id, uuid=entity_uuid)

        if not entity:
            raise [[ entity_name|capitalize_first ]]NotFoundError(id=entity_id or entity_uuid)

        # actualizar la instancia y validar
        entity.update(data)     
        entity.validate()   

        # Guardar en el repositorio
        updated_entity = self.repository.update(entity=entity, external_id=external_id, externals=externals, adicionalData=adicionalData)

        return updated_entity.to_dict()


    def delete(self, entity_id: int = None, entity_uuid: str = None) -> bool:
        """
        Elimina una instancia de [[ entity_name|decapitalize_first ]].

        params:
            entity_id: ID de la instancia a eliminar.
            entity_uuid: UUID de la instancia a eliminar.
        return: 
            True/False (depende del exito de la operacion)
        raises:
            [[ entity_name|capitalize_first ]]NotFoundError: Si no se encuentra la instancia.
            [[ entity_name|capitalize_first ]]ValueError: Si el valor de entrada no es válido.
            [[ entity_name|capitalize_first ]]ValidationError: Si los datos no son válidos.            
            ConnectionDataBaseError: Si ocurre un error al acceder a la base de datos.
            RepositoryError: Si ocurre un error inesperado (interno del sistema).            
        """
        # Validación de entrada
        if not entity_id and not entity_uuid:
            raise [[ entity_name|capitalize_first ]]ValueError(field="id/uuid", detail="The id or uuid field is required")

        # Eliminación en el repositorio
        self.repository.delete(id=entity_id, uuid=entity_uuid)

        return True
