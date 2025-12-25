import os
from configparser import ConfigParser


def load_config(filename="database.ini", section="postgresql"):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        current_file_path = os.path.abspath(filename)
        raise Exception(
            "Section {0} not found in the {1} file".format(section, current_file_path)
        )

    return config
