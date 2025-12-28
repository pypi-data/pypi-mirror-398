from typing import TYPE_CHECKING
from typing import Any
import logging

from ...utils.config import CONFIG

if TYPE_CHECKING:
    from ..methods import VkMethods

class BaseRule:

    def __init__(self, **kwargs):
        '''
        Base rule with base logic
        All child rules should inherit this one with changing check() function's logic

        :param kwargs: Dict of addictional arguments to this function
        :type kwargs: dict
        '''
        self.event: dict = None
        self.methods: "VkMethods" = None
        self.kwargs: dict = kwargs
        self.logger = logging.getLogger("rule-handler")
        self.__parseKwargs__()
        self.logger.log(1, f"Rule {self.__class__.__name__}({", ".join(self.__printKwargs__())}) is initiated")
    
    def __parseKwargs__(self):
        '''
        Parsing kwargs attribute, allowing to use each item as separate rule's attribute
        '''
        for key, value in self.kwargs.items():
            setattr(self, key, value)
    
    def __printKwargs__(self):
        output = []
        for key, value in self.kwargs.items():
            if key in ["rules", "rule"]:
                output.append(f"{key}: {", ".join(obj.__class__.__name__ for obj in value)}")
                continue
            output.append(f"{key}: {value}")
        return output

    def __getattr__(self, name):
        '''
        Allows to handle errors with parsing
        '''
        if name not in ['event', 'kwargs', 'methods', 'logger']:
            return getattr(self, self.kwargs[name])
    
    async def __linkVkMethods__(self, methods):
        '''
        Updates the methods attribute so you could make api requests from inside the rule
        '''
        try:
            self.logger.debug(f"Linking VkMethods class to the {self.__class__.__name__}...")
            self.methods = methods
        except Exception as ex:
            self.logger.error(f"Got an error while linking", exc_info=True)
            return False
    
    async def __check__(self, event: dict) -> bool:
        '''
        The shell for Rule.check()
        Allows to logging
        '''
        try:
            self.logger.debug(f"Checking rule {self.__class__.__name__}({self.__printKwargs__()})...")
            response = await self.check(event)
            self.logger.debug(f"Rule {self.__class__.__name__} returned {response}")
            return response
        except Exception as ex:
            self.logger.error(f"Rule {self.__class__.__name__} returned an exception", exc_info=True)
            return False

    async def check(self, event: dict) -> bool:
        '''
        Main function with specific check logic for specific rule.
        It may be different in different rules
        It should always return the boolean as the result
        '''
        pass

    def __and__(self, other: "BaseRule"):
        return AndRule(self, other)
    
    def and_(self, other: "BaseRule"):
        return AndRule(self, other)
    
    def __or__(self, other: "BaseRule"):
        return OrRule(self, other)
    
    def or_(self, other: "BaseRule"):
        return OrRule(self, other)
    
    def __not__(self):
        return NotRule(self)
    
    def not_(self):
        return NotRule(self)


class AndRule(BaseRule):
    
    def __init__(self, *rules: BaseRule):
        '''
        Модификатор AND для комбинирования правил
        '''
        super().__init__(
            rules = rules
        )

    async def check(self, event: dict):
        results = {}

        for rule in self.rules:

            result = await rule.__check__(event)

            if isinstance(result, Exception):
                return result
            
            if result is False:
                return False
            
            if isinstance(result, dict):
                results.update(result)

        if results != {}:
            return results
        
        return True

class OrRule(BaseRule):
    
    def __init__(self, *rules: BaseRule):
        '''
        Модификатор OR для комбинирования правил
        '''
        super().__init__(
            rules = rules
        )
    
    async def check(self, event: dict):

        for rule in self.rules:

            result = await rule.__check__(event)

            if isinstance(result, Exception):
                return result
            
            if result is True:
                return True
            
        return False

class NotRule(BaseRule):
    
    def __init__(self, rule: BaseRule):
        '''
        Модификатор NOT для комбинирования правил
        '''
        super().__init__(
            rule = rule
        )
    
    async def check(self, event: dict):

        result = await self.rule.__check__(event)
        return not result if isinstance(result, bool) else False