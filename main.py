from imports import  (asyncio, logging, bot, dp, MessageCreated, MessageCallback,
                      CommandStart, Command, Keyboards, logging_conf, LoggingMiddleware,
                      main_router, EventContext, log_response_detailed, CallbackHandlers,
                      BotResponses, WaitingStates, json, os)
from maxapi.context import MemoryContext
from flask import Flask, request, jsonify
logging_conf()
callback_handler = CallbackHandlers()

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mySecretKey2026")


@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик входящих вебхуков от MAX"""

    # 1. Проверяем секретный заголовок (безопасность)
    received_secret = request.headers.get('X-Max-Bot-Api-Secret', '')
    if received_secret != WEBHOOK_SECRET:
        logging.warning(f"Неверный секрет вебхука: {received_secret}")
        return jsonify({"error": "forbidden"}), 403

    # 2. Получаем и парсим JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid json"}), 400

    update_type = data.get('update_type')
    logging.info(f"📨 Получен вебхук: {update_type}")

    try:
        # 3. Маршрутизация по типу события
        if update_type == "message_created":
            # Преобразуем JSON в объект события (способ зависит от вашей библиотеки maxapi)
            # Если maxapi поддерживает from_dict, используем его
            if hasattr(MessageCreated, 'from_dict'):
                event = MessageCreated.from_dict(data)
            else:
                # Альтернатива: создаём объект вручную или передаём словарь
                # Временно используем обёртку
                event = _dict_to_message_created(data)

            # Обрабатываем сообщение через вашу существующую логику
            asyncio.run(_handle_message_created(event))

        elif update_type == "message_callback":
            if hasattr(MessageCallback, 'from_dict'):
                callback = MessageCallback.from_dict(data)
            else:
                callback = _dict_to_message_callback(data)

            # Обрабатываем колбэк
            asyncio.run(_handle_message_callback(callback))

        elif update_type == "bot_started":
            # Обработка запуска бота пользователем
            chat_id = data.get('chat_id')
            user_name = data.get('user', {}).get('name', '')
            logging.info(f"Бот запущен пользователем {user_name} в чате {chat_id}")

        # Добавьте другие типы событий по необходимости

    except Exception as e:
        logging.exception(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"error": "internal error"}), 500

    # 4. Обязательно возвращаем 200 OK
    return jsonify({"ok": True}), 200


async def _handle_message_created(event):
    """Асинхронная обработка сообщения через вашу существующую маршрутизацию"""
    # Получаем текст сообщения
    text = event.message.body.text if hasattr(event.message.body, 'text') else ""

    # Маршрутизация через ваш main_router
    # Это зависит от того, как устроен ваш dispatcher

    # Пример: прямая маршрутизация
    if text == '/start':
        ctx = await EventContext.from_event(event)
        response = BotResponses.greeting()
        await event.message.answer(response)
    elif text == '/menu':
        keyboard, response_text = Keyboards.main_menu()
        await event.message.answer(text=response_text, attachments=[keyboard])
    else:
        # Другая логика...
        pass


async def _handle_message_callback(callback):
    """Асинхронная обработка колбэка"""
    await callback_handler.handle(callback, None)


def _dict_to_message_created(data):
    """Вспомогательная функция для преобразования словаря в объект MessageCreated"""
    # Это временное решение. Лучше использовать from_dict, если библиотека его поддерживает
    from maxapi.types import MessageCreated
    # Если нет from_dict, создаём объект вручную
    return MessageCreated(**data)


def _dict_to_message_callback(data):
    """Вспомогательная функция для преобразования словаря в объект MessageCallback"""
    from maxapi.types import MessageCallback
    return MessageCallback(**data)


@app.route('/health', methods=['GET'])
def health():
    """Health check для Bothost"""
    return jsonify({"status": "ok"}), 200


@app.route('/', methods=['GET'])
def index():
    """Корневой путь — просто для информации"""
    return jsonify({
        "bot": "MAX Bot",
        "status": "running",
        "webhook": "/webhook"
    }), 200


# @main_router.message_created(LoggingMiddleware())
# async def handle_audio_messages(event: MessageCreated, context: MemoryContext = None):
#     """Специальный обработчик для аудио/голосовых сообщений"""
#
#     attachments = event.message.body.attachments or []
#     att_types = [att.type for att in attachments]
#
#     # Проверяем, есть ли audio в вложениях
#     if "audio" not in att_types:
#         return  # Не аудио - игнорируем
#
#     # Проверяем состояние
#     if context:
#         current_state = await context.get_state()
#         if current_state != WaitingStates.waiting_for_message:
#             print(f"🔥 Аудио получено, но состояние не ожидания: {current_state}")
#             return
#
#     print("🔥 ПОЛУЧЕНО АУДИО/ГОЛОСОВОЕ! Обрабатываем...")
#
#     ctx = await EventContext.from_event(event)
#     user_name = event.message.sender.first_name or f"User_{ctx.user_id}"
#
#     # Обрабатываем голосовое сообщение
#     await BotResponses.format_received_message(
#         event=event,
#         context=context,
#         user_name=user_name,
#         user_id=ctx.user_id,
#         bot=bot
#     )


@main_router.message_created(CommandStart(), LoggingMiddleware())
async def start(event: MessageCreated):
    ctx = await EventContext.from_event(event)
    ctx.log_info("вызвал /start")

    response = BotResponses.greeting()
    await event.message.answer(response)

    log_response_detailed(
        chat_id=ctx.chat_id,
        response_text=response,
        reply_to=ctx.message_mid if ctx.message_mid else None
    )


@main_router.message_created(Command("menu"), LoggingMiddleware())
async def menu(event: MessageCreated):
    ctx = await EventContext.from_event(event)
    ctx.log_info("открыл меню")

    keyboard, response_text = Keyboards.main_menu()
    await event.message.answer(text=response_text, attachments=[keyboard])

    log_response_detailed(
        chat_id=ctx.chat_id,
        response_text=response_text,
        attachments=[keyboard],
        reply_to=ctx.message_mid if ctx.message_mid else None
    )


@main_router.message_callback(LoggingMiddleware())
async def callbacks(callback: MessageCallback, context: MemoryContext = None):
    ctx = await EventContext.from_event(callback)
    data = callback.callback.payload
    ctx.log_info(f"нажал кнопку: {data}")

    await callback_handler.handle(callback, context)


@main_router.message_created(WaitingStates.waiting_for_message, LoggingMiddleware())
async def waiting_message_handler(event: MessageCreated, context: MemoryContext):
    """Обрабатывает сообщения, когда бот в состоянии waiting_for_message"""

    ctx = await EventContext.from_event(event)
    user_name = event.message.sender.first_name or f"User_{ctx.user_id}"

    # Передаем bot в метод
    await BotResponses.format_received_message(
        event=event,
        context=context,
        user_name=user_name,
        user_id=ctx.user_id,
        bot=bot  # <-- передаем bot
    )


async def main():
    logging.info("🚀 Бот запущен и начал приём сообщений!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    logging.basicConfig(level=logging.INFO)
    logging.info(f"🚀 Запуск вебхук-сервера на порту {port}")
    app.run(host='0.0.0.0', port=port)