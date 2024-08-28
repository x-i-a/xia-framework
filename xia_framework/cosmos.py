import os
import argparse
import subprocess
import yaml
from xia_framework.application import Application


class Cosmos(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_book.update({
            "bigbang": {"cli": self.cli_bigbang, "run": self.cmd_bigbang},
            "activate-module": {"cli": self.cli_activate_module, "run": self.cmd_activate_module},
        })

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

    @classmethod
    def cli_bigbang(cls, subparsers):
        sub_parser = subparsers.add_parser('bigbang', help='Create Cosmos Singularity')
        sub_parser.add_argument('-t', '--topology',
                                type=str, help='Cosmos topology', default="github:x-i-a/xia-cosmos-template")
        sub_parser.add_argument('-n', '--name', type=str, help='Cosmos Name')

    @classmethod
    def cli_activate_module(cls, subparsers):
        sub_parser = subparsers.add_parser('activate-module',
                                           help='Activation of a new module to be used in foundation')
        sub_parser.add_argument('-n', '--module-uri', type=str,
                                help='Module name to be activated in format: <package_name>@<version>/<module_name>')

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

    def cmd_bigbang(self, args):
        self.bigbang(cosmos_name=args.name)

    def cmd_activate_module(self, args):
        self.activate_module(module_uri=args.module_uri)

    def cmd_plan(self, args):
        return self.prepare(env_name=self.BASE_ENV, skip_terraform=True)

    def cmd_apply(self, args):
        self.prepare(env_name=self.BASE_ENV, skip_terraform=True)
        self.terraform_init(env=self.BASE_ENV)
        self.terraform_apply(env=self.BASE_ENV, auto_approve=args.auto_approve)

    def cmd_destroy(self, args):
        self.prepare(env_name=self.BASE_ENV, skip_terraform=True)
        self.terraform_destroy(env=self.BASE_ENV, auto_approve=args.auto_approve)


if __name__ == "__main__":
    Cosmos().main()
