import logging

from aiohttp.client_exceptions import ClientConnectorDNSError
from aiohttp import ClientResponse

from .base_longpoll import BaseLongPoll
from ..exceptions.vkapi import (
    AuthError,
    VkApiError,
    LongPollError
)
from ...utils.config import CONFIG
from ..methods.base import VkBaseMethods
from ..methods import VkMethods
from ..handlers import EventRouter
from ..validators.http_validator import HttpValidator
from ..validators.event_validator import EventValidator
from ...http.async_http import Http
from ...utils.event_loop import TwiTaskManager

class BotsLongPoll(BaseLongPoll):

    def __init__(self,
                 access_token:str=None,
                 group_id:int=None,
                 api_version:str=CONFIG.VK_API.version,
                 loop_wrapper: TwiTaskManager = None) -> None:
        '''
        BotLongPoll provides a communication between your app and VK API
        Bots Long Poll API allows you to process community events in real time

        :param access_token: your group's access token, you can find it here(https://dev.vk.com/ru/api/access-token/community-token/in-community-settings)
        :type access_token: str

        :param group_id: your group's id, you can find it in your group's settings
        :type group_id: int

        :param api_version: version of VK API, by default its grabbed from DarkyVK's configuration
        :type api_version: str | None
        '''
        self.__stop__ = False
        self.authorized = False
        self.httpValidator = HttpValidator()
        self.eventValidator = EventValidator()
        self.httpClient = Http()
        self.logger = logging.getLogger(self.__class__.__name__.lower())
        self.__access_token__ = access_token
        self.__group_id__ = group_id
        self.__api_url__ = CONFIG.VK_API.url
        self.__api_version__ = api_version
        self.__server__ = None
        self.__key__ = None
        self.__ts__ = None
        self.__wait__ = CONFIG.VK_API.wait
        self.base_methods = VkBaseMethods(self.__api_url__, self.__access_token__, self.__group_id__)
        self.vk_methods = VkMethods(self.base_methods)
        self._loop_wrapper = loop_wrapper if loop_wrapper is not None else TwiTaskManager()
        self._router = EventRouter(self.vk_methods, _loop_wrapper=self._loop_wrapper)
        self.on_event = self._router.on_event
    
    async def auth(self, update_ts: bool = True):

        '''
        Authorizing framework in VK API by getting LongPoll server

        :param update_ts: Update the ts value flag
        :type update_ts: bool
        '''

        try:
            self.logger.debug(f"Authorization...")

            self.logger.debug(f"Getting Bots LongPoll Server...")
            response = await self.vk_methods.groups.getLongPollServer()
            response = response["response"]
            self.logger.debug(f"Server aquired: {response}")

            self.__key__ = response["key"]
            self.__server__ = response["server"]
            if update_ts:
                self.__ts__ = response["ts"]
            self.authorized = True

            self.logger.debug(f"Authorized")

        except ClientConnectorDNSError as ex:
            self.logger.critical(f"{ex}", exc_info=True)
            self.stop(_from="Authorization")
        except AuthError as ex:
            self.logger.error(f"Authrization error: {ex}")
            self.stop(_from="Authorization")
        except VkApiError as ex:
            self.logger.critical("Request to VK API was handled with error", exc_info=True)
            self.stop(_from="Authorization")

    
    async def check_event(self) -> dict:
        
        '''
        Getting the event from BotsLongPoll server
        '''
        try:
            self.logger.debug(f"Listening the BotsLongPoll server for events...")
            response = await self.httpClient.get(url=f"{self.__server__}",
                                            params={
                                                "act": "a_check",
                                                "key": self.__key__,
                                                "ts": self.__ts__,
                                                "wait": self.__wait__
                                            },
                                            raw=True)
            self.logger.debug(f"Validating...")
            response = await self.httpValidator.validate(response)
            response = await self.eventValidator.validate(response, from_polling=True)
            self.logger.debug(f"Got an event: {response}")

            if "ts" not in response:
                self.auth()

            self.__ts__ = response["ts"]
            
            return response
        except LongPollError as ex:
            match ex.failed_code:
                case 1:
                    self.logger.warning(f"The event history is outdated or has been partially lost. "\
                                        f"The application can receive events further using the new \"ts\" value from the response.")
                    self.__ts__ = ex.new_ts
                case 2:
                    self.logger.warning(f"The key is expired. Getting new one...")
                    await self.auth(update_ts=False)
                case 3:
                    self.logger.error(f"The information is lost. Reauthorizing...")
                    await self.auth()
            self.logger.debug(f"Retrying to get event...")
            if not self.__stop__:
                return await self.check_event()
        except VkApiError as ex:
            self.logger.critical("Request to VK API was handled with error", exc_info=True)
            self.stop()