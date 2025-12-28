import json

class ResponseHandler:

    def __init__(self,
                 peer_ids: int | list[int] = None,
                 domain: str = None,
                 chat_id: int = None,
                 message: str = None,
                 lat: str = None,
                 long: str = None,
                 attachment: str | list[str] = None,
                 reply_to: int = None,
                 forward_messages: int | list[int] = None,
                 forward: dict = None,
                 sticker_id: int = None,
                 keyboard: object = None,
                 template: object = None,
                 payload: object = None,
                 content_source: dict = None,
                 dont_parse_links: bool = None,
                 disable_mentions: bool = None):
        '''
        Allows to send responses for the bot


        '''
        self.peer_ids = ",".join([f"{peer_id}" for peer_id in peer_ids]) if isinstance(peer_ids, list) else f"{peer_ids}"
        self.domain = domain
        self.chat_id = chat_id
        self.message = message

        self.lat = lat
        self.long = long

        self.attachment = attachment = ",".join([f"{attach}" for attach in attachment]) if attachment is not None else None

        self.reply_to = reply_to
        self.forward_messages = forward_messages
        self.forward = json.dumps(forward) if forward is not None else None

        self.sticker_id = sticker_id
        
        self.keyboard = keyboard
        self.template = template
        self.payload = payload
        self.content_source = json.dumps(content_source) if content_source is not None else None
        self.dont_parse_links = dont_parse_links
        self.disable_mentions = disable_mentions
    
    def getData(self) -> dict:
        '''
        Returns all data from initialized class
        '''
        return self.__dict__