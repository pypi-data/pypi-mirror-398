from django import forms
from django.core import validators
from django.core.validators import (
    MinLengthValidator,
    MaxLengthValidator,
    RegexValidator,
    EmailValidator,
    MinValueValidator,
    MaxValueValidator,
)


class [[ entity_name|capitalize_first ]]BaseForm(forms.Form):
    """
    Formulario base para la entidad [[ entity_name|decapitalize_first ]].
    """

    # Campos del formulario no actualizables en la entidad
    # Son aquellos que no son utiles para la logica del dominio o persistencia
    # o aquellos que se presentan mediante una estructura distinta a la que espera la entity (ej: imagenes o archivos)
    ENTITY_NOT_UPDATABLE_FIELDS = {
        'attributePhoto',
        'attributePassword',
    }    

    def __init__(self, *_args, **kwargs):
        super().__init__(*_args, **kwargs)

        # Definimos los campos del formulario de manera dinámica
        # Campo de texto y numeros (Nombre)
        self.fields['attributeName'] = forms.CharField(
            label="Name",
            max_length=100,
            required=True,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'minlength': '3',  # HTML5 validación
                'maxlength': '100',  # HTML5 validación
                'pattern': r'^[A-Za-z0-9ñÑáéíóúÁÉÍÓÚ ]*$',  # Expresión regular en el navegador
                'title': 'The name must only contain letters, numbers, and spaces.'  # Mensaje de ayuda                          
            }),
            validators=[
                MinLengthValidator(3, "The name must be at least 3 characters"),
                MaxLengthValidator(100, "The name must not exceed 100 characters"),
                RegexValidator(r'^[A-Za-z0-9ñÑáéíóúÁÉÍÓÚ ]*$', 'The name must only contain letters, numbers, and spaces.'),
            ]
        )

        # Campo de correo electrónico
        self.fields['attributeEmail'] = forms.EmailField(
            label="Email",
            required=True,
            widget=forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email',
            }),
            validators=[
                EmailValidator("Please enter a valid email address"),
            ]
        )

        # Campo de contraseña
        self.fields['attributePassword'] = forms.CharField(
            label="Password",
            required=True,
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Create a password',
                'minlength': '8',
            }),
            validators=[
                MinLengthValidator(8, "Password must be at least 8 characters long"),
            ]
        )

        self.fields['attributePhoto'] = forms.ImageField(
            label="Image",
            required=False,  # La photo no es obligatoria
            widget=forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',  # Restringe el tipo de archivo a imágenes
            }), 
            help_text="Formatos permitidos: JPG, PNG" # Esta ayuda se mostrará debajo del campo
        )   


    def clean_attributeName(self):
        '''
        Esta validacion es solo para el campo 'attributeName'

        raises:
            forms.ValidationError: Si el nombre es menor a 3 caracteres.
        '''    
        attributeName = self.cleaned_data.get('attributeName')
        if len(attributeName) < 3:
            raise forms.ValidationError("The name must be at least 3 characters long")
        return attributeName


    def clean_attributeEmail(self):
        '''
        Esta validacion es solo para el campo 'attributeEmail'
        
        raises:
            forms.ValidationError: Si el email no es válido.
        '''
        attributeEmail = self.cleaned_data.get('attributeEmail')
        if attributeEmail.endswith('@example.com'):
            raise forms.ValidationError("Emails from example.com are not allowed")
        return attributeEmail

        
    def clean(self):
        '''
        Aqui podemos hacer validaciones que involucren a varios campos

        raises:
            forms.ValidationError: Si hay errores de validación en los campos.
        '''
        cleaned_data = super().clean()
        attributePassword = cleaned_data.get('attributePassword')
        attributePassword_confirm = cleaned_data.get('attributePassword_confirm')

        if attributePassword != attributePassword_confirm:
            raise forms.ValidationError("Passwords do not match")


class [[ entity_name|capitalize_first ]]CreateForm([[ entity_name|capitalize_first ]]BaseForm):
    """
    Formulario para crear una nueva instancia de [[ entity_name|decapitalize_first ]]. Sin modificaciones adicionales.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)       
        
        #Permitimos que el attributeEmail sea editable
        self.fields['attributeEmail'].widget.attrs.update({
            'readonly': False,
        })

        # Aqui podemos agregar validaciones adicionales o modificar el comportamiento del formulario


class [[ entity_name|capitalize_first ]]EditGetForm([[ entity_name|capitalize_first ]]BaseForm):
    """
    Formulario para editar mediante GET una instancia de [[ entity_name|decapitalize_first ]]. 
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   
        
        #Agregamos un campo adicional para 'id' Oculto para el Formulario
        self.fields['id'] = forms.IntegerField(
            label='ID',
            required=False,
            widget=forms.HiddenInput()
        )

        # Aqui podemos agregar validaciones adicionales o modificar el comportamiento del formulario

        #impedimos que el attributeEmail sea editable 
        self.fields['attributeEmail'].widget.attrs.update({
            'readonly': 'True'
        })


