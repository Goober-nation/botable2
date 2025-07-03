import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config.settings import settings
from bot.handlers import BotHandlers
from data.user_storage import user_storage

# Проверяем настройки
settings.validate()

# Настройка логирования для Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("/app/logs/bot.log") if os.path.exists("/app/logs") else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создаем приложение Telegram бота
ptb_app = Application.builder().token(settings.BOT_TOKEN).build()

# Регистрируем обработчики команд
ptb_app.add_handler(CommandHandler("start", BotHandlers.start_command))
ptb_app.add_handler(CommandHandler("set_filters", BotHandlers.set_filters_command))
ptb_app.add_handler(CommandHandler("register", BotHandlers.set_filters_command))
ptb_app.add_handler(CommandHandler("website", BotHandlers.website_command))
ptb_app.add_handler(CommandHandler("package", BotHandlers.manual_package_command))
ptb_app.add_handler(CallbackQueryHandler(BotHandlers.button_callback))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    await ptb_app.initialize()
    logger.info("PTB приложение инициализировано.")

    webhook_url = f"{settings.WEBHOOK_URL}/webhook"
    await ptb_app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info(f"Webhook установлен на: {webhook_url}")

    await ptb_app.start()
    logger.info("PTB приложение запущено в Docker контейнере.")
    logger.info("Упаковщик настроен для работы по требованию (при сохранении фильтров)")

    yield

    # Остановка
    logger.info("Остановка PTB приложения...")
    await ptb_app.stop()
    await ptb_app.bot.delete_webhook()
    await ptb_app.shutdown()
    logger.info("PTB приложение остановлено.")


# Создаем FastAPI приложение
app = FastAPI(lifespan=lifespan, title="DAHA Telegram Bot")


@app.post("/webhook")
async def process_update(request: Request):
    """Обработка обновлений от Telegram"""
    update_data = await request.json()
    update = Update.de_json(update_data, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"status": "ok"}


@app.get("/package_status")
async def package_status():
    """Эндпоинт для проверки статуса упаковщика"""
    return {
        "total_users": user_storage.get_user_count(),
        "packager_mode": "on_demand",
        "container": "docker",
        "last_check": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "users_count": user_storage.get_user_count(),
        "environment": "docker"
    }


if __name__ == "__main__":
    # Создаем директории если их нет
    os.makedirs("/app/logs", exist_ok=True)
    os.makedirs("/app/exports", exist_ok=True)

    uvicorn.run(app, host="0.0.0.0", port=8000)
