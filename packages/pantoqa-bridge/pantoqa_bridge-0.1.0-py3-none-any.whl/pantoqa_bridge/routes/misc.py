import aiohttp
from fastapi import APIRouter

from pantoqa_bridge.config import APPIUM_SERVER_URL, EXT_VERSION

route = APIRouter()


@route.get("/health", tags=["misc"])
async def health() -> dict[str, str]:
  return {
    "status": "ok",
    "version": EXT_VERSION,
  }


@route.get("/appium-status", tags=["misc"])
async def get_appium_status():
  async with aiohttp.ClientSession() as session:
    res = await session.get(f"{APPIUM_SERVER_URL}/status")
    res.raise_for_status()
    data = await res.json()
  return data
