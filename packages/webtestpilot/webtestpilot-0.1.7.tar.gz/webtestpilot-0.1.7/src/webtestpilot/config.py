import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv, load_dotenv
from baml_py import ClientRegistry


logger = logging.getLogger(__name__)
DEFAULT_CONFIG = {
    "executor": {
        "llm_clients": {
            "assertion_generation": "GPT_4_1",
            "assertion_api": "GPT_4_1",
            "action_proposer": "GPT_4_1",
            "ui_locator": "GUI_Grounding_Model",
            "page_reidentification": "GPT_4_1_mini",
        },
        "max_tries": 1,
    }
}


@dataclass(frozen=True)
class Config:
    assertion_generation: ClientRegistry
    assertion_api: ClientRegistry
    action_proposer: ClientRegistry
    action_proposer_name: str
    ui_locator: ClientRegistry
    page_reidentification: ClientRegistry

    max_tries: int

    @staticmethod
    def load(path: Path | str = None) -> "Config":
        # Load environment variables
        dotenv_path = find_dotenv(raise_error_if_not_found=False)
        load_dotenv(dotenv_path)

        # Load YAML config
        if path is not None:
            yaml_path = Path(path)
            with yaml_path.open("r") as f:
                yaml_data: dict[str, Any] = yaml.safe_load(f) or {}
        else:
            yaml_data = DEFAULT_CONFIG

        executor_clients = yaml_data["executor"]["llm_clients"]
        assertion_generation = ClientRegistry()
        assertion_generation.set_primary(executor_clients["assertion_generation"])

        assertion_api = ClientRegistry()
        assertion_api.set_primary(executor_clients["assertion_api"])

        action_proposer = ClientRegistry()
        action_proposer.set_primary(executor_clients["action_proposer"])

        ui_locator = ClientRegistry()
        ui_locator.set_primary(executor_clients["ui_locator"])

        page_reidentification = ClientRegistry()
        page_reidentification.set_primary(executor_clients["page_reidentification"])

        max_tries = yaml_data["executor"]["max_tries"]

        return Config(
            assertion_generation=assertion_generation,
            assertion_api=assertion_api,
            action_proposer_name=executor_clients["action_proposer"],
            action_proposer=action_proposer,
            ui_locator=ui_locator,
            page_reidentification=page_reidentification,
            max_tries=max_tries,
        )
