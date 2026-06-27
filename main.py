from imports import  (asyncio, logging, bot, dp, MessageCreated, CommandStart, Command, Keyboards, logging_conf,
                      LoggingMiddleware, main_router, EventContext, log_response_detailed,
                      BotResponses, WaitingStates, WEBHOOK_SECRET, WEBHOOK_URL, PORT, WEBHOOK_PATH,
                      populate_initial_data, init_db, MemoryContext, MessageHandlers, MessageCallback, RegistrationStates, TextFormat)
from callback_handlers import (
    CallbackHandlers
)

from test_handlers import *

logging_conf()
callback_handler = CallbackHandlers()

# ========== ОБРАБОТЧИК /start ==========
@main_router.message_created(CommandStart(), LoggingMiddleware())
async def start(event: MessageCreated, context: MemoryContext):
    """Обработчик команды /start — только собирает данные и передаёт в callback_handlers."""
    ctx = await EventContext.from_event(event)
    ctx.log_info("вызвал /start")

    user_name = event.message.sender.first_name or "Пользователь"

    # Вся логика в callback_handlers
    await CallbackHandlers.handle_start(event, context, user_name, bot)


@main_router.message_callback(LoggingMiddleware())
async def callbacks(callback: MessageCallback, context: MemoryContext = None):
    ctx = await EventContext.from_event(callback)
    data = callback.callback.payload
    ctx.log_info(f"нажал кнопку: {data}")

    await callback_handler.handle(callback, context, bot)


MODE_WEBHOOK = False


# Режим 2: LONG POLLING (для разработки/тестирования)
# MODE_WEBHOOK = False, True
# ============================================================


async def main_webhook():
    """Запуск бота в режиме WEBHOOK"""
    logging.info(f"🔗 Регистрирую вебхук: {WEBHOOK_URL}")
    await bot.subscribe_webhook(url=WEBHOOK_URL, secret=WEBHOOK_SECRET)

    logging.info(f"🚀 Запуск вебхук-сервера на порту {PORT}")
    await dp.handle_webhook(
        bot=bot,
        host='0.0.0.0',
        port=PORT,
        path=WEBHOOK_PATH,
        secret=WEBHOOK_SECRET
    )


async def main_polling():
    """Запуск бота в режиме LONG POLLING"""
    logging.info("🚀 Запуск бота в режиме Long Polling")

    try:
        await bot.delete_webhook()
        logging.info("✅ Вебхук удалён (если был)")
    except Exception as e:
        logging.warning(f"Не удалось удалить вебхук: {e}")
    await dp.start_polling(bot)


async def main():
    """Универсальный запуск бота"""
    if MODE_WEBHOOK:
        logging.info("=" * 50)
        logging.info("🔵 ЗАПУСК В РЕЖИМЕ WEBHOOK")
        logging.info("=" * 50)
        await main_webhook()
    else:
        logging.info("=" * 50)
        logging.info("🟢 ЗАПУСК В РЕЖИМЕ LONG POLLING")
        logging.info("=" * 50)
        await main_polling()


if __name__ == "__main__":
    init_db()
    populate_initial_data()
    asyncio.run(main())