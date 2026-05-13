from imports import os, load_dotenv, Bot, Dispatcher, Router

load_dotenv()
API_TOKEN = os.getenv("MAX_BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

main_router = Router(router_id="main_router")
dp.include_routers(main_router)

BASE_URL = "https://platform-api.max.ru"

# Webhook конфигурация
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "my_secret_key_2026")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 3000))

# Bothost домен (публичный URL)
BOTHOST_DOMAIN = os.getenv("BOTHOST_DOMAIN", "bot-1778649490-6034-d-andrey-v.bothost.tech")
WEBHOOK_URL = f"https://{BOTHOST_DOMAIN}{WEBHOOK_PATH}"