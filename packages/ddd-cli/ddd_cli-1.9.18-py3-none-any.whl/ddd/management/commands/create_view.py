from .utils import *
from colorama import Fore, Style

class CreateViewCommand:
    def __init__(self, subparsers):      
        parser = subparsers.add_parser('create-view', help='Create a view for web')
        parser.add_argument('app_path', type=str, help='The relative path of the app within the project (for example, "apps/app1")')
        parser.add_argument('entity_name', type=str, help='The name of the entity')      
        parser.add_argument("--simulate", action="store_true", help="Simulate the creation of this entity without writing files")          
        parser.set_defaults(func=self.execute)           

    def execute(self, args):
        self.create_view(args.app_path, args.entity_name, args.simulate)

    def create_view(self, app_path, entity_name, simulate=False, **kwargs):
        """Crea una view para web"""
        # decodificar app_path 
        app_name, last_app_name, app_route, relative_app_path = decodeAppPath(app_path)

        views_dir = app_path
        views_templates_dir = os.path.join(views_dir, 'templates', relative_app_path)

        urls_path = os.path.join(views_dir, entity_name.lower() + '_urls.py')
        views_path = os.path.join(views_dir, entity_name.lower() + '_views.py')
        forms_path = os.path.join(views_dir, entity_name.lower() + '_forms.py')

        if not simulate:
            # Crear directorios si no existen
            try:
                os.makedirs(views_dir, exist_ok=True)
                create__init__files(views_dir)
                
                # Crear directorios de templates si no existen
                os.makedirs(views_templates_dir, exist_ok=True)

            except OSError as e:
                print(Fore.RED + f"Failed to create directory '{views_dir}': {e}" + Style.RESET_ALL)
                return    
            
            #si ya existe el archivo view mostrar error
            if os.path.exists(views_path):
                print(Fore.RED + f"The file '{views_path}' already exists" + Style.RESET_ALL)
                return
            
            #si ya existe el archivo form mostrar error
            if os.path.exists(forms_path):
                print(Fore.RED + f"The file '{forms_path}' already exists" + Style.RESET_ALL)
                return

        web_list_register_path = os.path.join(views_templates_dir, entity_name.lower() + '_web_list' + '.html')
        web_create_register_path = os.path.join(views_templates_dir, entity_name.lower() + '_web_create' + '.html')
        web_edit_register_path = os.path.join(views_templates_dir, entity_name.lower() +'_web_edit' + '.html')
        web_detail_register_path = os.path.join(views_templates_dir, entity_name.lower() + '_web_detail' + '.html')        
        web_form_errors_path = os.path.join(views_templates_dir, '_web_form_errors' + '.html') 
        web_global_errors_path = os.path.join(views_templates_dir, '_web_global_errors' + '.html') 

        if not simulate:
            #si ya existe el archivo web_create_register mostrar error
            if os.path.exists(web_create_register_path):
                print(Fore.RED + f"The file '{web_create_register_path}' already exists" + Style.RESET_ALL)
                return  

            #si ya existe el archivo web_edit_register mostrar error
            if os.path.exists(web_edit_register_path):
                print(Fore.RED + f"The file '{web_edit_register_path}' already exists" + Style.RESET_ALL)
                return

            #si ya existe el archivo web_list_register mostrar error
            if os.path.exists(web_list_register_path):
                print(Fore.RED + f"The file '{web_list_register_path}' already exists" + Style.RESET_ALL)
                return

            #si ya existe el archivo web_detail_register mostrar error
            if os.path.exists(web_detail_register_path):
                print(Fore.RED + f"The file '{web_detail_register_path}' already exists" + Style.RESET_ALL)
                return          

            # #si ya existe el archivo web_form_errors mostrar error
            # if os.path.exists(web_form_errors_path):
            #     print(Fore.RED + f"The file '{web_form_errors_path}' already exists" + Style.RESET_ALL)
            #     return

            # #si ya existe el archivo web_global_errors mostrar error
            # if os.path.exists(web_global_errors_path):
            #     print(Fore.RED + f"The file '{web_global_errors_path}' already exists" + Style.RESET_ALL)
            #     return                            

        #renderizar views
        readWriteTemplate(
            templateName='view',
            fileName='web_views.py',
            render_params={
                'app_path': app_path, 
                'app_name': app_name, 
                'last_app_name': last_app_name, 
                'app_route': app_route, 
                'relative_app_path': relative_app_path, 
                'entity_name': entity_name
            },
            repository_path=views_path,
            failIfError=True,
            simulate=simulate
        )

        #renderizar forms
        readWriteTemplate(
            templateName='view',
            fileName='web_forms.py',
            render_params={'entity_name': entity_name},
            repository_path=forms_path,
            failIfError=True,
            simulate=simulate
        )

        #renderizar urls
        readWriteTemplate(templateName='routers', fileName='web_urls.py',  render_params={'last_app_name':last_app_name, 'entity_name':entity_name}, repository_path=urls_path, failIfError=True, simulate=simulate)
        # print(f"Urls of Entity '{entity_name}' created at {urls_path}")

        #renderizar templates
        readWriteTemplate(templateName='templates', fileName='web_list_register.html',  render_params={'app_route':app_route, 'entity_name':entity_name, 'relative_app_path':relative_app_path}, repository_path=web_list_register_path, failIfError=True, simulate=simulate)
        # print(f"Template web_list of Entity '{entity_name}' created at {web_list_register_path}")

        readWriteTemplate(templateName='templates', fileName='web_create_register.html',  render_params={'app_route':app_route, 'entity_name':entity_name, 'relative_app_path':relative_app_path}, repository_path=web_create_register_path, failIfError=True, simulate=simulate)
        # print(f"Template web_create of Entity '{entity_name}' created at {web_create_register_path}")

        readWriteTemplate(templateName='templates', fileName='web_edit_register.html',  render_params={'app_route':app_route, 'entity_name':entity_name, 'relative_app_path':relative_app_path}, repository_path=web_edit_register_path, failIfError=True, simulate=simulate)
        # print(f"Template web_edit of Entity '{entity_name}' created at {web_edit_register_path}")

        readWriteTemplate(templateName='templates', fileName='web_detail_register.html',  render_params={'app_route':app_route, 'entity_name':entity_name, 'relative_app_path':relative_app_path}, repository_path=web_detail_register_path, failIfError=True, simulate=simulate)
        # print(f"Template web_detail of Entity '{entity_name}' created at {web_detail_register_path}")

        readWriteTemplate(templateName='templates', fileName='_web_form_errors.html',  render_params={}, repository_path=web_form_errors_path, failIfError=False, simulate=simulate)
        # print(f"Template web_form_errors of Entity '{entity_name}' created at {web_form_errors_path}")

        readWriteTemplate(templateName='templates', fileName='_web_global_errors.html',  render_params={}, repository_path=web_global_errors_path, failIfError=False, simulate=simulate)
        # print(f"Template web_global_errors of Entity '{entity_name}' created at {web_global_errors_path}")

