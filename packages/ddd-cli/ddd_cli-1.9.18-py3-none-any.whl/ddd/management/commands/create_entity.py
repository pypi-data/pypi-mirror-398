from .utils import *
from colorama import Fore, Style

class CreateEntityCommand:
    def __init__(self, subparsers):
        parser = subparsers.add_parser("create-entity", help="Create a new entity (DataClass or Pydantic)")
        parser.add_argument("app_path", type=str, help='The relative path of the app within the project (for example, "apps/app1")')
        parser.add_argument("entity_name", type=str, help="The name of the entity")
        parser.add_argument("--pydantic", action="store_true", help="Create a Pydantic structure for this entity")
        parser.add_argument("--simulate", action="store_true", help="Simulate the creation of this entity without writing files")
        parser.set_defaults(func=self.execute)     

    def execute(self, args):
        self.create_entity(args.app_path, args.entity_name, args.pydantic, args.simulate)

    def create_entity(self, app_path, entity_name, pydantic=False, simulate=False, **kwargs):
        """Crea una nueva entidad"""
        domain_dir = os.path.join(app_path, 'domain') 
        exceptions_path = os.path.join(domain_dir, entity_name.lower() + '_exceptions.py')        
        schemas_path = os.path.join(domain_dir, entity_name.lower() + '_schemas.py')

        entities_dir = os.path.join(app_path, 'domain') 
        entities_path = os.path.join(entities_dir, entity_name.lower() + '_entity.py')


        if not simulate:
            # Crear directorios si no existen
            try:
                os.makedirs(entities_dir, exist_ok=True)
                create__init__files(entities_dir)
                
            except OSError as e:
                print(Fore.RED + f"Failed to create directory '{entities_dir}': {e}" + Style.RESET_ALL)
                return
        
            #si ya existe el archivo mostrar error
            if os.path.exists(entities_path):
                print(Fore.RED + f"File '{entities_path}' already exists. Cannot create separate file" + Style.RESET_ALL)
                return

        # Escribir imports en el archivo 
        # si no existe el archivo template_imports
        if not os.path.exists(entities_path) or simulate:
            readWriteTemplate(
                templateName='entity',
                fileName='imports_dataclass.py' if not pydantic else 'imports_pydantic.py',
                render_params={'entity_name': entity_name},
                repository_path=entities_path,
                failIfError=True,
                simulate=simulate
            )

        #renderizar class
        readWriteTemplate(
            templateName='entity',
            fileName='class_dataclass.py' if not pydantic else 'class_pydantic.py',
            render_params={'entity_name': entity_name},
            repository_path=entities_path,
            failIfError=True,
            addition=True,
            simulate=simulate
        )     

        #renderizar exceptions
        readWriteTemplate(
            templateName='entity',
            fileName='exceptions.py',
            render_params={'entity_name': entity_name},
            repository_path=exceptions_path,
            failIfError=True,
            simulate=simulate
        )
        
        #renderizar schemas
        readWriteTemplate(
            templateName='entity',
            fileName='schemas_dataclass.py' if not pydantic else 'schemas_pydantic.py',
            render_params={},
            repository_path=schemas_path,
            failIfError=False,
            simulate=simulate
        )            
