import os
import subprocess
import yaml


class Framework:
    def __init__(self, config_dir: str = "config", **kwargs):
        self.config_dir = config_dir
        self.landscape_yaml = os.path.sep.join([self.config_dir, "landscape.yaml"])
        self.module_yaml = os.path.sep.join([self.config_dir, "modules.yaml"])

    def get_needed_packages(self, ignore_existed: bool = False) -> dict:
        """Get needed packages in requirements.txt form

        Args:
            ignore_existed (bool): Do not check local packages

        """
        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}

        package_dict = {}
        for module_name, module_config in module_dict.items():
            package_name = module_config["package"]
            package_dir = package_name.replace("-", "_")
            if package_name in package_dict:
                # Case 1: Package already configured, nothing to do
                continue
            elif not ignore_existed and os.path.exists(f"./{package_dir}"):
                print(f"Found local package {package_name}: ./{module_name}")
            elif not ignore_existed and os.path.exists(f"../{package_name}"):
                print(f"Found local package {package_name}: ../{package_name}")
            else:
                package_version = module_config.get("version", None)
                git_https_url = module_config.get("git_https", None)
                if git_https_url:
                    if package_version:
                        package_address = f"git+https://{git_https_url}@{package_version}#egg={package_name}"
                    else:
                        package_address = f"git+https://{git_https_url}#egg={package_name}"
                else:
                    package_address = f"{package_name}=={package_version}" if package_version else package_name
                package_dict[package_name] = package_address
            return package_dict

    def terraform_init(self, env: str):
        with open(self.landscape_yaml, 'r') as file:
            landscape_dict = yaml.safe_load(file) or {}
        current_settings = landscape_dict.get("settings", {})
        bucket_name = current_settings["realm_name"] + "_" + current_settings["foundation_name"]
        tf_init_cmd = f'terraform -chdir=iac/environments/{env} init -backend-config="bucket={bucket_name}"'
        subprocess.run(tf_init_cmd, shell=True)

    def terraform_apply(self, env: str):
        tf_apply_cmd = f'terraform -chdir=iac/environments/{env} apply'
        subprocess.run(tf_apply_cmd, shell=True)

    def terraform_plan(self, env: str):
        tf_plan_cmd = f'terraform -chdir=iac/environments/{env} plan'
        subprocess.run(tf_plan_cmd, shell=True)