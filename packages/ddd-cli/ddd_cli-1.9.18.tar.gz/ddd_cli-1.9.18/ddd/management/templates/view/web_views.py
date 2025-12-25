from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .utils.filter_dict import clean_dict_of_keys

# importa las excepciones personalizadas
from .domain.[[ entity_name.lower() ]]_exceptions import (
    [[ entity_name|capitalize_first ]]ValueError,
    [[ entity_name|capitalize_first ]]ValidationError,
    [[ entity_name|capitalize_first ]]AlreadyExistsError,
    [[ entity_name|capitalize_first ]]NotFoundError,
    [[ entity_name|capitalize_first ]]OperationNotAllowedError,
    [[ entity_name|capitalize_first ]]PermissionError
)

# importa las excepciones de repositorio
from .infrastructure.exceptions import (
    ConnectionDataBaseError,
    RepositoryError
)

# Importar formularios específicos de la entidad
from [[ app_name.lower() ]].[[ entity_name.lower() ]]_forms import (
    [[ entity_name|capitalize_first ]]CreateForm, 
    [[ entity_name|capitalize_first ]]EditGetForm, 
    [[ entity_name|capitalize_first ]]EditPostForm, 
    [[ entity_name|capitalize_first ]]ViewForm
)

# Importar servicios específicos del dominio
from [[ app_name.lower() ]].services.[[ entity_name.lower() ]]_service import [[ entity_name|capitalize_first ]]Service


def list(request):
    """
    Vista genérica para mostrar una lista de todas las instancias de [[ entity_name|decapitalize_first ]].
    """

    [[ entity_name|decapitalize_first ]]List = [] #inicialize list

    # Obtener la lista del repositorio
    try:
        [[ entity_name|decapitalize_first ]]List = [[ entity_name|capitalize_first ]]Service().list()

    except ([[ entity_name|capitalize_first ]]ValueError) as e:
        messages.error(request,  str(e))
    except (ConnectionDataBaseError, RepositoryError) as e:
        messages.error(request, "There was an error accessing the database or repository: " + str(e))
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))

    # Renderizar la plantilla con la lista
    return render(request, '[[ relative_app_path.lower() ]]/[[ entity_name.lower() ]]_web_list.html', {
        '[[ entity_name|decapitalize_first ]]List': [[ entity_name|decapitalize_first ]]List
    })


def count_all(request):
    """
    Vista genérica para contar todas las instancias de [[ entity_name|decapitalize_first ]].
    """

    count = 0

    # Obtener el conteo del repositorio
    try:
        count = [[ entity_name|capitalize_first ]]Service().count_all()

    except ([[ entity_name|capitalize_first ]]ValueError) as e:
        messages.error(request,  str(e))
    except (ConnectionDataBaseError, RepositoryError) as e:
        messages.error(request, "There was an error accessing the database or repository: " + str(e))
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))

    # Retornar el conteo como respuesta HTTP
    return HttpResponse(f"Total [[ entity_name|decapitalize_first ]] count: {count}")


def create(request):
    """
    Vista genérica para crear una nueva instancia de [[ entity_name|decapitalize_first ]] utilizando un servicio.
    """

    if request.method == "POST":

        # Validar los datos del formulario
        form = [[ entity_name|capitalize_first ]]CreateForm(request.POST, request.FILES)

        if form.is_valid():
            try:        
                form_data = form.cleaned_data

                # Obtener el ID de la entidad relacionada si existe
                external_id = request.POST.get('external_id', None)

                # Obtener la lista de ids de externals seleccionadas
                externals_ids = form_data.get('externals', [])

                # LLamar al servicio de creación
                [[ entity_name|capitalize_first ]]Service().create(data=form_data, external_id=external_id, externals=externals_ids)

                # Mostrar mensaje de éxito y redirigir
                messages.success(request, f"Successfully created [[ entity_name|decapitalize_first ]]")
                return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

            except [[ entity_name|capitalize_first ]]AlreadyExistsError as e:
                messages.error(request, "Already Exists Error: " + str(e))
            except ([[ entity_name|capitalize_first ]]ValueError, [[ entity_name|capitalize_first ]]ValidationError) as e:
                form.add_error(None, "Validation Error: " + str(e))
            except (ConnectionDataBaseError, RepositoryError) as e:
                messages.error(request, "There was an error accessing the database or repository: " + str(e))
            except Exception as e:
                messages.error(request, "An unexpected error occurred: " + str(e))
        else:
            messages.error(request, "There were errors in the form. Please correct them")

    # request.method == "GET":
    else:
        # Formulario vacío para solicitudes GET
        form = [[ entity_name|capitalize_first ]]CreateForm()

    # Renderizar la plantilla con el formulario
    return render(request, '[[ relative_app_path.lower() ]]/[[ entity_name.lower() ]]_web_create.html', {'form': form}) 


