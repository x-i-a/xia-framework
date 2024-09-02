import subprocess


class CliGH:
    @classmethod
    def get_gh_action_var(cls, variable_name: str, env_name: str = None):
        get_variable_cmd = f"gh variable get {variable_name}"
        if env_name:
            get_variable_cmd += f" -e {env_name}"
        r = subprocess.run(get_variable_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        return r.stdout.strip() if "was not found" not in r.stderr else None
