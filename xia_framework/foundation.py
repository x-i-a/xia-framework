import os
import argparse
import subprocess
import yaml
from xia_framework.application import Application


class Foundation(Application):
    def __init__(self, config_dir: str = "config", **kwargs):
        super().__init__(config_dir=config_dir, **kwargs)
        self.application_yaml = os.path.sep.join([self.config_dir, "applications.yaml"])
        self.run_book.update({
            "activate-module": {"cli": self.cli_activate_module, "run": self.cmd_activate_module},
            "create-app": {"cli": self.cli_create_app, "run": self.cmd_create_app}
        })

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

    def terraform_get_state_file_prefix(self, env_name: str = None):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        realm_name = current_settings["realm_name"]
        foundation_name = current_settings["foundation_name"]
        return f"{realm_name}/_/{foundation_name}/_/terraform/state"

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

    def create_app(self, app_name: str, module_list: list, visibility: str = None,
                   repository_owner: str = None, repository_name: str = None,
                   template_owner: str = None, template_name: str = None):
        with open(self.module_yaml, 'r') as module_file:
            module_dict = self.yaml.load(module_file) or {}
        with open(self.application_yaml, 'r') as app_file:
            app_dict = self.yaml.load(app_file) or {}
        if app_name not in app_dict:
            raise ValueError(f"Application {app_name} already exists")
        params = {"visibility": visibility, "repository_owner": repository_owner, "repository_name": repository_name,
                  "template_owner": template_owner, "template_name": template_name}
        app_dict[app_name] = {k: v for k, v in params.items() if v}  # Removing None Value
        module_changed = False
        for module_name in module_list:
            if "activate" not in module_dict.get(module_name, {}).get("events", {}):
                raise ValueError(f"Module {module_name} is not activated yet")
            if "activate_scope" in module_dict[module_name]:
                module_dict[module_name]["activate_scope"].append(app_name)
            else:
                module_dict[module_name]["activate_scope"] = [app_name]
            module_changed = True
        # Save results
        if module_changed:
            with open(self.module_yaml, 'w') as module_file:
                self.yaml.dump(module_dict, module_file)
        with open(self.application_yaml, 'w') as app_file:
            self.yaml.dump(app_dict, app_file)

    @classmethod
    def cli_activate_module(cls, subparsers):
        sub_parser = subparsers.add_parser('activate-module',
                                           help='Activation of a new module to be used in foundation')
        sub_parser.add_argument('-n', '--module-uri', type=str,
                                help='Module name to be activated in format: <package_name>@<version>/<module_name>')

    @classmethod
    def cli_create_app(cls, subparsers):
        sub_parser = subparsers.add_parser('create_app',
                                           help='Creation of a new application')
        sub_parser.add_argument('-n', '--app-name', type=str, help='Application Name')
        sub_parser.add_argument('-m', '--modules', type=str, help='Needed module list for application')
        sub_parser.add_argument('-v', '--visibility', type=str, help='Application Visibility')
        sub_parser.add_argument('--repository-owner', type=str, help='Application Repository Owner')
        sub_parser.add_argument('--repository-name', type=str, help='Application Repository Name')
        sub_parser.add_argument('--template-owner', type=str, help='Template Owner')
        sub_parser.add_argument('--template-name', type=str, help='Template Name')

    @classmethod
    def cli_plan(cls, subparsers):
        subparsers.add_parser('plan', help=f'Prepare {cls.__name__} Deploy time objects')

    @classmethod
    def cli_apply(cls, subparsers):
        sub_parser = subparsers.add_parser('apply', help=f'Prepare {cls.__name__} Deploy time objects')
        sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve apply automatically')

    @classmethod
    def cli_destroy(cls, subparsers):
        sub_parser = subparsers.add_parser('destroy', help=f'Prepare {cls.__name__} Deploy time objects')
        sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve destroy automatically')

    def cmd_activate_module(self, args):
        self.activate_module(module_uri=args.module_uri)

    def cmd_create_app(self, args):
        module_list = [] if not args.modules else args.modules.split(" ")
        self.create_app(app_name=args.app_name, module_list=module_list, visibility=args.visibility,
                        repository_owner=args.repository_owner, repository_name=args.repository_name,
                        template_owner=args.template_owner, template_name=args.template_name)

    def cmd_plan(self, args):
        return self.prepare(env_name=self.BASE_ENV, skip_terraform=True)

    def cmd_apply(self, args):
        self.prepare(env_name=self.BASE_ENV, skip_terraform=True)
        self.terraform_init(env=self.BASE_ENV)
        self.terraform_apply(env=self.BASE_ENV, auto_approve=args.auto_approve)

    def cmd_destroy(self, args):
        self.prepare(env_name=self.BASE_ENV, skip_terraform=True)
        self.terraform_init(env=self.BASE_ENV)
        self.terraform_destroy(env=self.BASE_ENV, auto_approve=args.auto_approve)


if __name__ == "__main__":
    Foundation().main()
