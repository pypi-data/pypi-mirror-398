import asyncio

from ..api.twilight_api import TwilightAPI
from .api import FrameworkRouter
from .polling.bots_longpoll import BotsLongPoll
from ..logger.darky_logger import DarkyLogger
from ..logger.darky_visual import STYLE, FG
from ..components.logo import LogoComponent
from ..utils.config import CONFIG
from ..utils.types.twi_states import TwiVKStates
from ..utils.event_loop import TwiTaskManager
from .exceptions.framework import (
    InitializationError
)

class TwilightVK:

    def __init__(self,
                 BOT_NAME: str = None,
                 ACCESS_TOKEN: str = None, 
                 GROUP_ID: int = None, 
                 API_VERSION: str = CONFIG.VK_API.version,
                 API_MODE: str = "BOTSLONGPOLL",
                 TWI_API_ENABLED: bool = True,
                 HOST: str = CONFIG.API.host,
                 PORT: str = CONFIG.API.port,
                 loop_wrapper: TwiTaskManager = None) -> None:
        '''
        Initializes TwilightVK

        :param BOT_NAME: name of your bot
        :type BOT_NAME: str

        :param ACCESS_TOKEN: your group's access token, you can find it here(https://dev.vk.com/ru/api/access-token/community-token/in-community-settings)
        :type ACCESS_TOKEN: str

        :param GROUP_ID: your group's id, you can find it in your group's settings
        :type GROUP_ID: int

        :param API_VERSION: version of VK API, by default its grabbed from the frameworks's default configuration
        :type API_VERSION: str | None

        :param API_MODE: mode of polling (BOTSLONGPOLL/.../...)
        :type API_MODE: str

        :param TWI_API_ENABLED: should be bot's api awailable
        :type TWI_API_ENABLED: bool

        :param loop_wrapper: Initialized class TwiTaskManager for async loop wrapping
        :type loop_wrapper: TwiTaskManager
        '''
        self._state = TwiVKStates.INITIALIZING
        self.bot_name = self.__class__.__name__ if BOT_NAME is None else BOT_NAME
        self.logo = LogoComponent()
        self.logger = DarkyLogger(logger_name=f"twilight-vk", configuration=CONFIG.LOGGER)

        self.logger.info(f"Initializing framework...")

        try:
            if not ACCESS_TOKEN or not GROUP_ID:
                raise InitializationError(ACCESS_TOKEN, GROUP_ID)
        except InitializationError as ex:
            self.logger.critical(f"Initialization error{ex}")
            exit()

        self.__access_token__ = ACCESS_TOKEN
        self.__group_id__ = GROUP_ID
        self.__api_version__ = API_VERSION

        self._loop_wrapper = TwiTaskManager() if loop_wrapper is None else loop_wrapper

        API_MODES = {
            "BOTSLONGPOLL": BotsLongPoll(access_token=ACCESS_TOKEN,
                                         group_id=GROUP_ID,
                                         api_version=API_VERSION,
                                         loop_wrapper=self._loop_wrapper)
        }
        self.__bot__ = API_MODES.get(API_MODE, "BOTSLONGPOLL")
        self.methods = self.__bot__.vk_methods
        self.on_event = self.__bot__._router.on_event

        self.api_router = FrameworkRouter(self)

        self._api: TwilightAPI = None

        #if TWI_API_ENABLED:
        if False:
            self._api = TwilightAPI(
                BOTS = [self],
                HOST = HOST,
                PORT = PORT,
                loop_wrapper = self._loop_wrapper,
                _need_root_router = False
            )
            self._loop_wrapper.add_task(self._api.run_server())

        self._state = TwiVKStates.DISABLED
        self.logger.info(f"Framework initialized")

    async def run_polling(self):
        '''
        Start polling
        '''
        try:
            self._state = TwiVKStates.STARTING
            self.logger.info(f"Framework is starting...")

            await self.__bot__.auth()

            if self.__bot__.__server__ is not None:
                self._state = TwiVKStates.READY
                self.logger.info(f"{FG.GREEN}Framework is started (BOT_NAME: {self.bot_name}){STYLE.RESET}")
            else:
                self.logger.error(f"Server was not aquired. Exiting...")
                self.should_stop()

            async for event_response in self.__bot__.listen():
                if self._state == TwiVKStates.READY:
                    self._loop_wrapper.add_task(self.__bot__._router.handle(event_response))

        except KeyboardInterrupt:
            self.logger.debug(f"TwilightVK was stopped by KeyboardInterrupt")
        except asyncio.CancelledError:
            self.logger.warning(f"Polling was forcibly canceled (it is not recommend to do this)")
        except Exception as exc:
            self.logger.critical(f"Framework was crashed with critical unhandled error", exc_info=True)
            self._state = TwiVKStates.ERROR
        finally:
            #self.__loop__.stop()
            if self._state == TwiVKStates.READY and not self.__bot__.__stop__:
                self.__bot__.stop()
            self.logger.info(f"{FG.RED}Framework has been stopped{STYLE.RESET}")
            await asyncio.sleep(0.1)
            if self._state not in [TwiVKStates.ERROR]:
                self._state = TwiVKStates.DISABLED
            if self._api:
                await self._api.stop()


    def start(self):
        '''
        Starts the bot and polling until stop() is called
        '''
        try:
            self.logger.note(self.logo.colored)
            self._loop_wrapper.add_task(self.run_polling())
            self._loop_wrapper.run()
        except KeyboardInterrupt:
            self.logger.debug(f"TwilightVK was stopped by KeyboardInterrupt")
        except Exception:
            self.logger.critical("Unhandled error", exc_info=True)

    def stop(self, force: bool = False):
        '''
        Stops the polling and bot

        :param force: *[Optional]* Force stopping with cancelling all current event handlings
        :type force: bool
        '''
        if self._state == TwiVKStates.READY:

            self.logger.info(f"Shutting down...")
            self.should_stop()

            #if force:
            #    self.logger.warning(f"Forced stop. For soft stop - use TwilightVK.should_stop() method")
            #    self._loop_wrapper.cancel_tasks(targets = [self.run_polling()])
    
    def should_stop(self):
        '''
        Tells the bot that it should stop after the next event
        '''
        if self._state == TwiVKStates.READY and not self.__bot__.__stop__:
            self.logger.info("Framework was asked to stop")
            self._state = TwiVKStates.SHUTTING_DOWN
            self.__bot__.stop()
        elif self._state == TwiVKStates.SHUTTING_DOWN:
            self.logger.warning("Framework is already stopping")
        else:
            self.logger.error(f"Unable to stop framework for some reason. BOT_STATE={self._state}")

    def __getApiRouters__(self):
        return self.api_router.get_router()