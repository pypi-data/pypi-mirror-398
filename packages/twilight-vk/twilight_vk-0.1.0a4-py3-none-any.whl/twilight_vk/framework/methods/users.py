from typing import overload

from .base import BaseMethodsGroup

class Users(BaseMethodsGroup):

    @overload
    async def get(self,
                  user_ids: str,
                  fields: str = None,
                  name_case: str = None,
                  from_group_id: int = None):
        ...

    async def get(self,
                  user_ids: str | list[str],
                  fields: str = None,
                  name_case: str = None,
                  from_group_id: int = None):
        '''
        Метод позволяет получить информацию о пользователях.
        (см. https://dev.vk.ru/ru/method/users.get)
        '''
        values = {
            "user_ids": ",".join([f"{uid}" for uid in user_ids]) if isinstance(user_ids, list) else f"{user_ids}",
            "fields": fields,
            "name_case": name_case,
            "from_group_id": from_group_id,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.get",
                                                       values=values)
        return response