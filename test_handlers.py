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
    await event.message.answer(
        text="✉️ **Введите любое сообщение или прикрепите вложение.**\n\n"
             "Я покажу что вы отправили.",
        format=TextFormat.MARKDOWN
    )


# ========== ОБРАБОТЧИК СООБЩЕНИЙ В ТЕСТОВОМ СОСТОЯНИИ ==========

@main_router.message_created(TestStates.waiting_for_test_message, LoggingMiddleware())
async def handle_test_message(event: MessageCreated, context: MemoryContext):
    """
    Обрабатывает сообщение в тестовом состоянии.
    Использует MessageHandlers для ответа.
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

    # Формируем ответ
    response = "📝 **Ваше сообщение:**\n\n"

    if text:
        response += f"**Текст:**\n{text}\n\n"
    else:
        response += "**Текст:** _отсутствует_\n\n"

    # Определяем тип вложения
    if attachments:
        response += "📎 **Тип вложения:**\n"
        for att in attachments:
            if isinstance(att, Image):
                att_type = "🖼️ Фото"
            elif isinstance(att, Video):
                att_type = "🎬 Видео"
            elif isinstance(att, Audio):
                att_type = "🎵 Аудио"
            elif isinstance(att, File):
                att_type = "📎 Файл"
            elif isinstance(att, Location):
                att_type = "📍 Геолокация"
            elif isinstance(att, Contact):
                att_type = "📞 Контакт"
            elif isinstance(att, Sticker):
                att_type = "🏷️ Стикер"
            else:
                att_type = f"❓ {type(att).__name__}"
            response += f"• {att_type}\n"
    else:
        response += "📎 **Тип вложения:** _Нет вложений_\n"

    # Получаем клавиатуру
    keyboard, _ = Keyboards.main_menu()

    # Отправляем ответ через MessageHandlers
    if attachments:
        await MessageHandlers.format_received_message(
            event=event,
            response=response,
            bot=bot,
            user_id=user_id,
            chat_id=chat_id,
            attachments=attachments,
            keyboard=keyboard,
            text_format=TextFormat.MARKDOWN
        )
    else:
        await MessageHandlers.format_received_message(
            event=event,
            response=response,
            bot=bot,
            user_id=user_id,
            chat_id=chat_id,
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
    ctx.log_info(f"нажал кнопку: {data}")

    if data == "write_message":
        await context.set_state(TestStates.waiting_for_test_message)
        await context.set_data({})
        await callback.message.answer(
            text="✉️ **Напишите сообщение**\n\n"
                 "Вы можете прикрепить:\n"
                 "📎 Файл\n"
                 "🖼️ Фото\n"
                 "🎬 Видео\n"
                 "🎵 Аудио\n"
                 "📍 Геолокацию\n"
                 "📞 Контакт\n\n"
                 "Я покажу текст и тип вложения.",
            format=TextFormat.MARKDOWN
        )