from .utils import *
from colorama import Fore, Style

class CreateSerializerCommand:
    def __init__(self, subparsers):
        parser = subparsers.add_parser('create-serializer', help='Create a new Serializer')
        parser.add_argument('app_path', type=str, help='The relative path of the app within the project (for example, "apps/app1")')
        parser.add_argument('serializer_name', type=str, help='The name of the Serializer')     
        parser.add_argument("--simulate", action="store_true", help="Simulate the creation of this entity without writing files")         
        parser.set_defaults(func=self.execute) 

    def execute(self, args):
        self.create_serializer(args.app_path, args.serializer_name, args.simulate)

    def create_serializer(self, app_path, serializer_name, simulate=False, **kwargs):
        """Crea un nuevo Serializer"""
        serializers_dir = os.path.join(app_path, 'serializers')
        serializers_path = os.path.join(serializers_dir, serializer_name.lower() + '_serializer.py')

        if not simulate:
            # Crear directorios si no existen
            try:
                os.makedirs(serializers_dir, exist_ok=True)
                create__init__files(serializers_dir)
                
            except OSError as e:
                print(Fore.RED + f"Failed to create directory '{serializers_dir}': {e}" + Style.RESET_ALL)
                return
            
            #si ya existe el archivo mostrar error
            if os.path.exists(serializers_path):
                print(Fore.RED + f"File '{serializers_path}' already exists. Cannot create separate file" + Style.RESET_ALL)
                return

        # Escribir imports en el archivo 
        # si no existe el archivo template_imports
        if not os.path.exists(serializers_path) or simulate:
            readWriteTemplate(
                templateName='serializer',
                fileName='imports.py',
                render_params={'serializer_name': serializer_name},
                repository_path=serializers_path,
                failIfError=True,
                simulate=simulate
            )

        readWriteTemplate(
            templateName='serializer',
            fileName='class.py',
            render_params={'serializer_name': serializer_name},
            repository_path=serializers_path,
            failIfError=True,
            addition=True,
            simulate=simulate
        )
      