import dateparser
from dateparser.search import search_dates
from datetime import datetime, time, timedelta
import re
import pytz

DAYS_MAP = {
    'понедельник': 'mon', 'пн': 'mon',
    'вторник': 'tue', 'вт': 'tue',
    'среда': 'wed', 'ср': 'wed',
    'четверг': 'thu', 'чт': 'thu',
    'пятница': 'fri', 'пт': 'fri',
    'суббота': 'sat', 'сб': 'sat',
    'воскресенье': 'sun', 'вс': 'sun'
}

def parse_reminder(text: str):
    """
    Парсит сообщение пользователя, выделяя текст напоминания, дату/время и тип повторения.
    """
    text_lower = text.lower()
    is_recurring = False
    recurrence_type = None  # 'daily', 'weekly'
    day_of_week = None
    
    # Проверка на "каждый день"
    if any(phrase in text_lower for phrase in ["каждый день", "ежедневно"]):
        is_recurring = True
        recurrence_type = 'daily'
        # Убираем эти слова для дальнейшего парсинга времени
        text = re.sub(r'(каждый день|ежедневно)', '', text, flags=re.IGNORECASE).strip()
    
    # Проверка на "каждый [день недели]"
    else:
        for day_name, day_code in DAYS_MAP.items():
            pattern = rf'кажд[аый][яй]\s+{day_name}'
            if re.search(pattern, text_lower):
                is_recurring = True
                recurrence_type = 'weekly'
                day_of_week = day_code
                # Убираем эти слова
                text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                break

    # Настройки для dateparser
    settings = {
        'PREFER_DATES_FROM': 'future',
        'RETURN_AS_TIMEZONE_AWARE': False,
        'PREFER_DAY_OF_MONTH': 'current',
    }
    
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz).replace(tzinfo=None) # Работаем с naive datetime для совместимости с dateparser
    
    # Ищем даты/время в оставшемся тексте
    results = search_dates(text, languages=['ru'], settings=settings)
    
    if not results:
        # Если это регулярное событие, но время не указано - ставим 09:00
        if is_recurring:
            reminder_text = text.strip() or "Напоминание"
            return {
                'text': reminder_text,
                'is_recurring': True,
                'type': recurrence_type,
                'day_of_week': day_of_week,
                'time': time(9, 0),
                'datetime': None
            }
        return None

    # Берем первое найденное совпадение
    date_str, date_obj = results[0]
    reminder_text = text.replace(date_str, "").strip() or "Напоминание"
    
    # Список признаков того, что пользователь указал время
    time_indicators = [":", " в ", " в", "в ", "утра", "вечера", "дня", "ночи", "через", "спустя", "мин", "час"]
    has_time_indicator = any(indicator in date_str.lower() for indicator in time_indicators)
    
    # Если время в объекте 00:00 и в строке нет явных признаков времени
    if date_obj.time() == time(0, 0) and not has_time_indicator:
        date_obj = date_obj.replace(hour=9, minute=0)
    
    if is_recurring:
        return {
            'text': reminder_text,
            'is_recurring': True,
            'type': recurrence_type,
            'day_of_week': day_of_week,
            'time': date_obj.time(),
            'datetime': None
        }

    # Логика "сегодня или завтра" для разовых событий без даты
    if date_obj < now and "через" not in date_str.lower() and "спустя" not in date_str.lower():
        if date_obj.date() == now.date():
            date_obj += timedelta(days=1)
            
    return {
        'text': reminder_text,
        'is_recurring': False,
        'datetime': date_obj
    }