class [[ entity_name|capitalize_first ]]EditPostForm([[ entity_name|capitalize_first ]]BaseForm):
    """
    Formulario para editar mediante POST una instancia de [[ entity_name|decapitalize_first ]]. 
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)     

        # Aqui podemos agregar validaciones adicionales o modificar el comportamiento del formulario 


class [[ entity_name|capitalize_first ]]ViewForm([[ entity_name|capitalize_first ]]BaseForm):
    """
    Formulario de solo lectura para Visualizar una instancia de [[ entity_name|decapitalize_first ]]
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aqui podemos agregar validaciones adicionales o modificar el comportamiento del formulario

        # Hacer todos los campos no editables
        for field in self.fields.values():
            field.widget.attrs['disabled'] = True



"""
    Ejemplo completo de formulario con todos los tipos de campo y widget más comunes.

    # === Campos de texto ===
    self.fields['char_field'] = forms.CharField(
        label=_("Nombre"),
        max_length=100,
        required=True,
        help_text=_("Ej: Juan Pérez"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[
            MinLengthValidator(3),
            MaxLengthValidator(100),
            RegexValidator(r'^[A-Za-zñÑáéíóúÁÉÍÓÚ ]+$', "Solo letras y espacios.")
        ]
    )

    self.fields['text_area'] = forms.CharField(
        label=_("Descripción"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )

    # === Campos numéricos ===
    self.fields['integer_field'] = forms.IntegerField(
        label=_("Edad"),
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        validators=[MinValueValidator(0), MaxValueValidator(120)]
    )

    self.fields['decimal_field'] = forms.DecimalField(
        label=_("Precio"),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    # === Campos de fecha y hora ===
    self.fields['date_field'] = forms.DateField(
        label=_("Fecha de nacimiento"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )

    self.fields['datetime_field'] = forms.DateTimeField(
        label=_("Fecha y hora"),
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        required=False
    )

    self.fields['time_field'] = forms.TimeField(
        label=_("Hora"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=False
    )

    # === Campos de selección ===
    self.fields['choice_field'] = forms.ChoiceField(
        label=_("País"),
        choices=[
            ('', 'Selecciona un país'),
            ('es', 'España'),
            ('mx', 'México'),
            ('co', 'Colombia')
        ],
        widget=forms.Select(attrs={'class': 'form-control form-select'}),
        required=True
    )

    self.fields['multiple_choice_field'] = forms.MultipleChoiceField(
        label=_("Hobbies"),
        choices=[
            ('reading', 'Leer'),
            ('sports', 'Deportes'),
            ('music', 'Música')
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    # === Campos booleanos ===
    self.fields['boolean_field'] = forms.BooleanField(
        label=_("¿Acepta términos?"),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': "Debe aceptar los términos"}
    )

    self.fields['null_boolean_field'] = forms.NullBooleanField(
        label=_("¿Ha visitado antes?"),
        widget=forms.Select(choices=[
            (None, '---'),
            (True, 'Sí'),
            (False, 'No')
        ], attrs={'class': 'form-control form-select'}),
        required=False
    )

    # === Campos de archivo ===
    self.fields['file_field'] = forms.FileField(
        label=_("Archivo"),
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        validators=[forms.FileExtensionValidator(['pdf', 'docx'], "Solo archivos PDF o DOCX")]
    )

    self.fields['image_field'] = forms.ImageField(
        label="Image",
        required=False,  # La imagen no es obligatoria
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',  # Restringe el tipo de archivo a imágenes
        }),
        help_text="Formatos permitidos: JPG, PNG"
    )   


    # === Campos especiales ===
    self.fields['email_field'] = forms.EmailField(
        label=_("Correo electrónico"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        validators=[EmailValidator("Correo inválido")]
    )

    self.fields['url_field'] = forms.URLField(
        label="Website",
        required=False,  # Este campo no es obligatorio
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your website URL',
        }),
        validators=[
            RegexValidator(
                r'^(https?|ftp)://[^\\s/$.?#].[^\\s]*$',
                "Please enter a valid URL starting with http://, https://, or ftp://"
            ),
        ]
    )

    self.fields['slug_field'] = forms.SlugField(
        label=_("Slug (URL)"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("Solo letras, números y guiones")
    )

    self.fields['ip_field'] = forms.GenericIPAddressField(
        label=_("Dirección IP"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    self.fields['uuid_field'] = forms.UUIDField(
        label=_("UUID"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("Formato: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx")
    )

    # === Campos ocultos ===
    self.fields['hidden_field'] = forms.CharField(
        widget=forms.HiddenInput(),
        initial="valor_oculto",
        required=False
    )

    # === Campos de solo lectura ===
    self.fields['read_only_field'] = forms.CharField(
        label=_("Campo de solo lectura"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )

    # === Campos personalizados ===
    self.fields['custom_field'] = forms.CharField(
        label=_("Campo personalizado"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[
            RegexValidator(r'^[A-Za-z0-9_]+$', "Solo letras, números y guiones bajos permitidos.")
        ]
    )
    custom_field.widget.attrs.update({
        'placeholder': 'Ingrese un valor personalizado',
        'title': 'Este es un campo personalizado con validación específica.'
    })  

    # === Ejemplos practicos de campos adicionales ===

    # Campo de solo texto sin números (Category)
    self.fields['attributeCategory'] = forms.CharField(
        label='Category',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'minlength': '4',  # Mínima longitud en el navegador
            'maxlength': '250',  # Máxima longitud en el navegador      
            'pattern': r'^[A-Za-z\\s]*$',  # Expresión regular en el navegador           
            'title': 'The name can only contain letters and spaces.'
        }),
        validators=[
            MinLengthValidator(4, "The name must be at least 4 characters"),
            MaxLengthValidator(250, "The name must not exceed 250 characters"),
            RegexValidator(r'^[A-Za-z\\s]*$', "The name can only contain letters and spaces"),
        ]          
    ) 

    # Campo de contraseña
    self.fields['attributePassword'] = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'minlength': '8',
        }),
        validators=[
            MinLengthValidator(8, "Password must be at least 8 characters long"),
        ]
    )

    # Campo numérico
    self.fields['attributeAge'] = forms.IntegerField(
        label="Age",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '18',  # HTML5 validación
            'max': '100',  # HTML5 validación
            'placeholder': 'Enter your age',
        }),
        validators=[
            MinValueValidator(18, "You must be at least 18 years old"),
            MaxValueValidator(100, "The age must not exceed 100"),
        ]
    )

    # Campo de fecha
    self.fields['attributeBirthDate'] = forms.DateField(
        label="Birth Date",
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',  # HTML5 tipo fecha
        })
    )

    # Selección desplegable
    self.fields['attributeCountry'] = forms.ChoiceField(
        label="Country",
        required=True,
        choices=[
            ('', 'Select your country'),
            ('us', 'United States'),
            ('es', 'Spain'),
            ('mx', 'Mexico'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
        })  
    )

    # Opciones de radio
    self.fields['attributeGender'] = forms.ChoiceField(
        label="Gender",
        required=True,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )

    # Casillas de verificación
    self.fields['attributeTerms'] = forms.BooleanField(
        label="I accept the terms and conditions",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        error_messages={
            'required': "You must accept the terms and conditions to proceed",
        }
    )      

    Nota: la razon de construir los campos de manera dinamica en el constructor es que
    permite fabricar formularios de manera flexible y reutilizable,
    especialmente cuando se trabaja con datos que pueden cambiar o ser configurables
    en tiempo de ejecución tales como traducciones, opciones de selección, etc.
    Esto es especialmente útil en aplicaciones que requieren internacionalización o personalización
    de la interfaz de usuario, ya que permite adaptar los formularios a diferentes contextos
    o preferencias del usuario sin necesidad de modificar el código fuente del formulario.

"""

            
'''
Flujo de Validación en Django Forms

Cuando se llama al método is_valid() de un formulario, Django realiza las siguientes acciones de manera secuencial:

1. Limpiar los datos de entrada crudos
    Antes de cualquier validación, Django toma los datos enviados ( o  en formularios de tipo GET) y los procesa en el objeto . 
    Esto incluye convertir los valores en tipos de datos que Django pueda interpretar.

2. Validación de los campos individuales
    Django valida cada campo del formulario según las reglas especificadas en el formulario o en el modelo asociado. 
    Este proceso incluye:
    
    Validadores básicos del campo:
    - Validación de tipo: Por ejemplo, un campo 'forms.integerField' asegura que el valor sea un entero.
    - Validación de valores requeridos: Si el campo tiene 'required=True' y no se proporciona ningún valor, se genera un error.
    - Validación de longitud: En campos como 'CharField', 'max_length' y 'min_length' son comprobados.
    - Validación de opciones: En campos como 'Choice_Field', el valor debe ser una de las opciones definidas

    Validadores específicos: Los validadores personalizados definidos en el propio campo o como funciones adicionales se ejecutan

3. Métodos 'clean_<nombr_campo>'
    Django busca métodos personalizados para los campos del formulario, siguiendo la convención 'clean_<nombr_campo>'. 
    Si existen, estos métodos se ejecutan después de las validaciones básicas del campo.

    Ejemplo:

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith("@example.com"):
            raise forms.ValidationError("Only example.com emails are allowed")
        return email

    Los errores generados por estos métodos se almacenan en el atributo 'form.field_name.errors'.

4. Método 'clean()' general
    Una vez que todos los campos han sido validados individualmente, Django llama al método 'clean()'  general del formulario. 
    Este método es útil para validar dependencias entre múltiples campos.
    Por ejemplo:

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match")

    Los errores de este método se almacenan en 'form.errors' como errores globales, no asociados a un campo específico.

5. Almacenar los datos validados
    Si no hay errores, los valores procesados y validados se almacenan en el atributo 'form.cleaned_data', 
    que es un diccionario con los datos del formulario que pasaron la validación.

Nota: raise forms.ValidationError no detiene la ejecución del código,
sino que agrega el error al formulario, permitiendo que se maneje adecuadamente en la plantilla o en la vista.
Esto permite que el formulario se pueda volver a renderizar con los errores
y que el usuario pueda corregir los datos ingresados.

'''