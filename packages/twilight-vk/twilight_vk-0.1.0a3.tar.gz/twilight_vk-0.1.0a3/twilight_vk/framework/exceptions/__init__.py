from .framework import (
    FrameworkError,
    InitializationError
)

from .handler import (
    HandlerError,
    ResponseHandlerError
)

from .validator import (
    ValidationError,
    HttpValidationError,
    EventValidationError
)

from .vkapi import (
    LongPollError,
    VkApiError,
    AuthError
)