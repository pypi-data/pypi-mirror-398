import os
from typing import Literal


EnvName = Literal["dev", "staging", "prod"]

def get_env_name() -> EnvName:
    env = os.getenv("ENV", "dev")

    if env in ["dev","staging", "prod"]:
        return env
    else:
        raise ValueError(
            f"'ENV' is set to: {env}. This is not a supported env! Please choose between: [dev, staging, prod]"
        )
