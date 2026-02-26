from aiogram import Router, types, F
from aiogram.filters import CommandStart
from utils import parse_reminder
from datetime import datetime
import logging
import pytz

router = Router()
moscow_tz = pytz.timezone('Europe/Moscow')

async def send_reminder(bot, chat_id, text):
    try:
        await bot.send_message(chat_id, f"🔔 Напоминание: {text}")
    except Exception as e:
        logging.error(f"Ошибка при отправке напоминания: {e}")

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот-напоминалка.\n\n"
        "Я понимаю обычные и повторяющиеся напоминания:\n"
        "• **Каждый день**: 'каждый день пить витамины в 9:00'\n"
        "• **Каждую неделю**: 'каждый понедельник планерка в 10:00'\n"
        "• **Разовые**: 'вынести мусор через 10 минут' или 'завтра в 12'\n\n"
        "Если время не указано, я поставлю его на 09:00."
    )

@router.message()
async def handle_message(message: types.Message, scheduler):
    text = message.text
    if not text:
        return

    res = parse_reminder(text)
    
    if not res:
        await message.answer(
            "Не удалось распознать дату или время. \n"
            "Попробуйте так: 'каждый день в 10:00 делать зарядку' или '20 марта к врачу'."
        )
        return

    reminder_text = res['text']
    now = datetime.now(moscow_tz).replace(tzinfo=None)
    # Уникальный ID для задачи
    job_id = f"remind_{message.chat.id}_{now.timestamp()}"
    
    if res.get('is_recurring'):
        if res['type'] == 'daily':
            scheduler.add_job(
                send_reminder,
                trigger='cron',
                hour=res['time'].hour,
                minute=res['time'].minute,
                args=[message.bot, message.chat.id, reminder_text],
                id=job_id
            )
            when_str = f"каждый день в {res['time'].strftime('%H:%M')}"
        else: # weekly
            scheduler.add_job(
                send_reminder,
                trigger='cron',
                day_of_week=res['day_of_week'],
                hour=res['time'].hour,
                minute=res['time'].minute,
                args=[message.bot, message.chat.id, reminder_text],
                id=job_id
            )
            when_str = f"каждую неделю ({res['day_of_week']}) в {res['time'].strftime('%H:%M')}"
    else:
        remind_at = res['datetime']
        if remind_at < now:
            await message.answer(
                f"Указанное время {remind_at.strftime('%d.%m.%Y %H:%M')} уже в прошлом."
            )
            return

        scheduler.add_job(
            send_reminder,
            trigger='date',
            run_date=remind_at,
            args=[message.bot, message.chat.id, reminder_text],
            id=job_id
        )
        when_str = remind_at.strftime('%d.%m.%Y %H:%M')

    await message.answer(
        f"✅ Напоминание установлено!\n"
        f"📝 **Что:** {reminder_text}\n"
        f"⏰ **Когда:** {when_str}",
        parse_mode="Markdown"
    )
