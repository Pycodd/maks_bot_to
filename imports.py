""" Стандартные библиотеки Python """
import os, re, time, json, asyncio, logging
import datetime
from datetime import datetime
from dataclasses import dataclass
import sqlite3
from pathlib import Path

""" Сторонние библиотеки """
import pytz
import aiohttp
from flask import Flask, request, jsonify

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

""" Импорты MaxAPI types.attachments.upload """
from maxapi.types.attachments.upload import (
    AttachmentUpload,
    AttachmentPayload
)

""" Импорты MaxAPI types.input_media """
from maxapi.types.input_media import (
    InputMediaBuffer
)

""" Импорты MaxAPI enums.upload_type """
from maxapi.enums.upload_type import (
    UploadType
)

""" Импорты MaxAPI types.attachments """
from maxapi.types.attachments.audio import Audio
from maxapi.types.attachments.video import Video
from maxapi.types.attachments.image import Image
from maxapi.types.attachments.file import File
from maxapi.types.attachments.sticker import Sticker
from maxapi.types.attachments.location import Location
from maxapi.types.attachments.contact import Contact

""" Импорты MaxAPI context """
from maxapi.context import (
    MemoryContext,
    StatesGroup,
    State
)

""" Импорты MaxAPI enums """
from maxapi.enums.sender_action import SenderAction


""" Импорты модуля config """
from config import (
    bot,
    dp,
    main_router,
    WEBHOOK_SECRET,
    WEBHOOK_URL,
    PORT, WEBHOOK_PATH, BASE_URL, BOTHOST_DOMAIN
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
from responses import (
    BotResponses
)

""" Импорты модуля callback_handlers """
from callback_handlers import (
    CallbackHandlers
)

""" Импорты модуля states """
from states import (
    WaitingStates
)

""" Импорты модуля handlers """
from message_handlers import (
    MessageHandlers
)

""" Импорты модуля handlers database"""
from database import (
    populate_initial_data,
    init_db
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
    'Image', 'File', 'Sticker', 'Location', 'Contact', 'WEBHOOK_SECRET', 'WEBHOOK_URL',
    'PORT', 'request', 'jsonify', 'datetime', 'WEBHOOK_PATH', 'BASE_URL', 'BOTHOST_DOMAIN',
    'AttachmentUpload', 'AttachmentPayload', 'UploadType', 'pytz', 'Flask', 'populate_initial_data',
    'init_db', 'MemoryContext', 'MessageHandlers', 'SenderAction', 'aiohttp', 'InputMediaBuffer',
    'State', 'StatesGroup', 'dataclass', 'sqlite3', 'Path'
]