def edit(request, id=None):
    """
    Vista genérica para editar una instancia existente de [[ entity_name|decapitalize_first ]] utilizando un servicio.
    """

    if id is None:
        # Redireccion si no se proporciona un ID
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

    try:
        # Obtener los datos de la entidad desde el servicio
        [[ entity_name|decapitalize_first ]] = [[ entity_name|capitalize_first ]]Service().retrieve(entity_id=id)

    except [[ entity_name|capitalize_first ]]NotFoundError as e:
        messages.error(request,  "Not Found Error: " + str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')
    except [[ entity_name|capitalize_first ]]ValueError as e:
        messages.error(request,  "Value Error: " + str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')
    except (ConnectionDataBaseError, RepositoryError) as e:
        messages.error(request, "There was an error accessing the database or repository: " + str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

    if request.method == "POST":

        # Validar los datos del formulario
        form = [[ entity_name|capitalize_first ]]EditPostForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                form_data = form.cleaned_data            
                
                # obtenemos del request los campos especiales del formulario
                # ejemplo: password = request.POST.get('password', None)
                # ejemplo: photo = request.FILES.get('photo', None)
                # y los enviamos como parametros al servicio de actualizacion

                # Obtener el ID de la entidad relacionada si existe
                external_id = request.POST.get('external_id', None)

                # Obtener la lista de ids de externals seleccionadas
                externals_ids = form_data.get('externals', [])         
                
                # Limpiar los campos no actualizables del diccionario de datos
                form_data = clean_dict_of_keys(form_data, keys=[[ entity_name|capitalize_first ]]EditPostForm.ENTITY_NOT_UPDATABLE_FIELDS)

                # LLamar al servicio de actualización
                [[ entity_name|capitalize_first ]]Service().update(entity_id=id, data=form_data, external_id=external_id, externals=externals_ids)

                # Mostrar mensaje de éxito
                messages.success(request, f"Successfully updated [[ entity_name|decapitalize_first ]]")

                # Redireccionar a la lista de [[ entity_name|decapitalize_first ]]s
                return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

            except [[ entity_name|capitalize_first ]]NotFoundError as e:
                messages.error(request,  "Not Found Error: " + str(e))                
            except ([[ entity_name|capitalize_first ]]ValueError, [[ entity_name|capitalize_first ]]ValidationError) as e:
                form.add_error(None, "Validation Error: " + str(e))
            except (ConnectionDataBaseError, RepositoryError) as e:
                messages.error(request, "There was an error accessing the database or repository: " + str(e))
            except Exception as e:
                messages.error(request, "An unexpected error occurred: " + str(e))

        else:
            messages.error(request, "There were errors in the form. Please correct them")

    # request.method == "GET":
    else:  
        # Initialize the form with existing data
        form = [[ entity_name|capitalize_first ]]EditGetForm(initial={
            'id': [[ entity_name|decapitalize_first ]].get('id'),
            'attributeName': [[ entity_name|decapitalize_first ]].get('attributeName'),
            'attributeEmail': [[ entity_name|decapitalize_first ]].get('attributeEmail')
        })

    # Renderizar la plantilla con el formulario
    return render(request, '[[ relative_app_path.lower() ]]/[[ entity_name.lower() ]]_web_edit.html', {'form': form})


def detail(request, id=None):
    """
    Vista genérica para mostrar los detalles de una instancia específica de [[ entity_name|decapitalize_first ]].
    """
    if id is None:
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

    try:
        # Obtener los datos de la entidad desde el servicio
        [[ entity_name|decapitalize_first ]] = [[ entity_name|capitalize_first ]]Service().retrieve(entity_id=id)

    except [[ entity_name|capitalize_first ]]NotFoundError as e:
        messages.error(request,  "Not Found Error: " + str(e))        
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')
    except [[ entity_name|capitalize_first ]]ValueError as e:
        messages.error(request,  str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')
    except (ConnectionDataBaseError, RepositoryError) as e:
        messages.error(request, "There was an error accessing the database or repository: " + str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

    # Renderizar la plantilla con el formulario de vista
    form = [[ entity_name|capitalize_first ]]ViewForm(initial={
        'attributeName': [[ entity_name|decapitalize_first ]].get('attributeName'),
        'attributeEmail': [[ entity_name|decapitalize_first ]].get('attributeEmail')
    })

    return render(request, '[[ relative_app_path.lower() ]]/[[ entity_name.lower() ]]_web_detail.html', {'form': form})


def delete(request, id=None):
    """
    Vista genérica para eliminar una instancia existente de [[ entity_name|decapitalize_first ]] utilizando un servicio.
    """
    if id is None:
        messages.error(request, "Non Valid id to delete")
        return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

    try:
        # LLamar al servicio de eliminación
        [[ entity_name|capitalize_first ]]Service().delete(entity_id=id)
        messages.success(request, f"Successfully deleted [[ entity_name|decapitalize_first ]]")

    except [[ entity_name|capitalize_first ]]NotFoundError as e:
        messages.error(request,  "Not Found Error: " + str(e))             
    except ([[ entity_name|capitalize_first ]]ValueError, [[ entity_name|capitalize_first ]]ValidationError) as e:
        messages.error(request,  "Validation Error: " + str(e))
    except (ConnectionDataBaseError, RepositoryError) as e:
        messages.error(request, "There was an error accessing the database or repository: " + str(e))
    except Exception as e:
        messages.error(request, "An unexpected error occurred: " + str(e))

    return redirect('[[ app_route.lower() ]]:[[ entity_name.lower() ]]_list')

