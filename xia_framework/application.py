import argparse
import subprocess
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

    def prepare(self, env_name: str = "base", skip_terraform: bool = False):
        self.install_requirements()
        self.load_modules()
        if env_name != "base":
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
        module_dict[module_name] = {"package": package_name, "class": None, "events": {"deploy": None}}
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

    def terraform_get_state_file_prefix(self, env_name: str = None):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        environment_settings = landscape_dict["environments"]
        if env_name not in environment_settings:
            raise ValueError(f"Environment {env_name} not defined in landscape.yaml")
        current_settings = landscape_dict["settings"]
        realm_name = current_settings["realm_name"]
        foundation_name = current_settings["foundation_name"]
        application_name = current_settings["application_name"]
        return f"{realm_name}/_/{foundation_name}/{application_name}/{env_name}/terraform/state"


def main():
    # Top level parser
    parser = argparse.ArgumentParser(description='Application tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create the parser for the "prepare" command
    sub_parser = subparsers.add_parser('init-module', help='Initialization of a new module')
    sub_parser.add_argument('-n', '--module-uri', type=str,
                            help='Module uri to be added in format: <package_name>@<version>/<module_name>')

    sub_parser = subparsers.add_parser('plan', help='Prepare Application Deploy time objects')
    sub_parser.add_argument('-e', '--env_name', type=str, help='Environment Name')

    sub_parser = subparsers.add_parser('apply', help='Prepare Application Deploy time objects')
    sub_parser.add_argument('-e', '--env_name', type=str, help='Environment Name')
    sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve apply automatically')

    sub_parser = subparsers.add_parser('destroy', help='Prepare Application Deploy time objects')
    sub_parser.add_argument('-e', '--env_name', type=str, help='Environment Name')
    sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve destroy automatically')

    # Parse the arguments
    args = parser.parse_args()

    # Handle different commands
    application = Application()
    if args.command == "init-module":
        application.init_module(module_uri=args.module_uri)
    elif args.command == "plan":
        application.prepare(env_name=args.env_name, skip_terraform=True)
    elif args.command == "apply":
        application.prepare(env_name=args.env_name, skip_terraform=True)
        application.terraform_init(env=args.env_name)
        application.terraform_apply(env=args.env_name, auto_approve=args.auto_approve)
    elif args.command == "destroy":
        application.prepare(env_name=args.env_name, skip_terraform=True)
        application.terraform_destroy(env=args.env_name, auto_approve=args.auto_approve)
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
