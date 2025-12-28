from .base import BaseRule
from ...utils.twiml import TwiML
from ...utils.types.event_types import MessageActionTypes

class TrueRule(BaseRule):

    '''
    Возвращает всегда True
    Правило сделано в основном для теста
    '''
    async def check(self, event: dict):
        return True

class FalseRule(BaseRule):

    '''
    Возвращает всегда False
    Правило сделано в основном для теста
    '''
    async def check(self, event: dict):
        return False

class ContainsRule(BaseRule):

    def __init__(self,
                 triggers: str | list[str],
                 ignore_case: bool = False,
                 need_list: bool = True):
        '''
        Проверяет наличие указанных в value фрагментов текста в сообщении, возвращает True при нахождении

        :param triggers: Слова-триггеры
        :type triggers: str | list[str]

        :param ignore_case: Флаг игнорирования регистра
        :type ignore_case: bool

        :param need_list: Дает понять нужно ли возвращать список найденных фрагментов или достаточно просто оповестить
        :type need_list: bool
        '''
        super().__init__(
            triggers = triggers,
            ignore_case = ignore_case,
            need_list = need_list
        )
    
    async def check(self, event: dict) -> bool | dict:
        text: str = event["object"]["message"]["text"]
        text = text.lower() if self.ignore_case else text
        result = {
            "triggers": []
        }

        for trigger in self.triggers:
            if trigger in text:
                if self.need_list:
                    result["triggers"].append(trigger)
                    continue
                return True
            
        if result["triggers"] != []:
            return result
        
        return False


class TextRule(BaseRule):

    def __init__(self,
                 value: str | list[str],
                 ignore_case: bool = False):
        '''
        Сверяет текст сообщения с указанным, возвращает True при совпадении

        :param value: Ожидаемое значение
        :type value: str | list[str]

        :param ignore_case: Флаг игнорирования регистра
        :type ignore_case: bool
        '''

        super().__init__(
            value = value,
            ignore_case = ignore_case
        )

    async def check(self, event: dict) -> bool:
        text:str = event["object"]["message"]["text"]
        return (text.lower() if self.ignore_case else text) in \
            ([val.lower() if self.ignore_case else self.value for val in self.value])


class TwiMLRule(BaseRule):

    def __init__(self,
                 value:str|list[str],
                 ignore_case:bool=False):
        '''
        Сверяет текст сообщения с указанным шаблоном на основе regex выражений, 
        возвращает словарь найденных аргументов или False если сообщение не соответствует шаблону

        :param value: Ожидаемое выражение(шаблон)
        :type value: str | list[str]

        :param ignore_case: Флаг игнорирования регистра
        :type ignore_case: bool
        '''

        super().__init__(
            value = value,
            ignore_case = ignore_case
        )

    async def check(self, event: dict) -> bool | dict:
        text:str = event["object"]["message"]["text"]
        text = text.lower() if self.ignore_case else text

        twiml = TwiML()

        for value in self.value:
            value = value.lower() if self.ignore_case else value

            twiml.update_template(value)
            result = await twiml.parse(text)

            if result is not None:
                return result
        else:
            return False


class MentionRule(BaseRule):

    def __init__(self,
                 need_list: bool = True):
        '''
        Проверяет наличие упоминаний в сообщении
        возвращает словарь найденных упоминаний/True или False если ни одного упоминания не было в сообщении
        
        :param need_list: Дает понять нужно ли возвращать список упоминаний или достаточно просто оповестить что упоминание было
        :type need_list: bool
        '''
        super().__init__(
            need_list = need_list
        )
    
    async def __get_mentions__(self, event: dict) -> dict:
        text: str = event["object"]["message"]["text"]

        twiml = TwiML()
        result = await twiml.extract_mentions(text)

        return result

    async def check(self, event: dict) -> bool | dict:
        result = await self.__get_mentions__(event)

        if result == {"mentions": []}:
            return False
        
        if self.need_list:
            return result
        
        return True

class IsMentionedRule(MentionRule):
    
    '''
    Проверяет был ли упомянут сам бот или нет
    '''
    async def check(self, event: dict) -> bool:
        mentions = await self.__get_mentions__(event)

        if mentions != False:
            for mention in mentions["mentions"]:
                if mention["type"] == "club" and mention["id"] == event.get("group_id", 0):
                    return True
        
        return False


class ReplyRule(BaseRule):

    '''
    Проверяет наличие ответа в событии.
    Возвращает True/False в зависимости от результата
    '''
    async def check(self, event: dict) -> bool:
        if event["object"]["message"].get("reply_message", None) is not None:
            return True
        return False

class ForwardRule(BaseRule):

    '''
    Проверяет наличие пересланного сообщения в событии.
    Возвращает True/False в зависимости от результата.
    '''
    async def check(self, event: dict) -> bool:
        if event["object"]["message"].get("fwd_messages") != []:
            return True
        return False


class AdminRule(BaseRule):

    '''
    Проверяет является ли пользователь отправивший сообщение в беседе его администратором
    Возвращает True/False в зависимости от результата
    '''

    async def __get_admins__(self, event: dict) -> None:
        if (
            event.setdefault("is_admin", None) is None or
            event.setdefault("is_bot_admin", None) is None
        ):
            chat_members = await self.methods.messages.getConversationMembers(
                peer_id=event["object"]["message"]["peer_id"]
            )
            member: dict
            for member in chat_members["response"]["items"]:
                if member.get("member_id") == event["object"]["message"]["from_id"]:
                    event["is_admin"] = member.get("is_admin", False)
                if member.get("member_id") == -event.get("group_id"):
                    event["is_bot_admin"] = member.get("is_admin", False)

    async def check(self, event: dict) -> bool:
        await self.__get_admins__(event)
        return event.get("is_admin")

class IsAdminRule(AdminRule):

    '''
    Проверяет является ли бот администратором в чате
    Возвращает True/False в зависимости от результата
    '''
    async def check(self, event: dict) -> bool:
        await self.__get_admins__(event)
        return event.get("is_bot_admin")


class InvitedRule(BaseRule):
    
    '''
    Возвращает True если какой-либо пользователь был добавлен в чат.
    '''
    async def __who_is_invited__(self, event: dict) -> int:
        if (
            event["object"]["message"].get("action", None) is not None and
            event["object"]["message"]["action"]["type"] == MessageActionTypes.CHAT_INVITE_USER
        ):
            return event["object"]["message"]["action"]["member_id"]
        return 0

    async def check(self, event: dict) -> bool:
        if await self.__who_is_invited__(event) != 0:
            return True
        return False 
    
class IsInvitedRule(InvitedRule):

    '''
    Возвращает True если бот был добавлен в чат
    '''
    async def check(self, event: dict) -> bool:
        if await self.__who_is_invited__(event) == -event.get("group_id"):
            return True
        return False