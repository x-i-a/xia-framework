import argparse
import subprocess
import importlib
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

    @classmethod
    def _config_replace(cls, lines: list, replace_dict: dict):
        """Configuration file line replace

        Args:
            lines: line list of configuration file
            replace_dict: replacement dictionary (example {"key:", "key: value"})

        Returns:
            replaced key value
        """
        new_lines = []
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line.startswith("#"):
                new_lines.append(line)
                continue
            stripped_line = stripped_line[1:].strip()
            key_word_found = False
            print(stripped_line)
            for key_word, new_content in replace_dict.items():
                if stripped_line.startswith(key_word):
                    new_lines.append(line)
                    key_word_found = True
                    break
            if not key_word_found:
                new_lines.append(line)
        return new_lines

    def init_config(self):
        replace_dict = {
            "cosmos_name:": f"  cosmos_name: {CliGH.get_gh_action_var('cosmos_name')}",
            "realm_name:": f"  realm_name: {CliGH.get_gh_action_var('realm_name')}",
            "foundation_name:": f"  foundation_name: {CliGH.get_gh_action_var('foundation_name')}",
        }
        with open(self.landscape_yaml) as landscape_file:
            lines = landscape_file.readlines()
        new_lines = self._config_replace(lines, replace_dict)
        with open(self.landscape_yaml, "w") as landscape_file:
            landscape_file.writelines(new_lines)

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
