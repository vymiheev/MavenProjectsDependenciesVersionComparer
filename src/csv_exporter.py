import csv

from src import settings


class Lib:
    def __init__(self, group_id, artifact_id):
        self.group_id = group_id
        self.artifact_id = artifact_id

    def __eq__(self, __value):
        return isinstance(__value, self.__class__) and self.group_id == __value.group_id \
            and self.artifact_id == __value.artifact_id

    def __hash__(self):
        return hash((self.group_id, self.artifact_id))

    def __repr__(self):
        return f"Lib({self.group_id}:{self.artifact_id})"

    def __str__(self):
        return f"{self.group_id}:{self.artifact_id}"


class CSVExporter:
    def __init__(self, apps):
        self.apps = apps
        self.apps_name = []
        self.lib2app = {}

        self.__prepare_data()

    def __prepare_data(self):
        for app in self.apps:
            if app.name in settings.IGNORE_APPLICATIONS:
                continue
            self.apps_name.append(app.name)
            for module in app.modules:
                for dependency in module.deps:
                    if dependency.group_id in settings.IGNORE_GROUP_ID:
                        continue
                    lib = Lib(dependency.group_id, dependency.artifact_id)
                    if lib not in self.lib2app:
                        self.lib2app[lib] = {app.name: dependency.version}
                    else:
                        self.lib2app[lib][app.name] = dependency.version

        self.lib2app = dict(sorted(self.lib2app.items(), key=lambda item: (len(item[1]), item[0].group_id, item[0].artifact_id), reverse=True))


    def export_to_csv(self, csv_file_path=settings.EXPORT_FILE_PATH):
        with open(csv_file_path + '.csv', mode='w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(['GroupID:ArtifactID'] + self.apps_name)
            for lib, app_dict in self.lib2app.items():
                row = [str(lib)]
                for app in self.apps:
                    if app.name in app_dict:
                        row.append(app_dict[app.name])
                    else:
                        row.append("NotExist")
                writer.writerow(row)
