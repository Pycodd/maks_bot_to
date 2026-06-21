from imports import (MessageCallback, MessageCreated, Audio, Video, Image,
                     File, Sticker, Location, Contact, AttachmentUpload,Keyboards,
                     AttachmentPayload, UploadType, asyncio, pytz)
from utils import EventContext, log_response_detailed
from maxapi.context import StatesGroup, State
from maxapi.context import MemoryContext
from datetime import datetime
from maxapi.types import Attachment
from maxapi.enums.attachment import AttachmentType
import aiohttp
import logging
from io import BytesIO
from maxapi.enums.sender_action import SenderAction


class WaitingStates(StatesGroup):
    """Группа состояний ожидания"""
    waiting_for_message = State()