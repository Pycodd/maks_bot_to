from imports import (MessageCallback, MessageCreated, Audio, Video, Image,
                     File, Sticker, Location, Contact)
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

        message = event.message
        text = message.body.text or ""
        attachments = message.body.attachments or []

        # Список для всех вложений бота
        attachments_for_bot = []
        content_types = []  # список типов для отображения

        for att in attachments:
            att_type = att.type.lower() if att.type else ""

            if att_type in ["image", "photo"]:
                content_types.append("фото")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.IMAGE,
                        payload={
                            "url": getattr(att.payload, 'url', None),
                            "token": getattr(att.payload, 'token', None)
                        },
                        bot=bot
                    ))

            elif att_type == "video":
                content_types.append("видео")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.VIDEO,
                        payload={
                            "url": att.payload.url,
                            "token": att.payload.token
                        },
                        bot=bot
                    ))

            elif att_type == "audio":
                content_types.append("аудио")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.AUDIO,
                        payload={
                            "url": getattr(att.payload, 'url', None),
                            "token": getattr(att.payload, 'token', None)
                        },
                        bot=bot
                    ))

            elif att_type == "file":
                content_types.append("файл")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.FILE,
                        payload={
                            "url": getattr(att.payload, 'url', None),
                            "token": getattr(att.payload, 'token', None)
                        },
                        bot=bot
                    ))

            elif att_type == "location":
                content_types.append("геолокация")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.LOCATION,
                        payload={
                            "latitude": att.payload.latitude,
                            "longitude": att.payload.longitude
                        },
                        bot=bot
                    ))

            elif att_type == "contact":
                content_types.append("контакт")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.CONTACT,
                        payload={
                            "name": att.payload.name,
                            "phone": att.payload.phone
                        },
                        bot=bot
                    ))

            elif att_type == "share":
                content_types.append("ссылка")
                # Для ссылки не создаем вложение

            elif att_type == "sticker":
                content_types.append("стикер")
                if hasattr(att, 'payload') and att.payload:
                    attachments_for_bot.append(Attachment(
                        type=AttachmentType.STICKER,
                        payload={
                            "url": att.payload.url,
                            "code": att.payload.code
                        },
                        bot=bot
                    ))

        # Если нет вложений, но есть текст
        if not content_types and text:
            content_types = ["текст"]

        # Формируем строку с типами вложений
        types_str = ", ".join(content_types) if content_types else "текст"
        print("=" * 50)
        print("🔍 DEBUG format_received_message:")
        print(f"   📝 content_types: {content_types}")
        print(f"   📝 types_str: '{types_str}'")
        print(f"   📝 text длина: {len(text) if text else 0}")
        print(f"   📝 text содержание: '{text[:200] if text else 'Нет текста'}'")
        print(f"   📎 Количество исходных вложений: {len(attachments)}")
        for i, att in enumerate(attachments):
            print(f"   📎 Исходное вложение {i + 1}: type={att.type}")
            if hasattr(att, 'payload') and att.payload:
                print(f"      payload: {att.payload}")
                if hasattr(att.payload, 'url'):
                    print(f"      url: {att.payload.url}")
                if hasattr(att.payload, 'token'):
                    print(f"      token: {att.payload.token[:30] if att.payload.token else None}...")
        print(f"   🤖 Вложений для бота: {len(attachments_for_bot)}")
        for i, att in enumerate(attachments_for_bot):
            print(f"   🤖 Бот вложение {i + 1}: type={att.type}")
            if att.payload:
                print(f"      payload: {att.payload}")
        print("=" * 50)

        # Формируем текстовый ответ
        now = datetime.now()
        response = (
            f"✅ Получено сообщение!\n"
            f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👤 Отправитель: {user_name} (ID: {user_id})\n"
            f"📎 Тип: {types_str}\n\n"
        )

        if text:
            response += f"📝 Текст:\n{text}\n\n"

        # Отправляем ответ с ВСЕМИ вложениями
        if attachments_for_bot:
            # Проверяем, есть ли стикеры среди вложений
            has_sticker = any(
                hasattr(att, 'type') and att.type == AttachmentType.STICKER
                for att in attachments_for_bot
            )

            if has_sticker:
                # Если есть стикер: отправляем сначала текст, потом отдельно стикеры и другие вложения

                # Отделяем стикеры от остальных вложений
                stickers = []
                other_attachments = []

                for att in attachments_for_bot:
                    if hasattr(att, 'type') and att.type == AttachmentType.STICKER:
                        stickers.append(att)
                    else:
                        other_attachments.append(att)

                # 1. Сначала отправляем текст
                await event.message.answer(response)

                # 2. Потом отправляем все стикеры (каждый отдельно или все вместе)
                for sticker in stickers:
                    await event.message.answer(
                        text="",
                        attachments=[sticker]
                    )

                # 3. Потом отправляем остальные вложения (фото, видео и т.д.)
                if other_attachments:
                    await event.message.answer(
                        text="",
                        attachments=other_attachments
                    )
            else:
                # Нет стикеров - отправляем всё вместе
                await event.message.answer(
                    text=response,
                    attachments=attachments_for_bot
                )
        else:
            # Нет вложений - отправляем только текст
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


