import asyncio
import os
import signal
import socket
import subprocess
import time
from collections.abc import Awaitable, Callable

from pantoqa_bridge.config import APPIUM_SERVER_HOST, APPIUM_SERVER_PORT
from pantoqa_bridge.logger import logger


async def start_appium_process() -> int:
  cmd = ["appium", "--port", str(APPIUM_SERVER_PORT), "--address", APPIUM_SERVER_HOST]
  logger.info(f"Starting Appium at http://{APPIUM_SERVER_HOST}:{APPIUM_SERVER_PORT}")
  result = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
  )
  logger.info(f"Running appium at pid {result.pid}...")
  return result.pid


def start_appium_process_sync() -> int:
  cmd = ["appium", "--port", str(APPIUM_SERVER_PORT), "--address", APPIUM_SERVER_HOST]
  logger.info(f"Starting Appium at http://{APPIUM_SERVER_HOST}:{APPIUM_SERVER_PORT}")
  process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    start_new_session=True,
  )
  logger.info(f"Running Appium at pid {process.pid}...")
  return process.pid


async def wait_for_port_to_alive(port: int, host: str = "0.0.0.0", timeout=15):
  start = time.time()
  while time.time() - start < timeout:
    try:
      with socket.create_connection((host, port), timeout=1):
        return True
    except OSError:
      await asyncio.sleep(0.5)
  raise TimeoutError("Appium did not start in time")


def watch_process_bg(
  pid: int,
  on_exit: Callable[[int], Awaitable[None] | None],
  *,
  poll_interval: float = 2.0,
) -> None:

  async def _watcher():
    try:
      while True:
        if not is_process_alive_sync(pid):
          result = on_exit(pid)
          if asyncio.iscoroutine(result):
            await result
          return

        await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
      return

  asyncio.create_task(_watcher())


def is_process_alive_sync(pid: int) -> bool:
  try:
    out = subprocess.check_output(["ps", "-o", "state=", "-p", str(pid)]).decode().strip()
    return "z" not in out.lower()
  except subprocess.CalledProcessError:
    return False


def kill_process_sync(pid: int, timeout: int = 10) -> None:
  if pid <= 0:
    return

  if not is_process_alive_sync(pid):
    return

  # Step 1: graceful terminate
  try:
    logger.info(f"Terminating process {pid}...")
    os.kill(pid, signal.SIGTERM)
  except ProcessLookupError:
    return

  if not is_process_alive_sync(pid):
    return

  # Step 2: wait
  logger.info(f"Waiting for process {pid} to terminate...")
  start = time.time()
  while time.time() - start < timeout:
    if not is_process_alive_sync(pid):
      logger.info(f"Process {pid} terminated.")
      return
    time.sleep(0.2)

  # Step 3: force kill
  try:
    logger.info(f"Killing process {pid}...")
    os.kill(pid, signal.SIGKILL)
  except ProcessLookupError:
    pass


def kill_self_process(signal=signal.SIGTERM):
  # DON'T WAIT HERE
  self_pid = os.getpid()
  logger.info(f"Killing self process {self_pid}...")
  os.kill(self_pid, signal)
