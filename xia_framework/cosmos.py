import os
import argparse
import subprocess
import yaml
from xia_framework.application import Application
from xia_framework.singularity import GcpSingularity
from xia_framework.tools import CliGH


class Cosmos(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_book.update({
            "bigbang": {"cli": self.cli_bigbang, "run": self.cmd_bigbang},
            "activate-module": {"cli": self.cli_activate_module, "run": self.cmd_activate_module},
        })
        self.topology_dict = {
            "gcp": [GcpSingularity]
        }

    def init_config(self):
        github_owner_name = CliGH.get_gh_owner()
        landscape_replace_dict = {
            "repository_owner:": f"  repository_owner: {github_owner_name}\n",
        }
        self._config_replace(self.landscape_yaml, landscape_replace_dict)

        # Prepare common
        repo_dict = {"owner": CliGH.get_gh_owner(), "repo": CliGH.get_gh_repo()}
        var_dict = CliGH.get_gh_variable_dict()

        # Module level init-config
        self.update_requirements()
        self.install_requirements()
        module_dict = self.load_modules()
        for module_name, module_config in module_dict.items():
            module_instance = module_config["_class"]()
            module_instance.init_config(repo_dict=repo_dict, var_dict=var_dict)

    def bigbang(self):
        """Create the cosmos administration project
        """
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict["settings"] or {}

        # Step 1: Define Cosmos Topology
        if "cosmos_name" not in current_settings:
            current_settings["cosmos_name"] = os.getenv("COSMOS_NAME")
        assert current_settings["cosmos_name"], "cosmos name shouldn't be empty"

        topology_type = (landscape_dict.get("topology", {}) or {}).get("type", None)
        while not topology_type:
            topology_type = input("Please define cosmos topology: \n"
                                  "gcp: Using GCS Bucket of Google Cloud Platform to save Cosmos state \n"
                                  "Your choice [gcp]: \n") or "gcp"
            if topology_type not in self.topology_dict:
                print(f"Topology {topology_type} is not among {list(self.topology_dict)}")
                topology_type = None

        # Step 2: Get extra Settings
        for singularity in self.topology_dict[topology_type]:
            current_settings = singularity.get_inputs(input_dict=current_settings)

        landscape_replace_dict = {
            key + ":": f"  {key}: {value}\n" for key, value in current_settings.items()
        }
        landscape_replace_dict["type:"] = f"  type: {topology_type}\n"
        self._config_replace(self.landscape_yaml, landscape_replace_dict)

        # Step 3: Put Some variable in repository
        for key, value in current_settings.items():
            CliGH.set_gh_action_var(key, value)
        CliGH.set_gh_action_var("tf_bucket_name", current_settings["bucket_name"])

        # Step 4: Bigbang
        for singularity in self.topology_dict[topology_type]:
            singularity.bigbang(**current_settings)

    def terraform_get_state_file_prefix(self, env_name: str = None):
        return f"_/terraform/state"

    @classmethod
    def cli_bigbang(cls, subparsers):
        subparsers.add_parser('bigbang', help='Create Cosmos Singularity')

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
        self.bigbang()

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
        self.terraform_init(env=self.BASE_ENV)
        self.terraform_destroy(env=self.BASE_ENV, auto_approve=args.auto_approve)


if __name__ == "__main__":
    Cosmos().main()
