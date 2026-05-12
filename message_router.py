""" Простой модуль для ожидания ввода от пользователя """

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from maxapi import Bot
from maxapi.types import MessageCreated


class SimpleInputWaiter:
    """Простой ожидальщик сообщений"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._waiting: Dict[str, asyncio.Future] = {}

    def _get_key(self, chat_id: int, user_id: int) -> str:
        return f"{chat_id}_{user_id}"

    async def wait(self, chat_id: int, user_id: int, timeout: float = 60):
        """
        Ждет сообщение от пользователя.

        Возвращает:
            - dict с информацией о сообщении
            - None если таймаут
        """
        key = self._get_key(chat_id, user_id)

        # Создаем ожидание
        future = asyncio.Future()
        self._waiting[key] = future

        try:
            # Ждем с таймаутом
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            self._waiting.pop(key, None)

    async def on_message(self, event: MessageCreated) -> bool:
        """Обработчик входящего сообщения"""
        message = event.message
        chat_id = message.recipient.chat_id
        user_id = message.sender.user_id

        key = self._get_key(chat_id, user_id)

        if key in self._waiting and not self._waiting[key].done():
            # Парсим сообщение
            data = self._parse_message(event)
            self._waiting[key].set_result(data)
            return True

        return False

    def _parse_message(self, event: MessageCreated) -> dict:
        """Преобразует сообщение в словарь"""

        message = event.message
        attachments = message.body.attachments or []

        # Определяем тип контента
        content_type = "текст"
        attachment_token = None

        if attachments:
            att = attachments[0]
            att_type = att.type.lower() if att.type else ""

            if att_type == "image":
                content_type = "фото"
            elif att_type == "video":
                content_type = "видео"
            elif att_type == "audio":
                content_type = "аудио"
            elif att_type == "file":
                content_type = "файл"
            elif att_type == "location":
                content_type = "геолокация"
            elif att_type == "contact":
                content_type = "контакт"

            # Получаем токен (для фото/видео/аудио/файла)
            if hasattr(att, 'payload') and att.payload:
                attachment_token = getattr(att.payload, 'token', None)

        # Геолокация
        location = None
        if content_type == "геолокация" and attachments:
            att = attachments[0]
            if hasattr(att, 'payload'):
                location = {
                    "lat": getattr(att.payload, 'latitude', None),
                    "lon": getattr(att.payload, 'longitude', None)
                }

        # Контакт
        contact = None
        if content_type == "контакт" and attachments:
            att = attachments[0]
            if hasattr(att, 'payload'):
                contact = {
                    "name": getattr(att.payload, 'name', None),
                    "phone": getattr(att.payload, 'phone', None)
                }

        return {
            "type": content_type,
            "text": message.body.text or "",
            "token": attachment_token,
            "location": location,
            "contact": contact,
            "user_id": user_id,
            "user_name": message.sender.first_name,
            "chat_id": chat_id,
            "timestamp": datetime.now()
        }