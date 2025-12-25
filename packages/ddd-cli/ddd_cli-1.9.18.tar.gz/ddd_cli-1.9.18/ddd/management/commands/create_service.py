from .utils import *
from colorama import Fore, Style

class CreateServiceCommand:
    def __init__(self, subparsers):
        parser = subparsers.add_parser("create-service", help='Create a new service')
        parser.add_argument("app_path", type=str, help='The relative path of the app within the project (for example, "apps/app1")')
        parser.add_argument("entity_name", type=str, help='The name of the entity')
        parser.add_argument("--simulate", action="store_true", help="Simulate the creation of this entity without writing files")        
        parser.set_defaults(func=self.execute)         

    def execute(self, args):
        self.create_service(args.app_path, args.entity_name, args.simulate)

    def create_service(self, app_path, entity_name="Entity", simulate=False, **kwargs):
        """Crea un nuevo servicio"""
        services_dir = os.path.join(app_path, 'services')
        services_path = os.path.join(services_dir, entity_name.lower() + '_service.py')

        if not simulate:
            # Crear directorios si no existen
            try:
                os.makedirs(services_dir, exist_ok=True)
                create__init__files(services_dir)
                
            except OSError as e:
                print(Fore.RED + f"Failed to create directory '{services_dir}': {e}" + Style.RESET_ALL)
                return
            
            #si ya existe el archivo mostrar error
            if os.path.exists(services_path):
                print(Fore.RED + f"The file '{services_path}' already exists. A separate file cannot be created" + Style.RESET_ALL)
                return

        # Escribir imports en el archivo 
        # si no existe el archivo template_imports
        if not os.path.exists(services_path) or simulate:
            readWriteTemplate(
                templateName='services',
                fileName='imports.py',
                render_params={'entity_name': entity_name},
                repository_path=services_path,
                failIfError=True,
                simulate=simulate
            )

        #renderizar class
        readWriteTemplate(
            templateName='services',
            fileName='class.py',
            render_params={'entity_name': entity_name},
            repository_path=services_path,
            failIfError=True,
            addition=True,
            simulate=simulate
        )
       