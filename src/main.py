import os

from src import find_pom, settings, parse_pom, csv_exporter
from src.beans import PomTraversalException
from src.csv_exporter import CSVExporter
from src.parse_pom import PomParser
from src.settings import GIT_ROOT_DIR


def check_settings():
    for it in [settings.GIT_ROOT_DIR, settings.EXPORT_ROOT_DIR]:
        if not os.path.isdir(it):
            raise PomTraversalException(f'{it} is not a directory.')


if "__main__" == __name__:
    check_settings()

    apps = find_pom.find_pom_files(GIT_ROOT_DIR)
    for app in apps:
        PomParser(app).parse()
    CSVExporter(apps).export_to_csv()
