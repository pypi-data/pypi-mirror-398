from .utils import *
from colorama import Fore, Style

class CreateDTOCommand:
    def __init__(self, subparsers):
        parser = subparsers.add_parser('create-dto', help='Create a new DTO (DataClass or Pydantic)')
        parser.add_argument('app_path', type=str, help='The relative path of the app within the project (for example, "apps/app1")')
        parser.add_argument('dto_name', type=str, help='The name of the DTO')
        parser.add_argument("--pydantic", action="store_true", help="Create a Pydantic structure for this dto")              
        parser.add_argument("--simulate", action="store_true", help="Simulate the creation of this entity without writing files")
        parser.set_defaults(func=self.execute) 

    def execute(self, args):
        self.create_dto(args.app_path, args.dto_name, args.pydantic, args.simulate)

    def create_dto(self, app_path, dto_name, pydantic=False, simulate=False, **kwargs):
        """Crea un nuevo DTO"""
        dtos_dir = os.path.join(app_path, 'dtos')
        dtos_path = os.path.join(dtos_dir, dto_name.lower() + '_dto.py')

        if not simulate:
            # Crear directorios si no existen
            try:
                os.makedirs(dtos_dir, exist_ok=True)
                create__init__files(dtos_dir)
                
            except OSError as e:
                print(Fore.RED + f"Failed to create directory '{dtos_dir}': {e}" + Style.RESET_ALL)
                return
            
            #si ya existe el archivo mostrar error
            if os.path.exists(dtos_path):
                print(Fore.RED + f"File '{dtos_path}' already exists. Cannot create separate file" + Style.RESET_ALL)
                return

        # Escribir imports en el archivo 
        # si no existe el archivo template_imports
        if not os.path.exists(dtos_path) or simulate:
            readWriteTemplate(
                templateName='dto',
                fileName='imports_dataclass.py' if not pydantic else 'imports_pydantic.py',
                render_params={'dto_name': dto_name},
                repository_path=dtos_path,
                failIfError=True,
                simulate=simulate
            )

        readWriteTemplate(
            templateName='dto',
            fileName='class_dataclass.py' if not pydantic else 'class_pydantic.py',
            render_params={'dto_name': dto_name},
            repository_path=dtos_path,
            failIfError=True,
            addition=True,
            simulate=simulate
        )
