"""OS env and shell utils"""

import json
import os
import subprocess

from pathlib import Path

from .colors import colored
from .logs import logger
from .dicts import CaseInsensitiveDict


class OSEnver:
    def __init__(self, secrets_json=None):
        if not secrets_json:
            self.secrets_json = Path(__file__).parent / "secrets.json"
        else:
            self.secrets_json = secrets_json
        self.load_secrets()

    def load_secrets(self):
        self.secrets = CaseInsensitiveDict()
        try:
            with open(self.secrets_json, mode="r", encoding="utf-8") as rf:
                secrets = json.load(rf)
                for key, value in secrets.items():
                    self.secrets[key] = value
        except Exception as e:
            logger.warn(f"Loading local secrets: {e}")

    def __getitem__(self, key=None):
        if key:
            return self.secrets.get(key, os.getenv(key, None))
        else:
            return dict(self.secrets.items())


def shell_cmd(cmd, getoutput=False, showcmd=True, env=None):
    if showcmd:
        logger.info(colored(f"\n$ [{os.getcwd()}]", "light_blue"))
        logger.info(colored(f"  $ {cmd}\n", "light_cyan"))
    if getoutput:
        output = subprocess.getoutput(cmd)
        return output
    else:
        subprocess.run(cmd, shell=True, env=env)
