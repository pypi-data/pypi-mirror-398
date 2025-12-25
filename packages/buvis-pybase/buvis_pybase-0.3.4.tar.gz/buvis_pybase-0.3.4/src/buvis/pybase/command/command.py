from pathlib import Path

import yaml
from buvis.pybase.adapters.console.console import console
from buvis.pybase.configuration.configuration import Configuration
from buvis.pybase.configuration.exceptions import ConfigurationKeyNotFoundError

FILENAME_COMMAND_INPUT_SPECIFICATION = "command_input_spec.yaml"


class BuvisCommand:
    def _setattr_from_config(
        self: "BuvisCommand",
        cfg: Configuration,
        child_module_path: str,
    ) -> None:
        input_spec_file = Path(child_module_path).parent.joinpath(
            FILENAME_COMMAND_INPUT_SPECIFICATION,
        )

        with input_spec_file.open("r") as input_spec_file:
            input_spec = yaml.safe_load(input_spec_file)

        for key, spec in input_spec.items():
            try:
                self.__setattr__(key, cfg.get_configuration_item(key, spec["default"]))
            except ConfigurationKeyNotFoundError as _:
                if spec.get("panic"):
                    console.panic(key["panic"])
