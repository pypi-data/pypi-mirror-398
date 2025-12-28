import asyncio

from ...http.async_http import Http
from ...logger.darky_logger import DarkyLogger
from ..methods.base import VkBaseMethods

class BaseLongPoll:

    def __init__(self):
        self.httpClient: Http
        self.base_methods: VkBaseMethods
        self.logger: DarkyLogger

    async def auth(self):
        pass

    async def check_event(self):
        pass

    async def listen(self):
        '''
        Listening for events
        '''
        try:
            self.logger.debug(f"Polling was started")
            while not self.__stop__:
                event = await self.check_event()
                
                if "updates" not in event or event["updates"] == []:
                    continue

                yield event
        
        except asyncio.CancelledError:
            self.logger.warning(f"Listening was forcibly canceled (it is not recommend to do this)")
        finally:
            await self.httpClient.close()
            await self.base_methods.close()
            self.logger.debug(f"Polling was stopped")
            self.__stop__ = True
    
    def stop(self, _from="Polling"):
        if self.__stop__ == False:
            if _from == "Polling":
                self.logger.info(f"Polling will be stopped as soon as the current request will be done. Please wait")
            self.__stop__ = True