from imports import os, load_dotenv, Bot, Dispatcher, Router

load_dotenv()
API_TOKEN = os.getenv("MAX_BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

main_router = Router(router_id="main_router")
dp.include_routers(main_router)