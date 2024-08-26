import os
import shutil
import subprocess
import argparse
import yaml
from xia_framework.framework import Framework


class Foundation(Framework):
    FOUNDATION_ENV = 'prd'  # Foundation default environment name

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

    def terraform_get_state_file_prefix(self):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        realm_name = current_settings["realm_name"]
        foundation_name = current_settings["foundation_name"]
        return f"{realm_name}/_/{foundation_name}/_/terraform/state"

    def prepare(self, env: str = None, skip_terraform: bool = False):
        env = env if env else self.FOUNDATION_ENV
        self.update_requirements()
        self.install_requirements()
        self.load_modules()
        self.enable_environments(env)
        if not skip_terraform:
            self.terraform_init(env)
            self.terraform_apply(env)

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

    def create_app(self, app_name: str):
        print(f"Creating application: {app_name}")


def main():
    # Top level parser
    parser = argparse.ArgumentParser(description='Foundation tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    sub_parser = subparsers.add_parser('init-module', help='Initialization of a new module')
    sub_parser.add_argument('-n', '--module-uri', type=str,
                            help='Module uri to be added in format: <package_name>@<version>/<module_name>')

    sub_parser = subparsers.add_parser('activate-module', help='Activation of a new module to be used in foundation')
    sub_parser.add_argument('-n', '--module-uri', type=str,
                            help='Module name to be activated in format: <package_name>@<version>/<module_name>')

    subparsers.add_parser('plan', help='Prepare Foundation Deploy time objects')

    sub_parser = subparsers.add_parser('apply', help='Prepare Foundation Deploy time objects')
    sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve apply automatically')

    sub_parser = subparsers.add_parser('destroy', help='Destroy Foundation Deploy time objects')
    sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve destroy automatically')

    # Parse the arguments
    args = parser.parse_args()

    # Handle different commands for the given Foundation
    foundation = Foundation()
    if args.command == "init-module":
        foundation.init_module(module_uri=args.module_uri)
    elif args.command == "activate-module":
        foundation.activate_module(module_uri=args.module_uri)
    elif args.command == "plan":
        foundation.prepare(skip_terraform=True)
    elif args.command == "apply":
        foundation.prepare(skip_terraform=True)
        foundation.terraform_init(env=foundation.FOUNDATION_ENV)
        foundation.terraform_apply(env=foundation.FOUNDATION_ENV, auto_approve=args.auto_approve)
    elif args.command == "destroy":
        foundation.terraform_destroy(env=foundation.FOUNDATION_ENV, auto_approve=args.auto_approve)
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
