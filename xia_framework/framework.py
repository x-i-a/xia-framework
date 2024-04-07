import os
import subprocess
import yaml
from ruamel.yaml import YAML
import re
import shutil
import importlib


class Framework:
    def __init__(self, config_dir: str = "config", **kwargs):
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

    def terraform_init(self, env: str):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        bucket_name = current_settings["cosmos_name"]
        # bucket_name = current_settings["realm_name"] + "_" + current_settings["foundation_name"]
        tf_init_cmd = (f'terraform -chdir=iac/environments/{env} init '
                       f'-backend-config="bucket={bucket_name}" '
                       f'-backend-config="prefix=terraform/state"')
        print(tf_init_cmd)
        subprocess.run(tf_init_cmd, shell=True)

    def terraform_apply(self, env: str):
        tf_apply_cmd = f'terraform -chdir=iac/environments/{env} apply'
        subprocess.run(tf_apply_cmd, shell=True)

    def terraform_plan(self, env: str):
        tf_plan_cmd = f'terraform -chdir=iac/environments/{env} plan'
        subprocess.run(tf_plan_cmd, shell=True)

    @classmethod
    def _fill_full_dependencies(cls, module_dict: dict):
        counter = 1  # Trigger the first iteration
        while counter > 0:
            counter = 0
            for module_name, module_config in module_dict.items():
                for dependency in module_config["_dependencies"]:
                    for sub_dep in module_dict[dependency]["_dependencies"]:
                        if sub_dep not in module_config["_dependencies"]:
                            module_config["_dependencies"].append(sub_dep)
                            counter += 1

    @classmethod
    def _get_dependencies(cls, module_class):
        return module_class.activate_depends

    def load_modules(self):
        """Loading all modules

        Returns:

        """
        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}
        # Step 1: Get All Module Class
        for module_name, module_config in module_dict.items():
            module_obj = importlib.import_module(module_config["package"].replace("-", "_"))
            module_class_name = getattr(module_obj, "modules", {}).get(module_name, module_config["class"])
            module_class = getattr(module_obj, module_class_name)
            module_config["_class"] = module_class
            module_config["_dependencies"] = self._get_dependencies(module_class=module_class)
        # Step 2: Fill Dependencies
        self._fill_full_dependencies(module_dict)
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}

        module_bindings = landscape_dict.get("modules", {})
        for module_name, module_binding in list(module_bindings.items()):
            app_names = module_binding.get("applications", [])
            for dependency in module_dict[module_name]["_dependencies"]:
                if dependency not in module_bindings:
                    module_bindings[dependency] = {"applications": app_names.copy()}
                elif "applications" not in module_bindings[dependency]:
                    module_bindings[dependency]["applications"] = app_names.copy()
                else:
                    new_apps = [n for n in app_names if n not in module_bindings[dependency].get("applications", [])]
                    module_bindings[dependency]["applications"].extend(new_apps)
        with open(self.landscape_yaml, 'w') as file:
            yaml.dump(landscape_dict, file, default_flow_style=False, sort_keys=False)

        # Step 3: Apply Events
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

