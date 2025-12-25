@dataclass
class [[ entity_name|capitalize_first ]]Entity:
    """
    Entidad del dominio para [[ entity_name|decapitalize_first ]].

    Esta clase representa la lógica de negocio central y las reglas asociadas 
    con [[ entity_name|decapitalize_first ]] en el sistema.
    """
    
    # Identificadores
    id: Optional[int] = None  # ID relacionado con la base de datos
    uuid: Optional[UUID] = None

    # Atributos principales
    attributeName: Optional[str] = None  # Atributo opcional
    attributeEmail: Optional[str] = None  # Atributo opcional

    # Relaciones
    external_id: Optional[int] = None  # ID de una entidad relacionada (opcional)

    # Relaciones Many-to-Many o Reverse FK
    externals: Optional[List[int]] = None  # Lista de IDs de entidades relacionadas

    # Descomentar si se quiere hacer una validacion estricta
    #def __post_init__(self):
    #    self.validate()   

    def validate(self) -> None:
        """
        Valida la entidad antes de guardar o procesar.
        Lanza excepciones si las reglas de negocio no se cumplen.
        - Consistencia interna de los atributos
        - Validaciones intrínsecas al momento de creación/modificación
        """
        if not self.attributeName or len(self.attributeName) < 3:
            raise [[ entity_name|capitalize_first ]]ValueError(field="attributeName", detail="attributeName must be at least 3 characters")

        if self.attributeEmail and len(self.attributeEmail) > 500:
            raise [[ entity_name|capitalize_first ]]ValueError(field="attributeEmail", detail="attributeEmail must not exceed 500 characters")

    def update(self, data:dict, addMode:bool = False) -> None:
        """
        Actualiza los atributos de la entidad con valores nuevos.
        si addMode = True permite añadir campos nuevos
        :param data: Diccionario con los nuevos valores para los atributos.
        :param addMode: Si es True, permite añadir nuevos campos que no existan en la entidad.
        :raises [[ entity_name|capitalize_first ]]ValueError: Si hay un error de estructura en los datos.
        """
        # Actualizar cada campo proporcionado en 'data'
        for key, value in data.items():
            if hasattr(self, key) or addMode:
                try:
                    setattr(self, key, value)             
                except TypeError as e:
                    raise [[ entity_name|capitalize_first ]]ValueError(field=key, detail=f"Error in data structure: {str(e)}") from e

        self.validate()    

    def to_dict(self) -> dict:
        """
        Convierte la entidad a un diccionario, excluyendo los campos con valor None.
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @staticmethod
    def from_dict(data: dict) -> "[[ entity_name|capitalize_first ]]Entity":
        """
        Crea una instancia de la entidad a partir de un diccionario.
        """
        # aqui quitaremos de 'data' los campos no deseados para la entity

        # construir la entidad
        try:
            entity = [[ entity_name|capitalize_first ]]Entity(**data)
        except TypeError as e:
            raise [[ entity_name|capitalize_first ]]ValueError("Error building entity:", str(e)) from e

        return entity
        

'''
Guía para añadir nuevos campos a entidades Dataclass:

- ✅ **Atributos opcionales**: usa `Optional[Tipo] = None`
- ✅ **Listas/Dicts por defecto**: usa `field(default_factory=list)` o `field(default_factory=dict)`
- ✅ **Atributos obligatorios**: define sin valor por defecto → fallará si no se proporciona
- ✅ **Valores por defecto simples**: asigna directamente (`is_active: bool = True`)
- ✅ **Fechas/horas**: usa `str` en formato ISO (ej. "2023-10-05T14:48:00Z") → convierte a datetime al usar
- ✅ **Archivos/URLs**: usa Optional[dict] o crea submodelos si es complejo

Ejemplos:

    # Atributos simples opcionales
    name: Optional[str] = None
    email: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    is_featured: Optional[bool] = None

    # Atributos con valor por defecto (no None)
    is_active: bool = True
    rating: float = 0.0

    # Colecciones con valor por defecto (¡nunca asignes [] o {} directamente!)
    categories: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    items: List[Dict[str, Any]] = field(default_factory=list)

    # Fechas (usa str en formato ISO)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Relaciones (IDs)
    external_id: Optional[int] = None # Identificador externo (ideal para relaciones 1-a-1 con otras entidades o FK)
    externals: Optional[List[int]] = None # Lista de identificadores externos (ideal para relaciones 1-a-M o M-a-M)

    # Referencias UUID a otras entidades (solo son refencias)
    external_uuid: Optional[str] = None  # UUID externo (para relaciones 1-a-1)
    externals_uuids: Optional[List[str]] = None  # Lista de UUIDs externos  (para relaciones 1-a-M o M-a-M)

    # Objetos complejos (mejor usar dict)
    image: Optional[dict] = None
    address: Optional[dict] = None

⚠️ Importante:
- Los campos se validan automáticamente al crear la instancia
- Para validaciones personalizadas, usa `@dataclass` o `@field_validator`
'''
