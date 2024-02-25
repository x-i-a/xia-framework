import os
import subprocess
import yaml
from xia_framework.framework import Framework


class Cosmos(Framework):
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
