from typing import TYPE_CHECKING
import logging
import re
import inspect

from fastapi import APIRouter

if TYPE_CHECKING:
    from ...twilight_vk import TwilightVK

class VkApiRouter:

    def __init__(self, _bot: 'TwilightVK') -> None:
        '''
        Framework's VkApi methods API router

        :param bot: TwilightVK object
        :type bot: TwilightVK
        '''
        self.logger = logging.getLogger("twi-api-vkapi")
        self.logger.log(1, f"VkApi API Router was initialized")
        self.bot = _bot

        self.router = APIRouter(
            tags=[self.bot.bot_name],
            prefix=f"/vk-methods"
        )

        self._parseVkApi()
    
    def _parseVkApi(self) -> None:

        self.logger.debug(f"Getting list of method groups...")
        _methodGroups = self.bot.methods.__dict__
        _methodGroups.__delitem__("logger")
        self.logger.debug(f"List of method groups: {_methodGroups}")

        for key in _methodGroups.keys():
            
            _router = APIRouter(
                    tags=[self.bot.bot_name],
                    prefix=f"/{key}"
                )
            
            self.logger.debug(f"Getting list of the methods inside {key} class...")
            _methodList = inspect.getmembers(getattr(self.bot.methods, key), predicate=inspect.ismethod)
            _methodsList = {_method[0]: _method[1] for _method in _methodList}
            _methodsList.__delitem__("__init__")
            self.logger.debug(f"List of methods: {_methodsList}")

            for _method in _methodsList.keys():
                _router.add_api_route(
                    f"/{_method}", getattr(getattr(self.bot.methods, key), _method), methods=["POST"]
                )

            self.router.include_router(_router)
    
    def get_router(self) -> APIRouter:
        return self.router