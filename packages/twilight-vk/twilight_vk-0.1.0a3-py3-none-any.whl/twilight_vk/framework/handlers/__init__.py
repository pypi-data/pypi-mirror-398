from typing import TYPE_CHECKING
import logging
import asyncio

from .event_handlers import (
    BASE_EVENT_HANDLER,
    DEFAULT_HANDLER,
    MESSAGE_NEW,
    MESSAGE_REPLY
)
from ...utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from ..methods import VkMethods
    from ...utils.event_loop import TwiTaskManager

class OnEventLabeler:

    def __init__(self, handlers: dict):
        self.handlers = handlers

    def all(self, *rules):
        def decorator(func):
            for handler_name in self.handlers.keys():
                self.handlers[handler_name].__add__(func, rules)
            return func
        return decorator
    
    def message_new(self, *rules):
        def decorator(func):
            self.handlers[BotEventType.MESSAGE_NEW].__add__(func, rules)
            return func
        return decorator

class EventRouter:

    def __init__(self,
                 vk_methods:'VkMethods',
                 _loop_wrapper: 'TwiTaskManager'):
        '''
        Router for events.
        Allows to route events to separate event handlers
        '''
        self.vk_methods = vk_methods
        self._loop_wrapper = _loop_wrapper
        self.logger = logging.getLogger("event-router")
        self._handlers = {
            "default": DEFAULT_HANDLER(self.vk_methods),
            BotEventType.MESSAGE_NEW: MESSAGE_NEW(self.vk_methods),
            BotEventType.MESSAGE_REPLY: MESSAGE_REPLY(self.vk_methods)
        }
        self.on_event = OnEventLabeler(self._handlers)
    
    async def handle(self, polling_response: dict):
        '''
        Handles the event list

        :param polling_response: Response from the polling requests contains "ts" and "updates" keys
        :type polling_response: dict
        '''
        self.logger.debug("Routing the events...")
        events = []
        for event in polling_response["updates"]:
            events.append(
                self._loop_wrapper._loop.create_task(
                    self.route(event)
                )
            )
        try:
            await asyncio.gather(*events, return_exceptions=False)
        except Exception as exc:
            self.logger.error(f"{exc.__class__.__name__}: {exc}", exc_info=True)

    async def route(self, current_event: dict):
        '''
        Routing the event to the exact handler
        '''
        event_type = current_event.get("type", "default")
        handler:BASE_EVENT_HANDLER = self._handlers.get(event_type, self._handlers["default"])
        self.logger.debug(f"Routing the event {current_event.get("type")} to the {handler.__class__.__name__} handler")
        await handler.__executeAsync__(current_event)