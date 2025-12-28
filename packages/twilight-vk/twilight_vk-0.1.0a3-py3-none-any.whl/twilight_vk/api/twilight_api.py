import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager

from ..components.logo import LogoComponent
from ..logger.darky_logger import DarkyLogger
from ..logger.darky_visual import STYLE, FG, BG, Visual
from ..utils.config import CONFIG
from ..utils.event_loop import TwiTaskManager
from ..utils.types.twi_states import TwiAPIStates
from .routers import RootRouter

BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"

Visual.ansi()

class TwilightAPI:

    def __init__(self,
                 BOTS: object | list[object] = [],
                 HOST: str = CONFIG.API.host,
                 PORT: str = CONFIG.API.port,
                 loop_wrapper: TwiTaskManager = None,
                 _need_root_router: bool = True
                ):
        '''
        API Swagger for bots based on Twilight framework

        :param BOTS: One or list of initialized Twilight bot objects
        :type BOTS: object | list[object]

        :param HOST: Sets the host ip adress for API Swagger
        :type HOST: str

        :param PORT: Sets the port for API Swagger
        :type PORT: str
        '''
        self._state = TwiAPIStates.INITIALIZING
        self.logo = LogoComponent()
        self.logger = DarkyLogger(logger_name=f"twilight-api", configuration=CONFIG.LOGGER)
        
        self.logger.info(f"Initializing API...")

        self.__HOST__ = HOST
        self.__PORT__ = PORT

        self.__api__ = FastAPI(
            title=CONFIG.API.title,
            description=CONFIG.API.description,
            version=CONFIG.API.version,
            lifespan=self.lifespan,
            root_path=CONFIG.API.prefix,
            docs_url=None
        )

        self.bots:list = BOTS

        self._loop_wrapper = TwiTaskManager() if loop_wrapper is None else loop_wrapper

        self._uvicorn_config = uvicorn.Config(
                app=self.__api__,
                host=self.__HOST__,
                port=self.__PORT__,
                log_config=CONFIG.LOGGER,
            )
        
        if _need_root_router:
            self.__api__.include_router(RootRouter(self.bots, self).get_router())

        self.router = APIRouter(
            tags=["Server"]
        )
        self.router.add_api_route(path="/favicon.ico", endpoint=self.favicon, methods=["GET"],
                                  include_in_schema=False)
        self.router.add_api_route(path="/docs", endpoint=self.custom_swagger, methods=["GET"],
                                  include_in_schema=False)
        self.__api__.include_router(self.router)

        self.logger.debug(f"Importing bot's API routers...")
        for bot in self.bots:
            self.logger.debug(f"Importing API routers from {bot.__class__.__name__}<{self.bots.index(bot)}> - {bot.bot_name}...")
            self.__api__.include_router(bot.__getApiRouters__())
        
        if not self.bots:
            self.logger.warning(f"There is no connected bots to the API")
        
        self._state = TwiAPIStates.DISABLED
        self.logger.info(f"API initialized")

    @asynccontextmanager
    async def lifespan(self, api: FastAPI):
        '''
        Provides start_up(preparing API wrapper) and
        shut_down(saving data for example) event handling
        '''
        try:
            '''Here is the startup code'''
            self._state = TwiAPIStates.STARTING
            self.logger.info(f"Twilight API is starting...")
            ...
            self._state = TwiAPIStates.READY
            self.logger.info(f"{FG.GREEN}Twilight API is started (on {CONFIG.API.host}:{CONFIG.API.port}){STYLE.RESET}")

            yield

            '''Here is the shutdown code'''
            self._state = TwiAPIStates.SHUTTING_DOWN
            ...
            self._state = TwiAPIStates.DISABLED
            self.logger.info(f"{FG.RED}Twilight API is stopped{STYLE.RESET}")
        except Exception as ex:
            self.logger.critical(f"Unhandled error", exc_info=True)
            await self.stop()

    async def run_server(self):
        '''
        Runs the API server
        '''
        try:
            self.__uvicorn_server__ = uvicorn.Server(self._uvicorn_config)
            await self.__uvicorn_server__.serve()
        except KeyboardInterrupt:
            self.logger.debug("API was stopped by KeyboardInterrupt")

    def start(self):
        '''
        Starts the API Swagger
        '''
        try:
            self.logger.note(self.logo.colored)
            self.__uvicorn_server__ = uvicorn.Server(self._uvicorn_config)
            self._loop_wrapper.add_task(self.run_server())
            self._loop_wrapper.run()
        except KeyboardInterrupt:
            self.logger.debug("API was stopped by KeyboardInterrupt")
        except Exception:
            self.logger.critical("Unhandled error", exc_info=True)

    async def stop(self):
        '''
        Shutdown the API Swagger
        '''
        if self.__uvicorn_server__.started:
            self.logger.info(f"Gracefully shutting down the API...")
            self.__uvicorn_server__.should_exit = True

            try:
                await asyncio.wait_for(
                    asyncio.sleep(1.0),
                    timeout = 5.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Force stopping API after timeout")
            
            self.logger.debug("Shutting down complete")
    
    #---
    #API METHODS
    #---

    async def favicon(self) -> FileResponse:
        '''
        THIS IS API METHOD
        '''
        return FileResponse(ASSETS / "favicon.ico")
    
    async def custom_swagger(self):
        '''
        THIS IS API METHOD
        '''
        return get_swagger_ui_html(
            openapi_url=self.__api__.openapi_url,
            title = f"{self.__api__.title} - Swagger UI",
            swagger_favicon_url="/favicon.ico"
        )
    
    #TODO: importing routers from bots