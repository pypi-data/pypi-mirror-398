class FrameworkError(Exception):
    
    def __init__(self,
                 message:str|None=None):
        '''
        Любые ошибки фреймворка

        :param message: Сообщение передаваемое вместе с исключением
        :type message: str | None
        '''
        self.message=message

    def __str__(self):
        return f"Framework got an error! {f"[{self.message}]" if self.message is not None else ""}"
    
class InitializationError(FrameworkError):
    
    def __init__(self,
                 access_token:str,
                 group_id:int):
        '''
        Ошибка инициализации класса TwilightVK

        :param access_token: Токен сообщества для авторизации
        :type access_token: str

        :param group_id: Идентификатор сообщества
        :type access_token: int
        '''
        self.__accessToken__ = access_token
        self.__groupId__ = group_id
    
    def __str__(self):
        return \
        f"{f" : ACCESS_TOKEN is None or empty" if not self.__accessToken__ else ""}"\
        f"{f" : GROUP_ID is None or empty" if not self.__groupId__ else ""}"