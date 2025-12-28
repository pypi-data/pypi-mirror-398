import re
from typing import TYPE_CHECKING
import logging
import asyncio

from fastapi import APIRouter

from ....utils.config import CONFIG
from ....utils.types.twi_states import TwiVKStates
from .vk_api import VkApiRouter

if TYPE_CHECKING:
    from ...twilight_vk import TwilightVK

class FrameworkRouter:

    def __init__(self, bot: 'TwilightVK'):
        '''
        Framework API router

        :param bot: TwilightVK object
        :type bot: TwilightVK
        '''
        self.logger = logging.getLogger("twi-api-fw")
        self.logger.log(1, f"Framework API Router was initiated")
        self.bot = bot

        self.router = APIRouter(
            tags=[bot.bot_name],
            prefix=f"/{re.escape(bot.bot_name)}"
        )

        self.router.add_api_route("/ping", self.ping, methods=["GET"],
                                  name="Ping Framework API",
                                  description="Pings the frameworks's main API router")
        self.router.add_api_route("/stop", self.stop, methods=["GET"],
                                  name="Stop Current Bot",
                                  description="Stops current linked bot")
        
        self.logger.debug(f"Including VkMethods router...")
        self.methods_router = VkApiRouter(self.bot)
        self.router.include_router(self.methods_router.get_router())
        self.logger.debug(f"Done")
    
    async def ping(self) -> dict:
        '''
        API METHOD
        Pings the bot
        '''
        if self.bot._state == TwiVKStates.READY:
            return {"response": {"message": "Pong OwO"}}
        
        return {"error": {"bot_state": f"{self.bot._state}"}}
    
    async def stop(self, force: bool = False) -> dict:
        '''
        API METHOD
        Stops the bot

        :param force: Forced stop
        :type force: bool
        '''
        if self.bot._state in [TwiVKStates.READY, TwiVKStates.STARTING]:
            self.bot.stop(force)

            while not self.bot._state == TwiVKStates.DISABLED:
                await asyncio.sleep(1.0)

            return {"response": {"message": "Bot was stopped", "forced": force}}
        
        return {"error": {"message": "Unable to stop the bot", "bot_state": f"{self.bot._state}"}}

    
    def get_router(self) -> APIRouter:
        return self.router