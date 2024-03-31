import importlib
import yaml
from xia_framework.framework import Framework


class Application(Framework):
    def prepare(self, skip_terraform: bool = False):
        self.update_requirements()
        self.install_requirements()

    def create(self, module_name: str):
        """Create a module

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
