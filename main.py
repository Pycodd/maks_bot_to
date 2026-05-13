from imports import  (asyncio, logging, bot, dp, MessageCreated, MessageCallback,
                      CommandStart, Command, Keyboards, logging_conf, LoggingMiddleware,
                      main_router, EventContext, log_response_detailed, CallbackHandlers,
                      BotResponses, WaitingStates, json, os)
from maxapi.context import MemoryContext
from flask import Flask, request, jsonify
import requests

logging_conf()
callback_handler = CallbackHandlers()
logger = logging.getLogger(__name__)
app = Flask(__name__)
TOKEN = os.getenv("MAX_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mySecretKey2026")
BASE_URL = "https://platform-api.max.ru"


def send_message(chat_id: int, text: str, attachments: list = None) -> dict:
    """Отправить сообщение через MAX Bot API (синхронно)"""
    payload = {"chat_id": chat_id, "text": text}
    if attachments:
        payload["attachments"] = attachments
    resp = requests.post(
        f"{BASE_URL}/messages",
        headers={"Authorization": TOKEN, "Content-Type": "application/json"},
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


def answer_callback(callback_id: str, text: str = "") -> dict:
    """Ответить на callback-запрос (убрать 'часики' с кнопки)"""
    resp = requests.post(
        f"{BASE_URL}/answers",
        headers={"Authorization": TOKEN, "Content-Type": "application/json"},
        json={"callback_id": callback_id, "text": text},  # <-- поле "text"
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. Проверяем подпись
    received_secret = request.headers.get("X-Max-Bot-Api-Secret", "")
    if WEBHOOK_SECRET and received_secret != WEBHOOK_SECRET:
        logger.warning("Неверная подпись webhook-запроса")
        return jsonify({"error": "forbidden"}), 403

    # 2. Разбираем обновление
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400

    update_type = data.get("update_type", "")
    logger.info("Получено событие: %s", update_type)

    # 3. Маршрутизация по типу события
    try:
        if update_type == "message_created":
            handle_message(data)
        elif update_type == "message_callback":
            handle_callback(data)
        elif update_type == "bot_started":
            handle_bot_started(data)
        elif update_type == "bot_added":
            handle_bot_added(data)
        elif update_type == "message_edited":
            logger.info("Сообщение отредактировано: %s", data)
    except Exception as e:
        logger.exception("Ошибка обработки: %s", e)

    # 4. Возвращаем 200
    return jsonify({"ok": True}), 200


def handle_message(data: dict):
    """Обработка сообщений (синхронная, как в примере MAX)"""
    msg = data.get("message", {})
    chat_id = msg.get("recipient", {}).get("chat_id")
    text = msg.get("body", {}).get("text", "")
    if not chat_id:
        return

    if text == "/start":
        send_message(chat_id, "Добро пожаловать! Напишите /menu для списка команд.")
    elif text == "/menu":
        keyboard, response_text = Keyboards.main_menu()
        send_message(chat_id, response_text, attachments=[keyboard])
    else:
        # Сообщение в свободной форме — обрабатываем как waiting_for_message
        # Здесь сохраните логику получения сообщений
        send_message(chat_id, f"Вы написали: {text}")


def handle_callback(data: dict):
    """Обработка нажатий кнопок"""
    cb = data.get("callback", {})
    chat_id = cb.get("message", {}).get("recipient", {}).get("chat_id")
    payload = cb.get("payload", "")
    callback_id = cb.get("callback_id", "")

    if callback_id:
        answer_callback(callback_id)

    # Передаём в ваш существующий обработчик
    # Так как callback_handler асинхронный, а нам нужен синхронный вызов,
    # временно используем прямую логику
    if payload == "settings":
        send_message(chat_id, "⚙️ Настройки бота...")
    elif payload == "info":
        send_message(chat_id, "ℹ️ Информация о боте...")
    else:
        send_message(chat_id, f"Нажата кнопка: {payload}")


def handle_bot_started(data: dict):
    chat_id = data.get("chat_id")
    user_name = data.get("user", {}).get("name", "")
    if chat_id:
        send_message(chat_id, f"Привет, {user_name}! Напишите /menu для начала.")


def handle_bot_added(data: dict):
    chat_id = data.get("chat_id")
    if chat_id:
        send_message(chat_id, "Бот добавлен в чат. Напишите /menu для списка команд.")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)