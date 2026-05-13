from imports import  (asyncio, logging, bot, dp, MessageCreated, MessageCallback,
                      CommandStart, Command, Keyboards, logging_conf, LoggingMiddleware,
                      main_router, EventContext, log_response_detailed, CallbackHandlers,
                      BotResponses, WaitingStates, os, WEBHOOK_SECRET, WEBHOOK_URL, PORT, WEBHOOK_PATH,
                      BASE_URL, BOTHOST_DOMAIN )
from maxapi.context import MemoryContext
logging_conf()
callback_handler = CallbackHandlers()


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


# Дополнительный обработчик для диагностики (опционально)
@main_router.message_created()
async def echo_all(event):
    """Логирует все входящие сообщения (для отладки)"""
    ctx = await EventContext.from_event(event)
    ctx.log_info("Получено сообщение (echo)")


async def main():
    """Запуск бота в режиме WEBHOOK"""
    logging.info(f"🔗 Регистрирую вебхук: {WEBHOOK_URL}")
    await bot.subscribe_webhook(url=WEBHOOK_URL, secret=WEBHOOK_SECRET)

    # 3. Запускаем встроенный веб-сервер maxapi
    logging.info(f"🚀 Запуск вебхук-сервера на порту {PORT}")
    await dp.handle_webhook(
        bot=bot,
        host='0.0.0.0',
        port=PORT,
        path=WEBHOOK_PATH,
        secret=WEBHOOK_SECRET
    )


if __name__ == "__main__":
    asyncio.run(main())