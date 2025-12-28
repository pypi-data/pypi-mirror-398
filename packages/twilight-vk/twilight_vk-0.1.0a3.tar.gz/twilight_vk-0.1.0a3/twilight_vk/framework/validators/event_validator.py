import logging

from aiohttp import ClientResponse

from ...utils.config import CONFIG
from ..exceptions.validator import (
    EventValidationError
)
from ..exceptions.vkapi import (
    VkApiError,
    AuthError,
    LongPollError
)

class EventValidator:

    def __init__(self):
        self.__requiredFields__ = ['response', 'error']
        self.__pollingRequiredFileds__ = ['updates', 'failed']
        self.__errorFields__ = [
            self.__requiredFields__[-1],
            self.__pollingRequiredFileds__[-1]
            ]
        self.logger = logging.getLogger("event-validator")

    async def __isJsonValid__(self,
                              response:ClientResponse) -> bool:
        self.logger.debug(f"Checking Content-Type header for JSON...")
        if 'application/json' not in response.headers.get('Content-Type', '').lower():
            self.logger.error(f"Response doesn't have JSON content")
            return False
        return True
    
    async def __fieldsAreValid__(self,
                                 content:dict,
                                 fields:dict={}) -> bool:
        self.logger.debug(f"Checking for one of the required response fields...")
        for field in fields:
            if field in content:
                return True
        else:
            self.logger.error(f"Response doesn't contain any of the requirement fields")
            return False
    
    async def __haveErrors__(self,
                             content:dict) -> bool:
        self.logger.debug(f"Checking for errors in response...")
        for field in self.__errorFields__:
            if field in content:
                # TODO: VK API Exceptions and validators
                if field == "error":
                    error_code = content[field]["error_code"]
                    error_msg = content[field]["error_msg"]
                    request_params = content[field]["request_params"]
                    
                    if content[field]["error_code"] in [5, 1116]:
                        raise AuthError(error_code, error_msg, request_params)
                    
                    raise VkApiError(error_code, error_msg, request_params)
                if field == "failed":
                    failed_code = content[field]
                    raise LongPollError(failed_code, content["ts"] if "ts" in content else None)
                return True
        else:
            return False

    async def validate(self,
                 response:ClientResponse,
                 from_polling:bool=False) -> dict:
        self.logger.debug(f"Validating event response for [{response.method}] \"{response.url}\"...")

        jsonIsValid = await self.__isJsonValid__(response)

        if jsonIsValid:
            content = await response.json()
            fieldsAreValid = await self.__fieldsAreValid__(content, self.__requiredFields__ if not from_polling else self.__pollingRequiredFileds__)
            haveErrors = await self.__haveErrors__(content)

            if fieldsAreValid and not haveErrors:
                self.logger.debug("Event response is valid")
                return content
        
            self.logger.warning(f"Event response is not valid")
            self.logger.warning(f'{"jsonIsValid":<15}|{"":>1}{"fieldsAreValid":<15}|{"":>1}{"haveErrors":<15}|{"":>1}{"content":<15}')
            self.logger.warning(f'{jsonIsValid:<15}|{"":>1}{fieldsAreValid:<15}|{"":>1}{haveErrors:<15}|{"":>1}{content}')

        raise EventValidationError(jsonIsValid, fieldsAreValid, content)