""" Стандартные библиотеки Python """
import os, re, time, json, asyncio, logging
from flask import Flask, request, jsonify
import datetime

""" Сторонние библиотеки """
from dotenv import (
    load_dotenv
)

""" Типизация (Type Hints) """
from typing import (
    Callable,
    Awaitable,
    Dict,
    Any,
    Optional,
    List,
    Union
)

""" Импорты MaxAPI """
from maxapi import (
    Bot,
    Dispatcher,
    Router
)

""" Импорты MaxAPI utils.inline_keyboard """
from maxapi.utils.inline_keyboard import (
    InlineKeyboardBuilder
)

""" Импорты MaxAPI filters.middleware """
from maxapi.filters.middleware import (
    BaseMiddleware
)

""" Импорты MaxAPI types """
from maxapi.types import (
    MessageCreated,
    MessageCallback,
    CommandStart,
    Command,
    LinkButton,
    CallbackButton,
    MessageButton,
    RequestContactButton,
    RequestGeoLocationButton,
    BotStarted,
    UpdateUnion,

)

from maxapi.types.attachments.audio import Audio
from maxapi.types.attachments.video import Video
from maxapi.types.attachments.image import Image
from maxapi.types.attachments.file import File
from maxapi.types.attachments.sticker import Sticker
from maxapi.types.attachments.location import Location
from maxapi.types.attachments.contact import Contact

""" Импорты модуля config """
from config import (
    bot,
    dp,
    main_router
)

""" Импорты модуля logger_config """
from logger_config import (
    logging_conf,
    LoggingMiddleware
)

""" Импорты модуля utils """
from utils import (
    EventContext,
    log_response_detailed
)

""" Импорты модуля keyboards """
from keyboards import (
    Keyboards
)

""" Импорты модуля handlers """
from handlers import (
    CallbackHandlers,
    BotResponses,
    WaitingStates
)

__all__ = [
    'os', 're', 'time', 'json', 'asyncio', 'logging', 'load_dotenv',
    'Callable', 'Awaitable', 'Dict', 'Any', 'Optional', 'List', 'Union',
    'Bot', 'Dispatcher', 'Router', 'InlineKeyboardBuilder', 'BaseMiddleware',
    'MessageCreated', 'MessageCallback', 'CommandStart', 'Command', 'LinkButton',
    'CallbackButton', 'MessageButton', 'RequestContactButton', 'Keyboards', 'dp',
    'BotStarted', 'UpdateUnion', 'RequestGeoLocationButton',  'CallbackHandlers',
    'bot', 'main_router', 'logging_conf', 'LoggingMiddleware', 'EventContext',
    'log_response_detailed', 'BotResponses', 'WaitingStates', 'Audio', 'Video',
    'Image', 'File', 'Sticker', 'Location', 'Contact'
]
