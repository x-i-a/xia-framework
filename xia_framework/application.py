import importlib
import yaml
from xia_framework.framework import Framework


class Application(Framework):
    @classmethod
    def _fill_full_dependencies(cls, module_dict: dict):
        counter = 1  # Trigger the first iteration
        while counter > 0:
            counter = 0
            for module_name, module_config in module_dict.items():
                for dependency in module_config["_dependencies"]:
                    for sub_dep in module_dict[dependency.replace("-", "_")]["_dependencies"]:
                        if sub_dep.replace("-", "_") not in module_config["_dependencies"]:
                            module_config["_dependencies"].append(sub_dep.replace("-", "_"))
                            counter += 1

    @classmethod
    def _get_dependencies(cls, module_class):
        return module_class.deploy_depends

    def prepare(self, env_name: str = "", skip_terraform: bool = False):
        self.update_requirements()
        self.install_requirements()
        self.load_modules()
        if env_name:
            self.enable_environments(env_name)

    def create(self, module_name: str):
        """Initialize a module

        Args:
            module_name (str):
        """
        with open(self.module_yaml, 'r') as file:
            module_dict = yaml.safe_load(file) or {}
        if module_name not in module_dict:
            raise ValueError(f"Module {module_name} is not configured")
        module_config = module_dict[module_name]
        module_obj = importlib.import_module(module_config["package"].replace("-", "_"))
        module_class = getattr(module_obj, module_config["class"])
        module_instance = module_class()
        init_config = module_config.get("events", {}).get("init", {}) or {}
        module_instance.initialize(**init_config)
