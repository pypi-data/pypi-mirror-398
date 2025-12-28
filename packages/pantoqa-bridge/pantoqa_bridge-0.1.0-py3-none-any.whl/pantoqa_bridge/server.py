import os
import subprocess
from contextlib import asynccontextmanager
from shutil import which

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pantoqa_bridge.config import (APPIUM_SERVER_HOST, APPIUM_SERVER_PORT, EXT_VERSION,
                                   SERVER_HOST, SERVER_PORT)
from pantoqa_bridge.logger import logger
from pantoqa_bridge.routes.executor import route as executor_route
from pantoqa_bridge.routes.misc import route as misc_route
from pantoqa_bridge.utils.misc import (kill_process_sync, kill_self_process,
                                       start_appium_process_sync, wait_for_port_to_alive,
                                       watch_process_bg)


def create_app() -> FastAPI:
  logger.info(f"Starting PantoQA Extension {EXT_VERSION}")
  logger.info("Checking required tools...")
  _check_if_required_tools_installed()
  appium_pid = start_appium_process_sync()

  @asynccontextmanager
  async def lifespan(app: FastAPI):
    await wait_for_port_to_alive(APPIUM_SERVER_PORT, APPIUM_SERVER_HOST, timeout=15)
    watch_process_bg(appium_pid, on_exit=lambda _: kill_self_process())
    yield
    kill_process_sync(appium_pid, timeout=10)

  app = FastAPI(
    title="PantoAI QA Ext",
    lifespan=lifespan,
  )

  # Allow *.getpanto.ai, *.pantomax.co and localhost origins
  allow_origin_regex = r"(https://(([a-zA-Z0-9-]+\.)*pantomax\.co|([a-zA-Z0-9-]+\.)*getpanto\.ai)|http://localhost(:\d+)?)$"  # noqa: E501

  app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )
  app.include_router(misc_route)
  app.include_router(executor_route)
  return app


def start_bridge_server(host=SERVER_HOST, port=SERVER_PORT):
  try:
    app = create_app()
    uvicorn.run(
      app,
      host=host,
      port=port,
    )
  except DependencyNotInstalledError as e:
    logger.error(e)
  except Exception as e:
    logger.error(f"Failed to start server: {e}")


class DependencyNotInstalledError(Exception):
  pass


def _check_if_required_tools_installed():

  def _install_uiautomator2() -> None:
    subprocess.check_output(
      ["appium", "driver", "install", "uiautomator2"],
      stderr=subprocess.STDOUT,
      text=True,
    )

  def _install_appium() -> None:
    subprocess.check_output(
      ["npm", "install", "-g", "appium"],
      stderr=subprocess.STDOUT,
      text=True,
    )

  required_tools = [
    ("node", "node --version", "Node.js", None),
    ("npm", "npm --version", "npm", None),
    ("appium", "appium --version", "Appium", _install_appium),
  ]
  for cmd, version_cmd, name, install_func in required_tools:
    if which(cmd) is None:
      if not install_func:
        raise DependencyNotInstalledError(f"{name} is not installed or not found in PATH.")
      logger.info(f"[Check] {name} is not installed. Installing...")
      try:
        install_func()
        logger.info(f"[Check] {name} installed successfully.")
      except subprocess.CalledProcessError as e:
        raise DependencyNotInstalledError(f"Failed to install {name}: {e.output}") from e
    else:
      version_output = subprocess.check_output(version_cmd, shell=True, text=True).strip()
      logger.info(f"[Check] {name} found: {version_output}")

    # check if uiautomator2 server is installed
  uiautomator2_check = subprocess.check_output(
    "appium driver list --installed --json",
    shell=True,
    text=True,
  )
  if "uiautomator2" in uiautomator2_check:
    logger.info("[Check] Appium uiautomator2 driver is installed.")
  else:
    logger.info("[Check] Appium uiautomator2 driver is not installed. Installing...")
    try:
      _install_uiautomator2()
      logger.info("[Check] Appium uiautomator2 driver installed successfully.")
    except subprocess.CalledProcessError as e:
      raise DependencyNotInstalledError(
        f"Failed to install Appium uiautomator2 driver: {e.output}") from e

  android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
  adb_path = os.path.join(android_home, "platform-tools", "adb") if android_home else ""
  if adb_path and os.path.isfile(adb_path):
    logger.info(f"[Check] Android SDK found: {adb_path}")
  elif which("adb") is not None:
    logger.info(f"[Check] adb found in PATH: {which('adb')}")
  else:
    # raise DependencyNotInstalledError(
    #  "Android SDK not found. "
    #  "Please install Android SDK "
    #  "and set ANDROID_HOME or ANDROID_SDK_ROOT "
    #  "environment variable.")
    logger.warning(
      "Android SDK not found. Please install Android SDK and set ANDROID_HOME or ANDROID_SDK_ROOT "
      "environment variable.")


if __name__ == '__main__':
  start_bridge_server()
