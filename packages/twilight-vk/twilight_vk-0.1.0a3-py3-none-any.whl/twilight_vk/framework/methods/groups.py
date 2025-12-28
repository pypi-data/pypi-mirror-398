from .base import BaseMethodsGroup

class Groups(BaseMethodsGroup):
    
    async def getLongPollServer(self,
                                group_id:int=None) -> dict:
        
        '''
        Returns data for connection to Bots Longpoll API

        :param group_id: - Group's ID
        :type group_id: int | None
        '''

        values = {
            "group_id": abs(group_id) if group_id is not None else self.__group_id__,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.getLongPollServer",
                                                       values=values)
        return response
    