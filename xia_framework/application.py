import argparse
import importlib
import yaml
from xia_framework.framework import Framework


class Application(Framework):
    @classmethod
    def _fill_full_dependencies(cls, module_dict: dict):
        counter = 1  # Trigger the first iteration
        while counter > 0:
            counter = 0
            for module_name, module_config in module_dict.items():
                for dependency in module_config["_dependencies"]:
                    for sub_dep in module_dict[dependency.replace("-", "_")]["_dependencies"]:
                        if sub_dep.replace("-", "_") not in module_config["_dependencies"]:
                            module_config["_dependencies"].append(sub_dep.replace("-", "_"))
                            counter += 1

    @classmethod
    def _get_dependencies(cls, module_class):
        return module_class.deploy_depends

    def prepare(self, env_name: str = "", skip_terraform: bool = False):
        self.install_requirements()
        self.load_modules()
        if env_name:
            self.enable_environments(env_name)

    def create(self, module_name: str):
        """Initialize a module

        Args:
            module_name (str): Module name as format <package_name>@<version>/<module_name>
        """
        package_name, module_name = module_name.split("/", 1)
        if "@" in package_name:
            package_name, version = package_name.split("@", 1)
        else:
            version = None
        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}
        if module_name not in module_dict:
            raise ValueError(f"Module {module_name} is not configured")
        module_config = module_dict[module_name]
        module_obj = importlib.import_module(module_config["package"].replace("-", "_"))
        module_class = getattr(module_obj, module_config["class"])
        module_instance = module_class()
        init_config = module_config.get("events", {}).get("init", {}) or {}
        module_instance.initialize(**init_config)


def main():
    # Top level parser
    parser = argparse.ArgumentParser(description='Application tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create the parser for the "prepare" command
    parser_create = subparsers.add_parser('init-module', help='Initialization of a new module')
    parser_create.add_argument('-n', '--module_name', type=str, help='Create files relates to module')

    parser_prepare = subparsers.add_parser('prepare', help='Prepare Modules for deploy')
    parser_prepare.add_argument('-e', '--env_name', type=str, help='Environment Name')

    # Parse the arguments
    args = parser.parse_args()

    # Handle different commands
    application = Application()
    if args.command == 'init-module':
        application.install_requirements()
        application.create(module_name=args.module_name)
    elif args.command == "prepare":
        application.prepare(env_name=args.env_name)
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
