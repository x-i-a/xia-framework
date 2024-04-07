import argparse
import subprocess
import importlib
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

    def create(self, module_uri: str):
        """Initialize a module

        Args:
            module_uri (str): Module name as format <package_name>@<version>/<module_name>
        """
        package_name, version, module_name = self._parse_module_uri(module_uri=module_uri)
        package_address = self.get_package_address(package_name=package_name, package_version=version)
        with open(self.module_yaml, 'r') as module_file:
            module_dict = self.yaml.load(module_file) or {}
        new_module = True if module_name not in module_dict else False
        if new_module:
            if package_address:
                # Installation of package
                subprocess.run(['pip', 'install', package_address], check=True)
        module_dict[module_name] = {"package": package_name,"class": None, "events": {"deploy": None}}
        module_config = module_dict[module_name]
        module_obj = importlib.import_module(module_config["package"].replace("-", "_"))
        module_class_name = getattr(module_obj, "modules", {}).get(module_name)
        module_class = getattr(module_obj, module_class_name)
        module_instance = module_class()
        init_config = module_config.get("events", {}).get("init", {}) or {}
        module_instance.initialize(**init_config)
        if new_module:
            # All goes well, should be safe to save the modified module configuration
            with open(self.package_yaml, 'r') as package_file:
                package_dict = self.yaml.load(package_file) or {}
            if package_name not in package_dict:
                if version:
                    package_dict["packages"][package_name] = {"version": version}
                else:
                    package_dict["packages"][package_name] = None
                with open(self.package_yaml, 'w') as package_file:
                    self.yaml.dump(package_dict, package_file)
            module_dict[module_name]["class"] = module_class_name
            with open(self.module_yaml, 'w') as module_file:
                self.yaml.dump(module_dict, module_file)


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
        application.create(module_uri=args.module_name)
    elif args.command == "prepare":
        application.prepare(env_name=args.env_name)
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
