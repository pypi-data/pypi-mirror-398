from .framework import FrameworkError

class LongPollError(FrameworkError):

    def __init__(self,
                 failed_code:int,
                 new_ts:int=None):
        '''
        Исключение при ошибках в ответ на запросы к LongPoll серверу

        :param failed_code: Код ошибки который возвращает сервер
        :type failed_code: int

        :param new_ts: Новый ts возвращаемый при failed: 1
        :type new_ts: int
        '''
        self.failed_code = failed_code
        self.new_ts = new_ts
        self.failed_msgs = {
            1: "The event history is outdated or has been partially lost. Use actual \"ts\"",
            2: "The key expired. New \"key\" is needed.",
            3: "The information is lost. New \"key\" and \"ts\" is needed."
        }

    def __str__(self):
        return f"[{self.failed_code}] {self.failed_msgs.get(self.failed_code)}"



class VkApiError(FrameworkError):
    
    def __init__(self,
                 error_code:int,
                 error_msg:str,
                 request_params:list
                 ):
        '''
        Исключение при ошибках в запросах к VK API

        :param error_code: Код ошибки
        :type error_code: int

        :param error_msg: Сообщение ошибки
        :type error_msg: str

        :param request_params: Переданные с запросом HTTP параметры
        :type request_params: list
        '''
        self.error_code = error_code
        self.error_msg = error_msg
        self.request_params = request_params
    
    def __str__(self):
        return f"[{self.error_code}] {self.error_msg}"

class AuthError(VkApiError):
    '''Ошибка авторизации в API'''
    pass