# test_handlers.py
"""
Независимый модуль для тестирования вложений и сообщений.
Использует MessageHandlers для отправки сообщений.
"""
import pytz
import asyncio
from datetime import datetime
from io import BytesIO

from maxapi.context import StatesGroup, State
from maxapi.types.attachments.audio import Audio
from maxapi.types.attachments.video import Video
from maxapi.types.attachments.image import Image
from maxapi.types.attachments.file import File
from maxapi.types.attachments.sticker import Sticker
from maxapi.types.attachments.location import Location
from maxapi.types.attachments.contact import Contact
from maxapi.enums.upload_type import UploadType
from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
from maxapi.enums.sender_action import SenderAction
from logger_config import (
    logging_conf,
    LoggingMiddleware
)

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

from imports import (
    main_router,
    EventContext,
    TextFormat,
    Keyboards,
    MessageHandlers,
    WaitingStates
)

from imports import (
    main_router,
    EventContext,
    TextFormat,
    Keyboards,
    MessageHandlers,
    WaitingStates,
    bot  # ← ИМПОРТИРУЕМ bot из imports
)


TZ_VOLGOGRAD = pytz.timezone('Europe/Volgograd')

# test_handlers.py
"""
Простой тестовый модуль для проверки MessageHandlers.
"""

from maxapi.context import StatesGroup, State, MemoryContext




# ========== ТЕСТОВОЕ СОСТОЯНИЕ ==========
class TestStates(StatesGroup):
    waiting_for_test_message = State()


# ========== ОСНОВНОЙ ТЕСТ ==========

@main_router.message_created(Command("test"), LoggingMiddleware())
async def test_handler(event: MessageCreated, context: MemoryContext):
    """
    Тест: просит пользователя ввести сообщение.
    Команда: /test
    """
    ctx = await EventContext.from_event(event)
    ctx.log_info("🧪 Запущен тест")

    # Устанавливаем состояние
    await context.set_state(TestStates.waiting_for_test_message)
    await context.set_data({})

    # Просим ввести сообщение
    await MessageHandlers.format_received_message(
        response="✉️ **Введите любое сообщение или прикрепите вложение.**\n\n"
                 "Я покажу что вы отправили.",
        bot=bot,
        user_id=ctx.user_id,
        chat_id=ctx.chat_id,
        chat_type="dialog",
        text_format=TextFormat.MARKDOWN
    )


# ========== ОБРАБОТЧИК СООБЩЕНИЙ В ТЕСТОВОМ СОСТОЯНИИ ==========

@main_router.message_created(TestStates.waiting_for_test_message, LoggingMiddleware())
async def handle_test_message(event: MessageCreated, context: MemoryContext):
    """
    Обрабатывает сообщение в тестовом состоянии.
    Передаёт всё в MessageHandlers.format_received_message.
    """
    ctx = await EventContext.from_event(event)
    ctx.log_info("📨 Получено тестовое сообщение")

    body = event.message.body
    text = body.text or ""
    attachments = body.attachments if body else []
    chat_id = event.message.recipient.chat_id
    user_id = event.message.sender.user_id

    # Проверяем состояние
    current_state = await context.get_state()
    if current_state != TestStates.waiting_for_test_message:
        return

    # Формируем простой ответ (без дублирования логики определения вложений)
    response = "📝 **Ваше сообщение:**\n\n"

    if text:
        response += f"**Текст:**\n{text}\n\n"
    else:
        response += "**Текст:** _отсутствует_\n\n"

    # Добавляем информацию о вложениях (кратко)
    if attachments:
        response += f"📎 **Количество вложений:** {len(attachments)}\n"
        response += "ℹ️ Подробный разбор типов вложений будет в ответе MessageHandlers."
    else:
        response += "📎 **Тип вложения:** _Нет вложений_\n"

    # Получаем клавиатуру
    keyboard, _ = Keyboards.main_menu()

    # Отправляем ответ через MessageHandlers (он сам определит тип вложений)
    await MessageHandlers.format_received_message(
        response=response,
        bot=bot,
        user_id=user_id,
        chat_id=chat_id,
        attachments=attachments if attachments else None,
        keyboard=keyboard,
        text_format=TextFormat.MARKDOWN
    )

    # Сбрасываем состояние
    await context.set_state(None)
    await context.set_data({})
    ctx.log_info("✅ Тест завершён, состояние сброшено")


# ========== ОБРАБОТЧИК КНОПКИ "НАПИСАТЬ СООБЩЕНИЕ" ==========

@main_router.message_callback(LoggingMiddleware())
async def test_write_message_callback(callback: MessageCallback, context: MemoryContext):
    """
    Обработчик кнопки '✉️ Написать сообщение' (тестовый)
    """
    ctx = await EventContext.from_event(callback)
    data = callback.callback.payload
    ctx.log_info(f"📌 Тестовый callback | payload: {data}")

    if data == "write_message":
        await context.set_state(TestStates.waiting_for_test_message)
        await context.set_data({})

        await MessageHandlers.format_received_message(
            response="✉️ **Напишите сообщение**\n\n"
                     "Вы можете прикрепить:\n"
                     "📎 Файл\n"
                     "🖼️ Фото\n"
                     "🎬 Видео\n"
                     "🎵 Аудио\n"
                     "📍 Геолокацию\n"
                     "📞 Контакт\n\n"
                     "Я покажу текст и тип вложения.",
            bot=bot,
            user_id=ctx.user_id,
            chat_id=ctx.chat_id,
            chat_type="dialog",
            text_format=TextFormat.MARKDOWN
        )