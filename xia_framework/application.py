import argparse
import subprocess
import importlib
import yaml
from xia_framework.base import Base


class Application(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_book.update({
            "init-module": {"cli": self.cli_init_module, "run": self.cmd_init_module},
            "plan": {"cli": self.cli_plan, "run": self.cmd_plan},
            "apply": {"cli": self.cli_apply, "run": self.cmd_apply},
            "destroy": {"cli": self.cli_destroy, "run": self.cmd_destroy},
        })

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
        self.terraform_destroy(env=args.env_name, auto_approve=args.auto_approve)


if __name__ == "__main__":
    Application().main()
