import argparse
import subprocess
import importlib
import os
import yaml
from xia_framework.base import Base
from xia_framework.tools import CliGH


class Application(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_book.update({
            "init-config": {"cli": self.cli_init_config, "run": self.cmd_init_config},
            "init-module": {"cli": self.cli_init_module, "run": self.cmd_init_module},
            "plan": {"cli": self.cli_plan, "run": self.cmd_plan},
            "apply": {"cli": self.cli_apply, "run": self.cmd_apply},
            "destroy": {"cli": self.cli_destroy, "run": self.cmd_destroy},
        })

    def init_config(self):
        landscape_replace_dict = {
            "cosmos_name:": f"  cosmos_name: {CliGH.get_gh_action_var('cosmos_name')}\n",
            "realm_name:": f"  realm_name: {CliGH.get_gh_action_var('realm_name')}\n",
            "foundation_name:": f"  foundation_name: {CliGH.get_gh_action_var('foundation_name')}\n",
            "application_name:": f"  application_name: {CliGH.get_gh_action_var('app_name')}\n",
        }
        self._config_replace(self.landscape_yaml, landscape_replace_dict)
        tf_bucket_name = CliGH.get_gh_action_var('tf_bucket_name')
        if tf_bucket_name:
            tfstate_replace_dict = {
                "tf_bucket:": f"tf_bucket: {tf_bucket_name}\n",
            }
            tfstate_file_path = os.path.sep.join([self.config_dir, "core", "tfstate.yaml"])
            self._config_replace(tfstate_file_path, tfstate_replace_dict)
        gcp_project_prefix = CliGH.get_gh_action_var('gcp_project_prefix')
        if gcp_project_prefix:
            gcp_replace_dict = {
                "project_prefix:": f"project_prefix: {gcp_project_prefix}\n",
            }
            gcp_file_path = os.path.sep.join([self.config_dir, "platform", "gcp-project.yaml"])
            self._config_replace(gcp_file_path, gcp_replace_dict)

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

    @classmethod
    def cli_init_config(cls, subparsers):
        subparsers.add_parser('init-config', help='Initialization of configuration')

    @classmethod
    def cli_init_module(cls, subparsers):
        sub_parser = subparsers.add_parser('init-module', help='Initialization of a new module')
        sub_parser.add_argument('-n', '--module-uri', type=str,
                                help='Module uri to be added in format: <package_name>@<version>/<module_name>')

    @classmethod
    def cli_plan(cls, subparsers):
        sub_parser = subparsers.add_parser('plan', help=f'Prepare {cls.__name__} Deploy time objects')
        sub_parser.add_argument('-e', '--env_name', type=str, help='Environment Name')

    @classmethod
    def cli_apply(cls, subparsers):
        sub_parser = subparsers.add_parser('apply', help=f'Prepare {cls.__name__} Deploy time objects')
        sub_parser.add_argument('-e', '--env_name', type=str, help='Environment Name')
        sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve apply automatically')

    @classmethod
    def cli_destroy(cls, subparsers):
        sub_parser = subparsers.add_parser('destroy', help=f'Prepare {cls.__name__} Deploy time objects')
        sub_parser.add_argument('-e', '--env_name', type=str, help='Environment Name')
        sub_parser.add_argument('-y', '--auto-approve', type=str, help='Approve destroy automatically')

    def cmd_init_config(self, args):
        return self.init_config()

    def cmd_init_module(self, args):
        return self.init_module(module_uri=args.module_uri)

    def cmd_plan(self, args):
        return self.prepare(env_name=args.env_name, skip_terraform=True)

    def cmd_apply(self, args):
        self.prepare(env_name=args.env_name, skip_terraform=True)
        self.terraform_init(env=args.env_name)
        self.terraform_apply(env=args.env_name, auto_approve=args.auto_approve)

    def cmd_destroy(self, args):
        self.prepare(env_name=args.env_name, skip_terraform=True)
        self.terraform_init(env=args.env_name)
        self.terraform_destroy(env=args.env_name, auto_approve=args.auto_approve)


if __name__ == "__main__":
    Application().main()
