import os
import argparse
import subprocess
import yaml
from ruamel.yaml import YAML
import re
import shutil
import importlib


class Base:
    BASE_ENV = "base"

    def __init__(self, config_dir: str = "config", **kwargs):
        self.run_book = {}
        self.yaml = YAML()
        yaml.preserve_quotes = True
        self.config_dir = config_dir
        self.module_dir = os.path.sep.join(["iac", "modules"])
        self.env_dir = os.path.sep.join(["iac", "environments"])
        self.landscape_yaml = os.path.sep.join([self.config_dir, "landscape.yaml"])
        self.module_yaml = os.path.sep.join([self.config_dir, "modules.yaml"])
        self.package_yaml = os.path.sep.join([self.config_dir, "packages.yaml"])

        # Temporary files
        self.requirements_txt = os.path.sep.join([self.config_dir, "requirements.txt"])
        self.package_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

    @classmethod
    def _parse_module_uri(cls, module_uri: str):
        pattern_1 = r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9\.]+/[a-zA-Z0-9_-]+$'
        pattern_2 = r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$'
        if not re.match(pattern_1, module_uri) and not re.match(pattern_2, module_uri):
            raise ValueError("Module name must be as format <package_name>@<version>/<module_name>")
        package_name, module_name = module_uri.split("/", 1)
        if "@" in package_name:
            package_name, version = package_name.split("@", 1)
        else:
            version = None
        return package_name, version, module_name

    def init_module(self, module_uri: str):
        """initialize a module

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
        module_dict[module_name] = {"package": package_name, "events": {"deploy": None}}
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
            with open(self.module_yaml, 'w') as module_file:
                self.yaml.dump(module_dict, module_file)

    def activate_module(self, module_uri: str, activate_scope: list = None, depends_on: list = None):
        """activate a module

        Args:
            module_uri (str): Module name as format <package_name>@<version>/<module_name>
            activate_scope (list): Activation Scope
            depends_on (list): Model dependency
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
        module_dict[module_name] = {"package": package_name, "events": {"activate": None}}
        module_config = module_dict[module_name]
        if activate_scope:
            module_config["activate_scope"] = activate_scope
        if depends_on:
            module_config["depends_on"] = activate_scope
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
            with open(self.module_yaml, 'w') as module_file:
                self.yaml.dump(module_dict, module_file)

    @classmethod
    def get_package_address(cls, package_name: str, package_version: str = None, git_https_url: str = None,
                            ignore_existed: bool = False):
        package_dir = package_name.replace("-", "_")
        if not ignore_existed and os.path.exists(f"./{package_dir}"):
            print(f"Found local package {package_name}: ./{package_dir}")
        elif not ignore_existed and os.path.exists(f"../{package_name}"):
            print(f"Found local package {package_name}: ../{package_name}")
        else:
            if git_https_url:
                if package_version:
                    package_address = (f"git+https://{git_https_url}/{package_name}"
                                       f"@{package_version}#egg={package_name}")
                else:
                    package_address = f"git+https://{git_https_url}/{package_name}#egg={package_name}"
            else:
                package_address = f"{package_name}=={package_version}" if package_version else package_name
            return package_address

    def get_needed_packages(self, ignore_existed: bool = False) -> dict:
        """Get needed packages in requirements.txt form

        Args:
            ignore_existed (bool): Do not check local packages

        """
        with open(self.package_yaml, 'r') as file:
            package_config = yaml.safe_load(file) or {}

        repo_dict = package_config.get("repositories", {})
        package_dict = package_config.get("packages", {})

        package_addresses = {}
        for package_name, package_config in package_dict.items():
            package_config = package_config if package_config else {}
            repository_name = package_config.get("repository", "default")
            repository_cfg = repo_dict.get(repository_name, {}) or {}
            package_version = package_config.get("version", None)
            git_https_url = repository_cfg.get("git_https", None)
            package_address = self.get_package_address(package_name, package_version, git_https_url)
            if package_address:
                package_addresses[package_name] = package_address
        return package_addresses

    def update_requirements(self):
        needed_packages = self.get_needed_packages()

        requirements_content = "\n".join(needed_packages.values())
        with open(self.requirements_txt, 'w') as file:
            print(f"Requirement File Generated Dynamically: \n{requirements_content}")
            file.write(requirements_content)

    def install_requirements(self):
        requirements_existed = os.path.exists(self.requirements_txt)
        if not requirements_existed:
            self.update_requirements()
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        pip_index_url = landscape_dict.get("settings", {}).get("pip_index_url", "https://pypi.org/simple")
        subprocess.run(['pip', 'install', '-r', self.requirements_txt,
                        f"--index-url={pip_index_url}"], check=True)
        if not requirements_existed:
            os.remove(self.requirements_txt)

    def prepare(self, env_name: str = None, skip_terraform: bool = False):
        env_name = env_name if env_name else self.BASE_ENV
        self.update_requirements()
        self.install_requirements()
        self.load_modules()
        self.enable_environments(env_name)
        if not skip_terraform:
            self.terraform_init(env_name)
            self.terraform_apply(env_name)

    def terraform_get_state_file_prefix(self, env_name: str = None):
        raise NotImplementedError

    def terraform_init(self, env: str):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        bucket_name = current_settings.get("bucket_name", current_settings["cosmos_name"])
        # bucket_name = current_settings["realm_name"] + "_" + current_settings["foundation_name"]
        tf_init_cmd = (f'terraform -chdir=iac/environments/{env} init '
                       f'-backend-config="bucket={bucket_name}" '
                       f'-backend-config="prefix={self.terraform_get_state_file_prefix(env)}"')
        print(tf_init_cmd)
        subprocess.run(tf_init_cmd, shell=True)

    def terraform_apply(self, env: str, auto_approve: bool = False):
        auto_approve_cmd = "--auto-approve " if auto_approve else ""
        tf_apply_cmd = f'terraform {auto_approve_cmd} -chdir=iac/environments/{env} apply'
        subprocess.run(tf_apply_cmd, shell=True)

    def terraform_plan(self, env: str):
        tf_plan_cmd = f'terraform -chdir=iac/environments/{env} plan'
        subprocess.run(tf_plan_cmd, shell=True)

    def terraform_destroy(self, env: str, auto_approve: bool = False):
        auto_approve_cmd = "--auto-approve " if auto_approve else ""
        tf_destroy_cmd = f'terraform {auto_approve_cmd} -chdir=iac/environments/{env} destroy'
        subprocess.run(tf_destroy_cmd, shell=True)

    def load_modules(self):
        """Loading all modules

        Returns:

        """
        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}
        # Step 1: Get All Module Class
        for module_name, module_config in module_dict.items():
            module_obj = importlib.import_module(module_config["package"].replace("-", "_"))
            module_class_name = getattr(module_obj, "modules", {})[module_name]
            module_class = getattr(module_obj, module_class_name)
            module_config["_class"] = module_class

        # Step 2: Apply Events
        for module_name, module_config in module_dict.items():
            module_instance = module_config["_class"]()
            for event, event_cfg in module_config.get("events", {}).items():
                event_cfg = {} if not event_cfg else event_cfg
                if event == "deploy":
                    module_instance.enable(self.module_dir, **event_cfg)
                elif event == "activate":
                    module_instance.activate(self.module_dir, **event_cfg)

    def enable_environments(self, env: str):
        if os.path.exists(os.path.join(self.env_dir, env)):
            print(f"Local environment {env} found")
        else:
            shutil.copytree(os.path.join(self.env_dir, "base"), os.path.join(self.env_dir, env))

    def main(self):
        parser = argparse.ArgumentParser(description=f'{self.__class__.__name__} tools')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Create the sub-parsers
        for cmd in self.run_book:
            self.run_book[cmd]["cli"](subparsers=subparsers)

        # Parse the arguments
        args = parser.parse_args()

        # Run the command
        if args.command in self.run_book:
            self.run_book[args.command]["run"](args)
        else:
            parser.print_help()
