import os
import tomllib
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(
  dotenv_path=".envrc",
  verbose=True,
)


def _get_bridge_version() -> str:
  return version("pantoqa_bridge")

  pyproject_path = Path(__file__).resolve().parents[1] / Path("pyproject.toml")
  with pyproject_path.open("rb") as f:
    data = tomllib.load(f)
  return data["project"]["version"]


SERVER_HOST = os.getenv("SERVER_HOST") or "0.0.0.0"
SERVER_PORT = int(os.getenv("SERVER_PORT") or "6565")

APPIUM_SERVER_HOST = os.getenv("APPIUM_SERVER_HOST") or SERVER_HOST
APPIUM_SERVER_PORT = int(os.getenv("APPIUM_SERVER_PORT") or "6566")
APPIUM_SERVER_URL = f"http://{APPIUM_SERVER_HOST}:{APPIUM_SERVER_PORT}"

EXT_VERSION = _get_bridge_version()
