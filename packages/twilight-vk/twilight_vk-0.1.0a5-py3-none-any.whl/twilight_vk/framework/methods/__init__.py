import logging

from .groups import Groups
from .messages import Messages
from .users import Users
from ...utils.config import CONFIG

class VkMethods:

    def __init__(self,
                 baseMethods:object):
        self.logger = logging.getLogger("vk-methods")
        self.groups = Groups(baseMethods)
        self.messages = Messages(baseMethods)
        self.users = Users(baseMethods)