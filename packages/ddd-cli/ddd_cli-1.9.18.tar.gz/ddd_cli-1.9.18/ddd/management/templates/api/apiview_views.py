from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated

# importar serializers
from .serializers import [[ entity_name|capitalize_first ]]DTOSerializer

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

# Importar servicios específicos del dominio
from [[ app_name.lower() ]].services.[[ entity_name.lower() ]]_service import [[ entity_name|capitalize_first ]]Service

class [[ entity_name|capitalize_first ]]APIView(APIView):
    """
    API para manejar operaciones CRUD relacionadas con [[ entity_name|decapitalize_first ]].
    Este APIView interactúa con:
    - Servicios del dominio que encapsulan la lógica de negocio.
    - Repositorios que interactúan con la capa de persistencia.
    """

    # Definición de permisos y autenticación
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    # Definición de métodos HTTP permitidos
    # http_method_names = ['get', 'post', 'put', 'delete']


    @swagger_auto_schema(
        operation_summary="Retrieve a list or a specific [[ entity_name|decapitalize_first ]]",
        operation_description="Retrieve a list of all [[ entity_name|decapitalize_first ]] or a specific one by ID",
        responses={
            200: [[ entity_name|capitalize_first ]]DTOSerializer,
            404: "Not Found",
            400: "Bad Request"
        },
        tags=["[[ entity_name|decapitalize_first ]]"]
    )
    def get(self, request, id=None):
        """
        Maneja solicitudes GET para recuperar uno o todos los registros.

        - Si se proporciona `id`, recupera un registro específico.
        - Si no se proporciona `id`, recupera todos los registros.
        """

        [[ entity_name|decapitalize_first ]]Service = [[ entity_name|capitalize_first ]]Service() # Instanciar el servicio

        if id is not None:
            # Recuperar un registro específico por ID
            try:

                [[ entity_name|decapitalize_first ]] = [[ entity_name|decapitalize_first ]]Service.retrieve(entity_id=id)

                # Serializar el registro recuperado
                response_serializer = [[ entity_name|capitalize_first ]]DTOSerializer([[ entity_name|decapitalize_first ]])
                response_serializer.is_valid(raise_exception=True)

                # Retornar la respuesta con un estado HTTP 200 OK
                return Response(response_serializer.data, status=status.HTTP_200_OK)                     

            except [[ entity_name|capitalize_first ]]NotFoundError as e:
                # Manejar errores si no se encuentra el registro
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            except [[ entity_name|capitalize_first ]]ValueError as e:
                # Manejar errores de validación si el ID no es válido
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except (ConnectionDataBaseError, RepositoryError) as e:
                # Manejar errores de conexión a la base de datos o repositorio
                return Response({"error": "Database or repository error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                # Manejar cualquier otro error inesperado
                return Response({"error": "Unexpected error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            # Recuperar todos los registros
            try:
                [[ entity_name|decapitalize_first ]]List = [[ entity_name|decapitalize_first ]]Service.list()

                # Serializar la lista de registros
                response_serializer_list = [[ entity_name|capitalize_first ]]DTOSerializer([[ entity_name|decapitalize_first ]]List, many=True)
                response_serializer_list.is_valid(raise_exception=True)

                # Retornar la respuesta con un estado HTTP 200 OK
                return Response(response_serializer_list.data, status=status.HTTP_200_OK)                          

            except ([[ entity_name|capitalize_first ]]ValueError) as e:
                # Manejar errores de validación si los datos no son válidos
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except (ConnectionDataBaseError, RepositoryError) as e:
                # Manejar errores de conexión a la base de datos o repositorio
                return Response({"error": "Database or repository error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                # Manejar cualquier otro error inesperado
                return Response({"error": "Unexpected error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @swagger_auto_schema(
        operation_summary="Create a new [[ entity_name|decapitalize_first ]]",
        operation_description="Create a new [[ entity_name|decapitalize_first ]] with the provided data",
        request_body=[[ entity_name|capitalize_first ]]DTOSerializer,
        responses={
            201: [[ entity_name|capitalize_first ]]DTOSerializer,
            400: "Bad Request"
        },
        tags=["[[ entity_name|decapitalize_first ]]"]
    )
    def post(self, request):
        """
        Maneja solicitudes POST para crear un nuevo registro.

        - Valida los datos entrantes.
        - Llama al servicio de creación para manejar la lógica de negocio.
        """
        
        # Datos enviados en el cuerpo de la solicitud
        serializer = [[ entity_name|capitalize_first ]]DTOSerializer(data=request.data) 
        if not serializer.is_valid():
            # Si la validación falla, retornar un error 400 BAD REQUEST
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Obtener el ID de la entidad relacionada si existe
        external_id = request.data.get('external_id', None)

        # Si se proporcionan IDs de entidades relacionadas, agregarlos
        externals = request.data.get('externals', None)

        [[ entity_name|decapitalize_first ]]Service = [[ entity_name|capitalize_first ]]Service() # Instanciar el servicio        

        try:
            # Llamar al servicio de creación con los datos proporcionados
            [[ entity_name|decapitalize_first ]] = [[ entity_name|decapitalize_first ]]Service.create(data=serializer.validated_data, external_id=external_id, externals=externals)
            # Serializar el nuevo registro creado
            response_serializer = [[ entity_name|capitalize_first ]]DTOSerializer([[ entity_name|decapitalize_first ]])
            response_serializer.is_valid(raise_exception=True)

            # Retornar la respuesta con un estado HTTP 201 CREATED
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except [[ entity_name|capitalize_first ]]AlreadyExistsError as e:
            # Manejar errores si ya existe un registro con el mismo nombre
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ([[ entity_name|capitalize_first ]]ValueError, [[ entity_name|capitalize_first ]]ValidationError) as e:
            # Manejar errores de validación si los datos no son válidos
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (ConnectionDataBaseError, RepositoryError) as e:
            # Manejar errores de conexión a la base de datos o repositorio
            return Response({"error": "Database or repository error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Manejar cualquier otro error inesperado
            return Response({"error": "Unexpected error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @swagger_auto_schema(
        operation_summary="Update an existing [[ entity_name|decapitalize_first ]]",
        operation_description="Update an existing [[ entity_name|decapitalize_first ]] with the provided ID and data",
        request_body=[[ entity_name|capitalize_first ]]DTOSerializer,
        responses={
            200: [[ entity_name|capitalize_first ]]DTOSerializer,
            400: "Bad Request",
            404: "Not Found"
        },
        tags=["[[ entity_name|decapitalize_first ]]"]
    )
    def put(self, request, id):
        """
        Maneja solicitudes PUT para actualizar un registro existente.

        - Valida los datos entrantes.
        - Llama al servicio de actualización para manejar la lógica de negocio.
        """

        # Datos enviados en el cuerpo de la solicitud
        serializer = [[ entity_name|capitalize_first ]]DTOSerializer(data=request.data) 
        if not serializer.is_valid():
            # Si la validación falla, retornar un error 400 BAD REQUEST
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Obtener el ID de la entidad relacionada si existe
        external_id = request.data.get('external_id', None)

        # Si se proporcionan IDs de entidades relacionadas, agregarlos
        externals = request.data.get('externals', None)       
        
        [[ entity_name|decapitalize_first ]]Service = [[ entity_name|capitalize_first ]]Service() # Instanciar el servicio        

        try:
            # Llamar al servicio de actualización con el ID y los nuevos datos
            [[ entity_name|decapitalize_first ]] = [[ entity_name|decapitalize_first ]]Service.update(entity_id=id, data=serializer.validated_data, external_id=external_id, externals=externals)

            # Serializar el registro actualizado
            response_serializer = [[ entity_name|capitalize_first ]]DTOSerializer([[ entity_name|decapitalize_first ]])
            response_serializer.is_valid(raise_exception=True)

            # Retornar la respuesta con un estado HTTP 200 OK
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except [[ entity_name|capitalize_first ]]NotFoundError as e:
            # Manejar errores si no se encuentra el registro con el ID dado
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ([[ entity_name|capitalize_first ]]ValueError, [[ entity_name|capitalize_first ]]ValidationError) as e:
            # Manejar errores de validación si los datos no son válidos
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (ConnectionDataBaseError, RepositoryError) as e:
            # Manejar errores de conexión a la base de datos o repositorio
            return Response({"error": "Database or repository error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Manejar cualquier otro error inesperado
            return Response({"error": "Unexpected error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @swagger_auto_schema(
        operation_summary="Delete an existing [[ entity_name|decapitalize_first ]]",
        operation_description="Delete an existing [[ entity_name|decapitalize_first ]] with the provided ID",
        responses={
            204: "No Content",
            400: "Bad Request",
            404: "Not Found"
        },
        tags=["[[ entity_name|decapitalize_first ]]"]
    )
    def delete(self, request, id):
        """
        Maneja solicitudes DELETE para eliminar un registro existente.

        - Valida el ID proporcionado.
        - Llama al servicio de eliminación para manejar la lógica de negocio.
        """
        
        [[ entity_name|decapitalize_first ]]Service = [[ entity_name|capitalize_first ]]Service() # Instanciar el servicio
        
        try:
            # Llamar al servicio de eliminación con el ID proporcionado
            [[ entity_name|decapitalize_first ]] = [[ entity_name|decapitalize_first ]]Service.delete(entity_id=id)

            # Retornar una respuesta sin contenido con estado HTTP 204 NO CONTENT
            return Response(status=status.HTTP_204_NO_CONTENT)

        except [[ entity_name|capitalize_first ]]NotFoundError as e:
            # Manejar errores si no se encuentra el registro con el ID dado
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ([[ entity_name|capitalize_first ]]ValueError, [[ entity_name|capitalize_first ]]ValidationError) as e:
            # Manejar errores de validación si el ID no es válido
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (ConnectionDataBaseError, RepositoryError) as e:
            # Manejar errores de conexión a la base de datos o repositorio
            return Response({"error": "Database or repository error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Manejar cualquier otro error inesperado
            return Response({"error": "Unexpected error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
