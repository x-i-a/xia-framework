import json
import subprocess


class CliGH:
    @classmethod
    def get_gh_variable_dict(cls) -> dict:
        get_var_dict_cmd = f"gh variable list --json=name,value"
        r = subprocess.run(get_var_dict_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        var_record = json.loads(r.stdout.strip())
        var_dict = {line["name"].lower(): line["value"] for line in var_record}
        return var_dict

    @classmethod
    def get_gh_action_var(cls, variable_name: str, env_name: str = None):
        get_variable_cmd = f"gh variable get {variable_name}"
        if env_name:
            get_variable_cmd += f" -e {env_name}"
        r = subprocess.run(get_variable_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        return r.stdout.strip() if "was not found" not in r.stderr else None

    @classmethod
    def set_gh_action_var(cls, variable_name: str, variable_value: str, env_name: str = None):
        get_variable_cmd = f'gh variable set {variable_name} --body "{variable_value}"'
        if env_name:
            get_variable_cmd += f" -e {env_name}"
        r = subprocess.run(get_variable_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if "ERROR" not in r.stderr:
            print(f"Variable {variable_name} updated successfully")
        else:
            raise Exception(r.stderr)

    @classmethod
    def get_gh_owner(cls):
        get_owner_cmd = "gh repo view --json owner"
        r = subprocess.run(get_owner_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        owner_dict = json.loads(r.stdout)
        return owner_dict["owner"]["login"]

    @classmethod
    def get_gh_repo(cls):
        get_repo_cmd = "gh repo view --json name -q .name"
        r = subprocess.run(get_repo_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        return r.stdout.strip()
