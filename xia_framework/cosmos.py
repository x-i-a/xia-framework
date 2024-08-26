import os
import argparse
import subprocess
import yaml
from xia_framework.framework import Framework


class Cosmos(Framework):
    COSMOS_ENV = 'prd'  # Cosmos default environment name

    def bigbang(self, cosmos_name: str):
        """Create the cosmos administration project

        TODO:
            * Activate Cloud Billing API during cosmos project creation
            * Activate Cloud Resource Manager API during cosmos project creation
            * Activate Identity and Access Management during cosmos project creation

        Args:
            cosmos_name (str): Cosmos Name
        """

        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        current_cosmos_name = current_settings.get("cosmos_name", "")
        if not cosmos_name:
            raise ValueError("Realm project must be provided")
        if current_cosmos_name and current_cosmos_name != cosmos_name:
            raise ValueError("Realm project doesn't match configured landscape.yaml")
        get_billing_cmd = f"gcloud billing accounts list --filter='open=true' --format='value(ACCOUNT_ID)' --limit=1"
        r = subprocess.run(get_billing_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        current_settings["billing_account"] = r.stdout if "ERROR" not in r.stderr else None
        print(current_settings["billing_account"])
        check_project_cmd = f"gcloud projects list --filter='{cosmos_name}' --format='value(projectId)'"
        r = subprocess.run(check_project_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if cosmos_name in r.stdout:
            print(f"Realm Project {cosmos_name} already exists")
        else:
            create_proj_cmd = f"gcloud projects create {cosmos_name} --name='{cosmos_name}'"
            r = subprocess.run(create_proj_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            if "ERROR" not in r.stderr:
                print(f"Realm Project {cosmos_name} create successfully")
                current_settings["cosmos_name"] = cosmos_name
                with open(self.landscape_yaml, 'w') as file:
                    yaml.dump(landscape_dict, file, default_flow_style=False, sort_keys=False)
            else:
                print(r.stderr)

    def terraform_get_state_file_prefix(self, env_name: str = None):
        return f"_/terraform/state"

    def prepare(self, env: str = None, skip_terraform: bool = False):
        env = env if env else self.COSMOS_ENV
        self.update_requirements()
        self.install_requirements()
        self.load_modules()
        self.enable_environments(env)
        if not skip_terraform:
            self.terraform_init(env)
            self.terraform_apply(env)


def main():
    # Top level commands
    parser = argparse.ArgumentParser(description='Cosmos tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    sub_parser = subparsers.add_parser('bigbang', help='Create Cosmos Singularity')
    sub_parser.add_argument('-t', '--topology',
                            type=str, help='Cosmos topology', default="github:x-i-a/xia-cosmos-template")
    sub_parser.add_argument('-n', '--name', type=str, help='Cosmos Name')

    sub_parser = subparsers.add_parser('init-module', help='Initialization of a new module')
    sub_parser.add_argument('-n', '--module-uri', type=str,
                            help='Module uri to be added in format: <package_name>@<version>/<module_name>')

    sub_parser = subparsers.add_parser('activate-module', help='Activation of a new module to be used in foundation')
    sub_parser.add_argument('-n', '--module-uri', type=str,
                            help='Module name to be activated in format: <package_name>@<version>/<module_name>')

    subparsers.add_parser('plan', help='Prepare Cosmos Deploy time objects')

    sub_parser = subparsers.add_parser('apply', help='Prepare Cosmos Deploy time objects')
    sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve apply automatically')

    sub_parser = subparsers.add_parser('destroy', help='Destroy Cosmos Deploy time objects')
    sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve destroy automatically')

    # Parse the arguments
    args = parser.parse_args()

    # Handle different commands for the given Cosmos
    cosmos = Cosmos()
    if args.command == 'bigbang':
        cosmos.bigbang(cosmos_name=args.name)
        # cosmos.create(module_uri=args.module_name)
    elif args.command == "init-module":
        cosmos.init_module(module_uri=args.module_uri)
    elif args.command == "activate-module":
        cosmos.activate_module(module_uri=args.module_uri)
    elif args.command == "plan":
        cosmos.prepare(skip_terraform=True)
    elif args.command == "apply":
        cosmos.prepare(skip_terraform=True)
        cosmos.terraform_init(env=cosmos.COSMOS_ENV)
        cosmos.terraform_apply(env=cosmos.COSMOS_ENV, auto_approve=args.auto_approve)
    elif args.command == "destroy":
        cosmos.prepare(skip_terraform=True)
        cosmos.terraform_destroy(env=cosmos.COSMOS_ENV, auto_approve=args.auto_approve)
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
