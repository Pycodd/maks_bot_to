from imports import (MessageCallback, MessageCreated, Audio, Video, Image,
                     File, Sticker, Location, Contact, AttachmentUpload, AttachmentPayload, UploadType)
from utils import EventContext, log_response_detailed
from maxapi.context import StatesGroup, State
from maxapi.context import MemoryContext
from datetime import datetime
from maxapi.types import Attachment
from maxapi.enums.attachment import AttachmentType


class WaitingStates(StatesGroup):
    """Группа состояний ожидания"""
    waiting_for_message = State()


class BotResponses:
    """
    Класс со всеми текстовыми ответами бота.
    """

    @staticmethod
    def greeting() -> str:
        """Приветственное сообщение. Функция start"""
        return (
            "Привет! 👋\n\n"
            "Доступные команды:\n"
            "/menu — открыть меню"
        )

    @staticmethod
    def settings() -> str:
        """Текст настроек. Класс CallbackHandlers, settings"""
        return (""
                "⚙️ Настройки:\n\n"
                "Пока тут ничего нет 😄"
        )

    @staticmethod
    def about() -> str:
        """Информация о боте. Класс CallbackHandlers, about"""
        return (
            "ℹ️ О боте:\n\n"
            "Это стабильный бот на MaxAPI 🚀\n"
            "Версия: 1.0.0"
        )

    @staticmethod
    def unknown() -> str:
        """Ответ на неизвестную команду. Класс CallbackHandlers, unknown"""
        return "❓ Неизвестная команда. Пожалуйста, используйте кнопки меню."

    @staticmethod
    def write_message() -> str:
        """Ответ на неизвестную команду. Класс CallbackHandlers, unknown"""
        return "Введи сообщение"

    @staticmethod
    async def format_received_message(
            event: MessageCreated,
            context: MemoryContext,
            user_name: str,
            user_id: int,
            bot
    ):
        """Отправляет обратно полученное сообщение с корректными вложениями"""

        message = event.message
        text = message.body.text or ""
        attachments = message.body.attachments or []

        # Собираем типы вложений для отображения
        content_types = []
        attachments_for_reply = []

        for att in attachments:
            att_type = att.type.lower() if att.type else ""

            # Маппинг типов из входящего сообщения в UploadType
            type_map = {
                "image": UploadType.IMAGE,
                "photo": UploadType.IMAGE,
                "video": UploadType.VIDEO,
                "audio": UploadType.AUDIO,
                "file": UploadType.FILE,
            }

            if att_type in type_map and hasattr(att, 'payload') and att.payload:
                # Получаем токен из входящего вложения
                token = getattr(att.payload, 'token', None)
                if token:
                    # Создаём AttachmentUpload для ответа
                    attachment = AttachmentUpload(
                        type=type_map[att_type],
                        payload=AttachmentPayload(token=token)
                    )
                    attachments_for_reply.append(attachment)
                    content_types.append(att_type)

            elif att_type == "location":
                content_types.append("геолокация")
                # Для геолокации нужна отдельная обработка (не через токен)
                if hasattr(att, 'payload') and att.payload:
                    lat = getattr(att.payload, 'latitude', None)
                    lon = getattr(att.payload, 'longitude', None)
                    if lat and lon:
                        # Отправляем геолокацию текстом или специальным вложением
                        content_types.append(f"📍 {lat}, {lon}")

            elif att_type == "contact":
                content_types.append("контакт")
                if hasattr(att, 'payload') and att.payload:
                    name = getattr(att.payload, 'name', '')
                    phone = getattr(att.payload, 'phone', '')
                    content_types.append(f"📞 {name}: {phone}")

            elif att_type in ["share", "link"]:
                content_types.append("ссылка")

        if not content_types and text:
            content_types = ["текст"]

        types_str = ", ".join(content_types)

        # Формируем текстовый ответ
        now = datetime.now()
        response = (
            f"✅ Получено сообщение!\n"
            f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👤 Отправитель: {user_name} (ID: {user_id})\n"
            f"📎 Тип: {types_str}\n\n"
        )

        if text:
            response += f"📝 Текст:\n{text}\n"

        # Отправляем ответ с вложениями
        if attachments_for_reply:
            await event.message.answer(
                text=response,
                attachments=attachments_for_reply
            )
        else:
            await event.message.answer(response)

        # Сбрасываем состояние
        await context.set_state(None)
        await context.set_data({})


class CallbackHandlers:
    """
    Класс для обработки всех callback-запросов от кнопок.
    """

    async def handle(self, callback: MessageCallback, context: MemoryContext = None):
        """
        Главный метод-диспетчер.
        Определяет, какой метод вызвать в зависимости от payload.
        """
        ctx = await EventContext.from_event(callback)
        data = callback.callback.payload
        ctx.log_info(f"нажал кнопку: {data}")

        if data == "settings":
            await self.settings(callback, ctx)
        elif data == "about":
            await self.about(callback, ctx)
        elif data == "write_message":
            await self.write_message(callback, ctx, context)
        else:
            await self.unknown(callback, ctx)

    @staticmethod
    async def settings(callback: MessageCallback, ctx: EventContext):
        """Обработчик кнопки 'Настройки'."""
        response = BotResponses.settings()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)

    @staticmethod
    async def about(callback: MessageCallback, ctx: EventContext):
        """Обработчик кнопки 'О боте'."""
        response = BotResponses.about()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)

    @staticmethod
    async def unknown(callback: MessageCallback, ctx: EventContext):
        """Обработчик неизвестных колбэков."""
        response = BotResponses.unknown()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)

    @staticmethod
    async def write_message(callback: MessageCallback, ctx: EventContext, context: MemoryContext = None):
        """Обработчик кнопки: Написать сообщение."""

        if context:
            await context.set_state(WaitingStates.waiting_for_message)
            await context.set_data({})
            ctx.log_info("Установлено состояние waiting_for_message")

        response = BotResponses.write_message()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)


