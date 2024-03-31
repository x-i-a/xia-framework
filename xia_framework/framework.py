import os
import subprocess
import yaml
import re


class Framework:
    def __init__(self, config_dir: str = "config", **kwargs):
        self.config_dir = config_dir
        self.landscape_yaml = os.path.sep.join([self.config_dir, "landscape.yaml"])
        self.module_yaml = os.path.sep.join([self.config_dir, "modules.yaml"])
        self.package_yaml = os.path.sep.join([self.config_dir, "packages.yaml"])

        # Temporary files
        self.requirements_txt = os.path.sep.join([self.config_dir, "requirements.txt"])
        self.package_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

    def get_needed_packages(self, ignore_existed: bool = False) -> dict:
        """Get needed packages in requirements.txt form

        Args:
            ignore_existed (bool): Do not check local packages

        """
        with open(self.package_yaml, 'r') as file:
            package_config = yaml.safe_load(file) or {}

        repo_dict = package_config.get("repositories", {})
        package_dict = package_config.get("packages", {})

        package_addresses = {}
        for package_name, package_config in package_dict.items():
            package_config = package_config if package_config else {}
            repository_name = package_config.get("repository", "default")
            repository_cfg = repo_dict.get(repository_name, {}) or {}
            package_dir = package_name.replace("-", "_")
            if not ignore_existed and os.path.exists(f"./{package_dir}"):
                print(f"Found local package {package_name}: ./{package_dir}")
            elif not ignore_existed and os.path.exists(f"../{package_name}"):
                print(f"Found local package {package_name}: ../{package_name}")
            else:
                package_version = package_config.get("version", None)
                git_https_url = repository_cfg.get("git_https", None)
                if git_https_url:
                    if package_version:
                        package_address = (f"git+https://{git_https_url}/{package_name}"
                                           f"@{package_version}#egg={package_name}")
                    else:
                        package_address = f"git+https://{git_https_url}/{package_name}#egg={package_name}"
                else:
                    package_address = f"{package_name}=={package_version}" if package_version else package_name
                package_addresses[package_name] = package_address
        return package_addresses

    def terraform_init(self, env: str):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        bucket_name = current_settings["cosmos_name"]
        # bucket_name = current_settings["realm_name"] + "_" + current_settings["foundation_name"]
        tf_init_cmd = (f'terraform -chdir=iac/environments/{env} init '
                       f'-backend-config="bucket={bucket_name}" '
                       f'-backend-config="prefix=terraform/state"')
        print(tf_init_cmd)
        subprocess.run(tf_init_cmd, shell=True)

    def terraform_apply(self, env: str):
        tf_apply_cmd = f'terraform -chdir=iac/environments/{env} apply'
        subprocess.run(tf_apply_cmd, shell=True)

    def terraform_plan(self, env: str):
        tf_plan_cmd = f'terraform -chdir=iac/environments/{env} plan'
        subprocess.run(tf_plan_cmd, shell=True)