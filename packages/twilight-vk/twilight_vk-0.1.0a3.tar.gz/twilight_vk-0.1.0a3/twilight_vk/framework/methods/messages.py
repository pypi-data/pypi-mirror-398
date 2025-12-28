from random import randint

from .base import BaseMethodsGroup

class Messages(BaseMethodsGroup):

    async def getConversationMembers(self,
                                     peer_id: int,
                                     offset: int | None = None,
                                     count: int | None = None,
                                     extended: bool = False,
                                     fields: str | None = None,
                                     group_id: int | None = None):
        '''
        Метод получает список участников беседы.
        (см. https://dev.vk.ru/ru/method/messages.getConversationMembers)
        '''
        values = {
            "peer_id": peer_id,
            "offset": abs(offset) if offset is not None else None,
            "count": abs(count) if count is not None else None,
            "extended": "true" if extended else "false",
            "fields": fields,
            "group_id": abs(group_id) if group_id is not None else self.__group_id__,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.getConversationMembers",
                                                       values=values)
        return response

    async def getConversationById(self,
                                  peer_ids: int | list[int],
                                  extended: bool = False,
                                  fields: str | None = None,
                                  group_id: int | None = None):
        '''
        Позволяет получить беседу по её идентификатору.
        (см. https://dev.vk.ru/ru/method/messages.getConversationsById)
        '''
        values = {
            "peer_ids": ",".join([f"{pid}" for pid in peer_ids]) if isinstance(peer_ids, list) else f"{peer_ids}",
            "extended": "true" if extended else "false",
            "fields": fields,
            "group_id": abs(group_id) if group_id is not None else self.__group_id__,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.getConversationsById",
                                                       values=values)
        return response
    
    async def removeChatUser(self,
                             chat_id: int,
                             user_id: int | None = None,
                             member_id: int | None = None):
        '''
        Исключает из мультидиалога пользователя, если текущий пользователь или сообщество
        является администратором беседы либо текущий пользователь пригласил исключаемого пользователя.
        (см. https://dev.vk.ru/ru/method/messages.removeChatUser)
        '''
        values = {
            "chat_id": abs(chat_id),
            "user_id": user_id,
            "member_id": member_id,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.removeChatUser",
                                                       values=values)
        return response
    
    async def send(self,
                   user_id: int = None,
                   peer_id: int = None,
                   peer_ids: int | list[int] = None,
                   domain: str = None,
                   chat_id: int = None,
                   user_ids: int | list[int] = None,
                   message: str = None,
                   lat: str = None,
                   long: str = None,
                   attachment: str | list[str] = None,
                   reply_to: int = None,
                   forward_messages: int | list[int] = None,
                   forward: dict = None,
                   sticker_id: int = None,
                   group_id: int | None = None,
                   keyboard: object = None,
                   template: object = None,
                   payload: object = None,
                   content_source: dict = None,
                   dont_parse_links: bool = None,
                   disable_mentions: bool = None,
                   intent: str = None,
                   subsribe_id: int = None):
        
        '''
        Отправляет сообщение
        (см. https://dev.vk.ru/ru/method/messages.send)
        '''

        values = {
            "user_id": user_id,
            "random_id": randint(0, 1000000000),
            "peer_id": peer_id,
            "peer_ids": ",".join([f"{pid}" for pid in peer_ids]) if isinstance(peer_ids, list) else f"{peer_ids}",
            "domain": domain,
            "chat_id": chat_id,
            "user_ids": ",".join([f"{uid}" for uid in user_ids]) if isinstance(user_ids, list) else f"{user_ids}",
            "message": message,
            "lat": lat,
            "long": long,
            "attachment": ",".join([f"{attach}" for attach in attachment]) if attachment is not None else None,
            "reply_to": reply_to,
            "forward_messages": forward_messages,
            "forward": forward,
            "sticker_id": abs(sticker_id) if sticker_id is not None else None,
            "group_id": abs(group_id) if group_id is not None else self.__group_id__,
            "keyboard": keyboard,
            "template": template,
            "payload": payload,
            "content_source": content_source,
            "dont_parse_links": "true" if dont_parse_links else "false",
            "disable_mentions": "true" if disable_mentions else "false",
            "intent": intent,
            "subscribe_id": abs(subsribe_id) if subsribe_id is not None else None,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.send",
                                                       values=values)
        return response