import os
import shutil
import subprocess
import yaml
from xia_framework.framework import Framework


class Foundation(Framework):
    def __init__(self, config_dir: str = "config", **kwargs):
        super().__init__(config_dir=config_dir, **kwargs)
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

    def init_module(self, module_name: str, package: str, module_class: str):
        self.register_module(module_name, package, module_class)
        self.update_requirements()
        self.install_requirements()

    def create_app(self, app_name: str):
        print(f"Creating application: {app_name}")

