import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from handlers import router

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    # Загрузка переменных окружения
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        logging.error("BOT_TOKEN не найден в .env файле! Скопируйте .env.example в .env и укажите токен.")
        return

    # Инициализация бота и диспетчера
    # В aiogram 3.x свойства по умолчанию задаются через DefaultBotProperties
    bot = Bot(
        token=token, 
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Инициализация планировщика
    # Устанавливаем часовой пояс МСК
    moscow_tz = pytz.timezone('Europe/Moscow')
    scheduler = AsyncIOScheduler(timezone=moscow_tz)
    scheduler.start()

    # Передаем планировщик в хендлеры через context
    dp["scheduler"] = scheduler
    
    # Регистрация роутеров
    dp.include_router(router)

    # Запуск поллинга
    try:
        logging.info("Бот запущен и готов к работе.")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Произошла ошибка при работе бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
