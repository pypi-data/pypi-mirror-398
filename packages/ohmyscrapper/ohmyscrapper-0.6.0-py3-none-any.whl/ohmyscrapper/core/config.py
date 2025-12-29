import yaml
import os

def get_dir(param="ohmyscrapper"):
    parent_param = 'default_dirs'

    if param == "ohmyscrapper":
        folder = "./" + param
    else:
        folder = get_param(parent_param, param)
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder

def get_files(param):
    parent_param = 'default_files'
    return get_param(parent_param, param)

def get_db(param="db_file"):
    if param == 'folder':
        return get_dir(param='db')
    return get_param(parent_param = 'db', param=param)

def get_ai(param):
    return get_param(parent_param = 'ai', param=param)

def load_config(force_default=False):
    customize_folder = "ohmyscrapper"
    if not os.path.exists(customize_folder):
        os.mkdir(customize_folder)

    config_file = "config.yaml"
    config_file = os.path.join(customize_folder, config_file)
    if force_default or not os.path.exists(config_file):
        with open(config_file, "+w") as f:
            config_params = _default_config()
            f.write(yaml.safe_dump(config_params))
    else:
        with open(config_file, "r") as f:
            config_params = yaml.safe_load(f.read())

    if config_params is None or "default_dirs" not in config_params:
        config_params = load_config(force_default=True)

    return config_params


def get_param(parent_param, param):
    default_dirs = load_config()[parent_param]
    if param in default_dirs:
        return default_dirs[param]
    else:
        raise Exception(f"{param} do not exist in your params {parent_param}.")

def _default_config():
    return {
                "default_dirs": {
                    "input": "./input",
                    "output": "./output",
                    "db": "./db",
                    "prompts": "./prompts",
                    "templates": "./templates",
                },
                "db":
                {
                    "db_file": "local.db"
                },
                "ai":
                {
                    "default_prompt_file" :"prompt.md"
                },
                "default_files": {
                    "url_types" : "url_types.yaml"
                }
            }

def update():
    legacy_folder = "./customize"
    new_folder = "./ohmyscrapper"
    if os.path.exists(legacy_folder) and not os.path.exists(new_folder):
        yes_no = input("We detected a legacy folder system for your OhMyScrapper, would you like to update? \n" \
        "If you don't update, a new version will be used and your legacy folder will be ignored. \n" \
        "[Y] for yes or  any other thing to ignore: ")
        if yes_no == "Y":
            os.rename(legacy_folder,new_folder)
        print(" You are up-to-date! =)")
        print("")
