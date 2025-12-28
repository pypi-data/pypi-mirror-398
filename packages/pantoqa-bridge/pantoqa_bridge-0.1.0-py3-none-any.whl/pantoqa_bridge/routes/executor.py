import asyncio
import json
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pantoqa_bridge.logger import logger
from pantoqa_bridge.models.code_execute import CodeFile
from pantoqa_bridge.tasks.executor import AppiumExecutable, MaestroQAExecutable

route = APIRouter()


class ExecutionRequest(BaseModel):
  files: list[CodeFile]
  framework: Literal['APPIUM', 'MAESTRO']


class ExecutionResult(BaseModel):
  status: str
  exit_code: int | None = None
  message: str | None = None


@route.post("/execute")
async def execute(rawrequest: Request) -> StreamingResponse:
  request_json = await rawrequest.json()
  request = ExecutionRequest.model_validate(request_json)
  if not request.files:
    raise HTTPException(status_code=400, detail="At least one file is required")

  stream = _stream_execution(request)
  return StreamingResponse(stream, media_type="text/event-stream")


def _format_sse(event: str, data: str) -> str:
  json_dict = {
    "event": event,
    "data": data,
  }
  json_str = json.dumps(json_dict)
  return f"data: {json_str}\n\n"


async def _stream_execution(request: ExecutionRequest) -> AsyncIterator[str]:
  copiedfiles: list[str] = []
  with tempfile.TemporaryDirectory(prefix="pantoqa-qa-run-") as tmpdir:
    workdir = Path(tmpdir)
    for code_file in request.files:
      target = workdir / code_file.path
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_text(code_file.content)
      copiedfiles.append(str(target))

    yield _format_sse("status", "starting process")
    await asyncio.sleep(1)  # Simulate some delay

    executable = AppiumExecutable(
      files=copiedfiles) if request.framework == 'APPIUM' else MaestroQAExecutable(copiedfiles)
    try:
      output = await executable.execute()
      yield _format_sse("status", f"Execution output: {output}")
    except Exception as e:
      yield _format_sse("error", f"Execution failed: {str(e)}")
      logger.exception(f"Execution failed: {str(e)}")

    return

    # process = await asyncio.create_subprocess_exec(
    #   sys.executable,
    #   str("entry.py"),
    #   stdout=PIPE,
    #   stderr=PIPE,
    #   cwd=workdir,
    # )

    # queue: asyncio.Queue[tuple[str, str | None]] = asyncio.Queue()

    # async def pump(stream: asyncio.StreamReader, label: str) -> None:
    #   while True:
    #     line = await stream.readline()
    #     if not line:
    #       break
    #     await queue.put((label, line.decode(errors="replace").rstrip("\n")))
    #   await queue.put((label, None))

    # stdout_task = asyncio.create_task(pump(process.stdout, "stdout"))
    # stderr_task = asyncio.create_task(pump(process.stderr, "stderr"))

    # completed_streams = 0
    # try:
    #   while completed_streams < 2:
    #     label, line = await queue.get()
    #     if line is None:
    #       completed_streams += 1
    #       continue
    #     yield _format_sse(label, line)
    # except asyncio.CancelledError:
    #   process.kill()
    #   raise
    # finally:
    #   await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

    # return_code = await process.wait()
    # status = "completed" if return_code == 0 else "failed"
    # yield _format_sse("status", f"{status} with exit code {return_code}")
