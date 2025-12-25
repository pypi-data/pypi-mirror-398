
from .utils import *
from colorama import Fore, Style
import os
from .create_serializer import CreateSerializerCommand

class CreateViewApiViewSetCommand:
    def __init__(self, subparsers):
        parser = subparsers.add_parser('create-view-api-viewset', help='Create a view for api based on ViewSet')
        parser.add_argument('app_path', type=str, help='The relative path of the app within the project (for example, "apps/app1")')
        parser.add_argument('entity_name', type=str, help='The name of the entity')  
        parser.add_argument("--simulate", action="store_true", help="Simulate the creation of this entity without writing files")         
        parser.set_defaults(func=self.execute)    

        # guardar el subparser para usarlo en el comando
        self.subparsers = subparsers                      

    def execute(self, args):
        self.create_view_api_viewset(args.app_path, args.entity_name, args.simulate)

    def create_view_api_viewset(self, app_path, entity_name, simulate=False, **kwargs):
        """Crea una view para api basada en ApiViewSet"""
        views_dir = app_path
        urls_path = os.path.join(views_dir, entity_name.lower() + '_urls.py')        
        views_path = os.path.join(views_dir, entity_name.lower() + '_views.py')

        if not simulate:
            # Crear directorios si no existen
            try:
                os.makedirs(views_dir, exist_ok=True)
                create__init__files(views_dir)
                
            except OSError as e:
                print(Fore.RED + f"Failed to create directory '{views_dir}': {e}" + Style.RESET_ALL)
                return    
            
            #si ya existe el archivo mostrar error
            if os.path.exists(views_path):
                print(Fore.RED + f"The file '{views_path}' already exists" + Style.RESET_ALL)
                return
        
        # decodficar app_path
        app_name, last_app_name, app_route, relative_app_path = decodeAppPath(app_path)

        #renderizar urls
        readWriteTemplate(templateName='routers', fileName='api_viewset_urls.py',  render_params={'entity_name':entity_name}, repository_path=urls_path, failIfError=True, simulate=simulate)  

        # Crear serializer
        serializer_command = CreateSerializerCommand(subparsers=self.subparsers)
        serializer_command.create_serializer(app_path=app_path, serializer_name=entity_name, simulate=simulate)                   

        readWriteTemplate(
            templateName='api',
            fileName='viewset_views.py',
            render_params={'app_name': app_name, 'entity_name': entity_name},
            repository_path=views_path,
            failIfError=True,
            simulate=simulate
        )