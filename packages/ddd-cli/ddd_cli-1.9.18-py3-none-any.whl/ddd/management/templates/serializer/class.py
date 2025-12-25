class [[ serializer_name|capitalize_first ]]DTOSerializer(serializers.Serializer):
    """
    Serializer Object para [[ serializer_name|decapitalize_first ]].

    Este Serializer se utiliza para transferir datos entre capas del sistema, 
    como entre la capa de dominio y vistas en Django REST Framework (DRF).
    """

    # Identificadores
    id =  serializers.IntegerField(read_only=True, help_text="ID relacionado con la base de datos")
    uuid = serializers.UUIDField(read_only=True, help_text="UUID relacionado con la entidad")

    # Atributos principales
    attributeName = serializers.CharField(help_text="Nombre del atributo")
    attributeEmail = serializers.EmailField(help_text="Email del atributo")

    # Relaciones
    external_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True, 
        help_text="ID de la entidad externa asociada"
    )

    externals = serializers.ListField(
        required=False,
        allow_empty=True,
        allow_null=True,
        child=serializers.IntegerField(),
        write_only=True,            
        help_text="Lista de IDs de entidades externas asociadas"
    )

    
    # Métodos create y update son obligatorios al usar `serializers.Serializer`
    def create(self, validated_data):
        """
        Debe implementarse según tu lógica de negocio.
        """
        raise NotImplementedError("Implement methond `create` in serializer.")


    def update(self, instance, validated_data):
        """
        Debe implementarse según tu lógica de negocio.
        """
        raise NotImplementedError("Implement method `update` in serializer.")


    '''
    Estructura de campos adicionales para el serializer para correcta validación y documentación:
        - Cada campo debe tener un tipo de dato específico.
        - Los campos obligatorios deben tener `required=True`.
        - Los campos opcionales pueden tener `allow_blank=True` o `allow_null=True`.
        - Los campos de texto deben tener `max_length` y `min_length` adecuados.
        - Los campos de fecha deben usar `serializers.DateTimeField()`.


        Ejemplo de campo obligatorio con validación:
            name = serializers.CharField(
                min_length=3, # Longitud mínima de 3 caracteres
                max_length=100, # Longitud máxima de 100 caracteres
                allow_blank=False, # No permitir cadenas vacías
                allow_null=False, # No permitir valores nulos
                allow_null=True, # Permitir valores nulos
                allow_blank=True, # Permitir cadenas vacías
                trim_whitespace=True,  # Eliminar espacios en blanco al inicio y al final
                error_messages={
                    'blank': 'Este campo no puede estar vacío.',
                    'min_length': 'Este campo debe tener al menos 3 caracteres.',
                    'max_length': 'Este campo no puede superar los 100 caracteres.'
                },
                required=True,  # Campo obligatorio
                read_only=False,  # Campo de solo lectura
                write_only=False, # Campo de solo escritura
                default=None, # Valor por defecto
                help_text="Nombre obligatorio" 
            )
    '''

    '''
    Ejemplos de: 

        - Atributos obligatorios y opcionales
        name = serializers.CharField(max_length=100, help_text="Nombre obligatorio") 
        email = serializers.EmailField(allow_null=True, help_text="Email opcional") 
        slug = serializers.SlugField(help_text="Identificador único legible para URLs") 
        content = serializers.CharField(help_text="Contenido breve o resumen") 
        price = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Precio o valor numérico") 
        quantity = serializers.IntegerField(help_text="Cantidad disponible o asociada")
        rating = serializers.FloatField(help_text="Valoración media (ej. 4.5 estrellas)") 
        is_active = serializers.BooleanField(default=True, help_text="Estado activo/inactivo") 
        is_featured = serializers.BooleanField(default=False, help_text="Si es destacado/promocionado")
        created_at = serializers.DateTimeField(read_only=True, help_text="Fecha de creación")
        updated_at = serializers.DateTimeField(read_only=True, help_text="Fecha de última modificación") 
        deleted_at = serializers.DateTimeField(allow_null=True, help_text="Fecha de eliminación o 'soft delete'")
        image = serializers.URLField(allow_null=True, help_text="URL hacia una imagen asociada") 
        video = serializers.URLField(allow_null=True, help_text="URL hacia un video asociado") 
        latitude = serializers.FloatField(allow_null=True, help_text="Coordenada de latitud")
        longitude = serializers.FloatField(allow_null=True, help_text="Coordenada de longitud") 
        location_name = serializers.CharField(allow_null=True, help_text="Nombre del lugar (dirección o ciudad)") 
        created_by = serializers.IntegerField(allow_null=True, help_text="Usuario que creó la entidad") 
        updated_by = serializers.IntegerField(allow_null=True, help_text="Usuario que actualizó la entidad") 
        order_status = serializers.ChoiceField(
            choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed')], 
            allow_null=True, 
            help_text="Estado de la orden (e.g., 'PENDING', 'COMPLETED')"
        )
        total_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, help_text="Precio total de la orden")
        config = serializers.DictField(allow_null=True, help_text="Configuración adicional ej. {'shipping': 'free', 'gift_wrap': True}")
        categories = serializers.ListField(
            child=serializers.CharField(), 
            allow_null=True, 
            help_text="Lista de categorías asociadas ej. ['electronics', 'clothing']")
        items = serializers.ListField(
            child=serializers.DictField(), 
            allow_null=True, 
            help_text="Lista de artículos asociados ej. [{'product_id': 1, 'quantity': 2}, {'product_id': 2, 'quantity': 1}]"
        )

    - Atributos de relación

        # Identificador externo (ideal para relaciones 1-a-1 con otras entidades o FK)
        external_id = serializers.IntegerField(
            required=False,
            allow_null=True,
            write_only=True, 
            help_text="ID de la entidad externa asociada"
        ) 

        # UUID externo
        external_uuid = serializers.UUIDField(
            required=False,
            allow_null=True,
            write_only=True, 
            help_text="UUID de la entidad externa asociada"
        )

        # Lista de identificadores externos (ideal para relaciones 1-a-M o M-a-M)
        externals = serializers.ListField(
            required=False,
            allow_empty=True,
            allow_null=True,
            child=serializers.IntegerField(), 
            write_only=True,
            help_text="Lista de IDs de entidades externas asociadas"
        )

        # Lista de UUIDs externos
        externals_uuids = serializers.ListField(
            required=False,
            allow_empty=True,
            allow_null=True,
            child=serializers.UUIDField(),
            write_only=True,
            help_text="Lista de UUIDs de entidades externas asociadas"
        )

    '''
