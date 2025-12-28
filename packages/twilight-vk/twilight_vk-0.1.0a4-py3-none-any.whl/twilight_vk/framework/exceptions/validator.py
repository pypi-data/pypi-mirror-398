from aiohttp import ClientResponse
from .framework import FrameworkError

class ValidationError(FrameworkError):
    
    def __init__(self,
                 response: dict | ClientResponse ,
                 message: str | None = None):
        '''
        Базовый класс ошибки валидации

        :param response: Ответ HTTP запроса или тело ответа
        :type response: dict | ClientResponse
        '''
        self.response = response
        self.message = message
    
    def __str__(self):
        return f"Validation error"\
        f"{f" : {self.message}" if self.message is not None else ""}"

class HttpValidationError(ValidationError):
    
    def __init__(self,
                 isValid: bool,
                 isSuccess: bool,
                 response: ClientResponse):
        '''
        Ошибка валидации ответов от любых HTTP запросов
        Возникает при некорректном raw-формате ответа либо при кодах ответа которые не соответствуют успешным кодам

        :param isValid: Результат проверки RAW
        :type isValid: bool

        :param isSuccess: Результат проверки успешного кода в ответе
        :type isSuccess: bool

        :param response: Ответ от HTTP запроса
        :type response: ClientResponse
        '''
        self.isRaw = isValid
        self.isSuccess = isSuccess
        self.response = response
    
    def __str__(self):
        return f"Response validation error"\
        f"{": Is not valid raw " if self.isRaw is None else ""}"\
        f"{": Status code is not success " if self.isSuccess is None else ""}"

class EventValidationError(ValidationError):

    def __init__(self,
                 jsonIsValid: bool,
                 fieldsAreValid: bool,
                 content: dict):
        '''
        Ошибка валидации ответов от API
        Возникает при ошибках в ответе или при некорректном формате

        :param jsonIsValid: Результат проверки наличия JSON в теле ответа
        :type jsonIsValid: bool

        :param fieldsAreValid: Результат проверки обязательных полей в теле ответа
        :type fieldsAreValid: bool

        :param content: Тело ответа в формате JSON
        :type response: dict
        '''
        self.jsonIsValid = jsonIsValid
        self.fieldsAreValid = fieldsAreValid
        self.content = content

    def __str__(self):
        return f"Response validation error"\
        f"{": Content is not JSON " if self.jsonIsValid is None else ""}"\
        f"{": Response doesn't contain the required fields " if self.fieldsAreValid is None else ""}"