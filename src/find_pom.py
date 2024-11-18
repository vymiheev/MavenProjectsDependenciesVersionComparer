import os

from src.beans import PomTraversalException, ApplicationPom, ModulePom


def __traverse_app_dirs(app_path):
    app_dir = os.path.basename(app_path)
    app = ApplicationPom(app_dir, app_path)

    for root, _, files in os.walk(app_path):
        for file in files:
            if file == "pom.xml":
                pom_path = os.path.join(root, file)
                module_name = os.path.basename(os.path.dirname(pom_path))
                module = ModulePom(module_name, pom_path)

                app.modules.append(module)
                print(f'Found module {module_name} for application {app_dir}')

    return app


def find_pom_files(search_path):
    if not os.path.isdir(search_path):
        raise PomTraversalException(f'{search_path} is not a directory.')

    search_path = os.path.abspath(search_path)
    apps = []
    app_dirs = os.listdir(search_path)
    for app_dir in app_dirs:
        app_path = os.path.join(search_path, app_dir)
        print(f"Looking into {app_path}...")
        app = __traverse_app_dirs(app_path)

        if len(app.modules) > 0:
            apps.append(app)
    return apps
