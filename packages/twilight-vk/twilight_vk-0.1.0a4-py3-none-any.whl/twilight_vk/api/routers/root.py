from typing import Callable, TYPE_CHECKING
import asyncio

from fastapi import APIRouter

from .base import BaseRouter
from ...utils.types.twi_states import (
    TwiAPIStates,
    TwiVKStates
)

if TYPE_CHECKING:
    from ... import TwilightVK
    from ... import TwilightAPI

class RootRouter(BaseRouter):

    def __init__(self,
                 bots: list['TwilightVK'] = [],
                 api: 'TwilightAPI' = None):
        '''
        Root API router for TwilightAPI

        :param bots: List of bots will be connected to the API
        :type bots: list[TwilightVK]

        :param api: TwilightAPI object
        :type api: TwilightAPI
        '''
        self.router = APIRouter(
            tags=["Root"],
            prefix="/root"
        )

        self._bots = bots
        self._api = api
        
        self.router.add_api_route("/ping", self.ping, methods=["GET"], 
                                  name="Pings the API",
                                  description="Method for API status check. All connected APIs should return \"pong\" if alive.")
        self.router.add_api_route("/stop", self.stop, methods=["GET"],
                                  name="Stops the API",
                                  description="Stops all framework routers of API and main API itself")
    
    async def ping(self) -> dict:
        '''
        API METHOD
        Pings all API routers of bots connected to the TwilightAPI
        '''
        responses = {"server": "Pong OwO"}

        for bot in self._bots:
            responses[f"{bot.bot_name}"] = await bot.api_router.ping()

        return {"response": responses}
    
    async def stop(self, stop_api: bool = False, force: bool = False) -> dict:
        '''
        API METHOD
        Stops all bots connected to the TwilightAPI and their API

        :param stop_api: Should this method also stop the TwilightAPI itself
        :type stop_api: bool

        :param force: Forced stop for TwilightVK bots
        :type force: bool
        '''
        responses = {}

        for bot in self._bots:
            responses[f"{bot.bot_name}"] = await bot.api_router.stop(force)

        while not all([bot._state == TwiVKStates.DISABLED for bot in self._bots]):
            await asyncio.sleep(1.0)

        if self._api and stop_api:
            await self._api.stop()
            responses[f"server"] = "Shutdown initiated"

        return {"response": responses}