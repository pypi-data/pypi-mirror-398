from aiohttp import ClientSession, ClientResponse, ClientTimeout, TCPConnector

class Http:

    def __init__(self,
                 headers:dict|None=None,
                 timeout:int=30):
        '''
        This class allows to use HTTP requests asynchronously
        '''
        self.session = None
        self.headers = headers
        self.timeout = timeout
    
    async def __getSession__(self):
        if self.session is None:
            self.session = ClientSession(headers=self.headers,
                                         timeout=ClientTimeout(self.timeout),
                                         connector=TCPConnector(force_close=True))
        
    @staticmethod
    async def __isRaw__(response:ClientResponse, raw:bool=False):
        if raw:
            return response
        return await response.json()

    async def get(self,
                  url:str,
                  params:dict|None=None,
                  headers:dict|None=None,
                  raw:bool=True) -> ClientResponse | dict:
        '''
        HTTP GET method

        :param url: The url to get the response from
        :type url: str

        :param params: Dictionary containing the optional data to be sent in the GET request
        :type params: dict | None

        :param headers: Optional dictionary of HTTP headers to include in the request
        :type headers: dict, optional

        :param raw: Defines the raw/json response
        :type raw: bool
        '''
        await self.__getSession__()
        response = await self.session.get(url=url,
                                          params=params,
                                          headers=headers)
        return await self.__isRaw__(response, raw=raw)
    
    async def post(self,
                   url:str,
                   data:dict,
                   params:dict={},
                   headers:dict=None,
                   raw:bool=True) -> ClientResponse | dict:
        '''
        HTTP POST method

        :param url: The URL to send the POST request to
        :type url: str

        :param data: Dictionary containing the data to be sent in the POST request body
        :type data: dict

        :param headers: Optional dictionary of HTTP headers to include in the request
        :type headers: dict, optional

        :param raw: Defines the raw/json response
        :type raw: bool
        '''
        await self.__getSession__()
        response = await self.session.post(url=url,
                                           params=params,
                                           json=data,
                                           headers=headers)
        return await self.__isRaw__(response, raw=raw)
    
    async def close(self):
        if self.session is not None and not self.session.closed:
            await self.session.close()
            self.session = None