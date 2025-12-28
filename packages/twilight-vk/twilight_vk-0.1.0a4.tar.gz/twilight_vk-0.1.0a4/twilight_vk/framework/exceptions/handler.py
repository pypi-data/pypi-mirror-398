from typing import TYPE_CHECKING, AnyStr

from .framework import FrameworkError

if TYPE_CHECKING:
    from ...utils.types.response import ResponseHandler

class HandlerError(FrameworkError):

    def __init__(self,
                 message:str):
        '''
        Базовое исключение обработчика

        :param message: Опционально. Дополнительная информация об ошибке
        :type message: str
        '''
        self.message = message
    
    def __str__(self):
        return f"Handler error"\
        f"{f" : {self.message}" if self.message is not None else ""}"
    

class ResponseHandlerError(HandlerError):

    def __init__(self,
                 callback: "ResponseHandler" | AnyStr,
                 _isinstance: bool = None):
        '''
        Исключение обработчика ответов от функций

        :param callback: Ответ от функции, которая выполнилась в обработчике событий
        :type callback: ResponseHandler | Any
        
        :param instance_needed: Класс который должен был передаться в функции (всегда должен быть ResponseHandler)
        :type instance_needed: ResponseHandler
        '''
        self.callback = callback
        self._isinstance = _isinstance
    
    def __str__(self):
        return f"Response handler error"\
        f"{f" : function callback is not instance of ResponseHandler, make sure you are returning correct values in your functions"\
           if self._isinstance is not None and not self._isinstance else self.callback}"