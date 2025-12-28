import re

class TwiML:

    def __init__(self, template: str=None):
        '''
        Twilight Markup Language for extracting args and mentions from message text

        :param template: Regex template for parsing
        :type template: str
        '''
        self.template = template
        self.placeholder_types = {
            "any": (r".+", str),
            "int": (r"\d+", int),
            "word": (r"\S+", str)
        }

    def update_template(self, template: str):
        '''
        Updates the template for parsing
        '''
        self.template = template

    async def parse(self,
                    message: str) -> dict:
        '''
        Parsing message for variable values.
        
        :param message: Message text
        :type message: str
        '''
        args = {}
        pattern = re.escape(self.template)
        placeholders = re.findall(r"<(\w+)(?::(\w+))?>", self.template)

        for name, type in placeholders:
            _type = type or "any"
            _regex, _convert_to = self.placeholder_types.get(_type)
            pattern = pattern.replace(
                re.escape(f"<{name}{":" + _type if type else ""}>"), f"({_regex})"
            )
            args[name] = _convert_to
        
        match = re.match(pattern, message)
        if not match:
            return None
        
        result = {}
        for (name, _), value in zip(placeholders, match.groups()):
            result[name] = args[name](value)
        return result
    
    async def extract_mentions(self,
                               message: str) -> dict:
        '''
        Extracts the mentions from message

        :param message: Message text
        :type message: str
        '''
        pattern = r"\[([a-zA-Z]+)(\d+)\|([^\]]*)\]"
        mentions = re.findall(pattern, message)

        result = {
            "mentions": [{
                "type": mention[0],
                "id": int(mention[1]),
                "screen_name": f"{mention[0]}{mention[1]}",
                "text": mention[2]
            } for mention in mentions]
        }

        return result