class [[ entity_name|capitalize_first ]]Entity(BaseEntity):
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

    model_config = ConfigDict(
        validate_assignment=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
        }
    )    

    @model_validator(mode='after')
    def validate(self) -> Self:
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

        return self
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "[[ entity_name|capitalize_first ]]Entity":
        """Crea una instancia desde un diccionario"""
        return cls(**data)
        

'''
Guía para añadir nuevos campos a entidades Pydantic (v2)

- ✅ **Atributos opcionales**: usa `Optional[Tipo] = None`
- ✅ **Listas/Dicts por defecto**: usa `Field(default_factory=list)` o `Field(default_factory=dict)`
- ✅ **Atributos obligatorios**: define sin valor por defecto → fallará si no se proporciona
- ✅ **Valores por defecto simples**: asigna directamente (`is_active: bool = True`)
- ✅ **Fechas/horas**: usa `datetime` (no str) → Pydantic parsea ISO automáticamente
- ✅ **Archivos/URLs**: define submodelos tipados (ej. `FileData`) en vez de `dict`

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
    categories: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    items: List[Dict[str, Any]] = Field(default_factory=list)

    # Fechas (usa datetime, no str)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relaciones (IDs)
    external_id: Optional[int] = None # Identificador externo (ideal para relaciones 1-a-1 con otras entidades o FK)
    externals: Optional[List[int]] = None # Lista de identificadores externos (ideal para relaciones 1-a-M o M-a-M)
    
    # Referencias UUID a otras entidades (solo son refencias)
    external_uuid: Optional[str] = None  # UUID externo (para relaciones 1-a-1)
    externals_uuids: Optional[List[str]] = None  # Lista de UUIDs externos  (para relaciones 1-a-M o M-a-M)

    # Objetos complejos (mejor que dict)
    image: Optional[FileData] = None
    address: Optional[AddressData] = None

⚠️ Importante:
- No uses `field(default_factory=...)` (eso es de dataclasses)
- En Pydantic v2, usa `Field(default_factory=...)` desde `pydantic`
- Los campos se validan automáticamente al crear la instancia
- Para validaciones personalizadas, usa `@model_validator` o `@field_validator`

💡 Validadores: ejemplos de uso:

    @model_validator(mode='after')
    def validate(self) -> self:
        if not self.attributeName or len(self.attributeName) < 3:
            raise ValueError("attributeName must be at least 3 characters")
        return self

    @field_validator('attributeEmail')
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Invalid email address")
        return v

💡 Consejo:
Si añades un campo nuevo, no necesitas modificar `__init__`,
`to_dict()`, `from_dict()` ni `update()` → Pydantic lo maneja todo.
'''

    