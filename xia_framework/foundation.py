import os
import shutil
import subprocess
import importlib
import yaml
from xia_framework.framework import Framework


class Foundation(Framework):
    def __init__(self, config_dir: str = "config", **kwargs):
        super().__init__(config_dir=config_dir, **kwargs)
        self.module_dir = os.path.sep.join(["iac", "modules"])
        self.env_dir = os.path.sep.join(["iac", "environments"])
        self.application_yaml = os.path.sep.join([self.config_dir, "applications.yaml"])

    def create_backend(self, foundation_name: str):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        if not current_settings.get("cosmos_name", ""):
            raise ValueError("Cosmos Name must be defined")
        if not foundation_name:
            raise ValueError("Foundation name must be provided")
        bucket_name = current_settings["realm_name"] + "_" + foundation_name
        foundation_region = current_settings.get("foundation_region", "eu")
        bucket_project = current_settings['cosmos_name']
        check_bucket_cmd = f"gsutil ls -b gs://{bucket_name}"
        r = subprocess.run(check_bucket_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if "AccessDeniedException" not in r.stderr and "NotFound" not in r.stderr:
            print(f"Bucket {bucket_name} already exists")
        else:
            create_bucket_cmd = f"gsutil mb -l {foundation_region} -p {bucket_project} gs://{bucket_name}/"
            r = subprocess.run(create_bucket_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            if "ERROR" not in r.stderr:
                print(f"Bucket {bucket_name} create successfully")
                current_settings["foundation_name"] = foundation_name
                if not current_settings.get("project_prefix", ""):
                    current_settings["project_prefix"] = foundation_name + "-"
                with open(self.landscape_yaml, 'w') as file:
                    yaml.dump(landscape_dict, file, default_flow_style=False, sort_keys=False)
            else:
                print(r.stderr)

    def birth(self, foundation_name: str):
        """Creation of a foundation

        Args:
            foundation_name: name of foundation
        """
        self.create_backend(foundation_name)
        # self.terraform_init('prd')
        # self.register_module("gcp-module-project", "Project")
        # self.register_module("gcp-module-application", "Application")
        # self.update_requirements()
        # self.install_requirements()
        # self.enable_modules()

    def prepare(self, skip_terraform: bool = False):
        self.update_requirements()
        self.install_requirements()
        self.load_modules()
        self.enable_environments("prd")
        if not skip_terraform:
            self.terraform_init("prd")
            self.terraform_apply("prd")

    def register_module(self, module_name: str, package: str, module_class: str):
        if not self.package_pattern.match(package):
            return ValueError("Package name doesn't meet the required pattern")

        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}

        if module_name in module_dict:
            print(f"Module {module_name} already exists")
        else:
            module_dict[module_name] = {"package": package, "class": module_class}
            print(f"Module {module_name} Registered")

        with open(self.module_yaml, 'w') as file:
            yaml.dump(module_dict, file, default_flow_style=False, sort_keys=False)

    def update_requirements(self):
        needed_packages = self.get_needed_packages()

        requirements_content = "\n".join(needed_packages.values())
        with open(self.requirements_txt, 'w') as file:
            file.write(requirements_content)

    def install_requirements(self):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        pip_index_url = landscape_dict["settings"].get("pip_index_url", "https://pypi.org/simple")
        subprocess.run(['pip', 'install', '-r', self.requirements_txt,
                        f"--index-url={pip_index_url}"], check=True)

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

    def load_modules(self):
        """Loading all modules

        Returns:

        """
        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}
        # Step 1: Get All Module Class
        for module_name, module_config in module_dict.items():
            module_obj = importlib.import_module(module_config["package"].replace("-", "_"))
            module_class = getattr(module_obj, module_config["class"])
            module_config["_class"] = module_class
            module_config["_dependencies"] = module_class.activate_depends
        # Step 2: Fill Dependencies
        self._fill_full_dependencies(module_dict)
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}

        module_bindings = landscape_dict.get("modules", {})
        for module_name, module_binding in list(module_bindings.items()):
            app_names = module_binding.get("applications", [])
            for dependency in module_dict[module_name]["_dependencies"]:
                dependency = dependency.replace("-", "_")
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

    def init_module(self, module_name: str, package: str, module_class: str):
        self.register_module(module_name, package, module_class)
        self.update_requirements()
        self.install_requirements()

    def create_app(self, app_name: str):
        print(f"Creating application: {app_name}")

