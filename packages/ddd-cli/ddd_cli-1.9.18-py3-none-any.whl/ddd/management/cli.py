import argparse
from ddd.management.commands.create_entity import CreateEntityCommand
from ddd.management.commands.create_service import CreateServiceCommand
from ddd.management.commands.create_repository import CreateRepositoryCommand
from ddd.management.commands.create_dto import CreateDTOCommand
from ddd.management.commands.create_serializer import CreateSerializerCommand
from ddd.management.commands.create_view_api_apiview import CreateViewApiApiViewCommand
from ddd.management.commands.create_view_api_viewset import CreateViewApiViewSetCommand
from ddd.management.commands.create_view import CreateViewCommand
from .version import version

class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description=f"CLI for DDD support in Python/Django projects v{version}")
        self.subparsers = self.parser.add_subparsers(dest="subcommand", help="Available subcommands")

        # Registro de subcomandos
        CreateEntityCommand(self.subparsers)
        CreateServiceCommand(self.subparsers)
        CreateRepositoryCommand(self.subparsers)
        CreateDTOCommand(self.subparsers)
        CreateSerializerCommand(self.subparsers)
        CreateViewApiApiViewCommand(self.subparsers)
        CreateViewApiViewSetCommand(self.subparsers)
        CreateViewCommand(self.subparsers)

    def run(self):
        args = self.parser.parse_args()
        if not args.subcommand:
            self.parser.print_help()
        else:
            # Ejecutar el subcomando seleccionado
            args.func(args)

def main():
    CLI().run()            

if __name__ == "__main__":
    main()
