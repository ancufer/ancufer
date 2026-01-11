import telebot
from telebot import types
from config import TOKEN
from extensions import Converter, APIException

# Создаем бота
bot = telebot.TeleBot(TOKEN)


# Команды /start и /help
@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = """
Привет! Я бот для конвертации валют.

Чтобы узнать курс, отправь сообщение в формате:
<валюта1> <валюта2> <количество>

Примеры:
доллар рубль 100
евро доллар 50
рубль евро 1000

Доступные валюты: USD, EUR, RUB
Команда /values покажет все валюты
"""
    bot.send_message(message.chat.id, text)


# Команда /values
@bot.message_handler(commands=['values'])
def values(message):
    text = """
Доступные валюты:

USD - Доллар США
EUR - Евро
RUB - Российский рубль

Также можно писать:
доллар, usd, $
евро, euro, eur, €
рубль, rub, ₽
"""
    bot.send_message(message.chat.id, text)


# Обработка всех текстовых сообщений
@bot.message_handler(content_types=['text'])
def convert(message):
    try:
        # Разбиваем сообщение на части
        text = message.text.strip().lower()
        parts = text.split()

        # Проверяем количество частей
        if len(parts) != 3:
            raise APIException("Неправильный формат. Нужно: валюта1 валюта2 количество")

        # Получаем параметры
        val1 = parts[0]
        val2 = parts[1]
        amount = parts[2]

        # Приводим валюты к стандартному виду
        # Для USD
        if val1 in ['доллар', 'usd', '$']:
            base = 'USD'
        elif val1 in ['евро', 'euro', 'eur', '€']:
            base = 'EUR'
        elif val1 in ['рубль', 'rub', 'р', '₽']:
            base = 'RUB'
        else:
            base = val1.upper()

        if val2 in ['доллар', 'usd', '$']:
            quote = 'USD'
        elif val2 in ['евро', 'euro', 'eur', '€']:
            quote = 'EUR'
        elif val2 in ['рубль', 'rub', 'р', '₽']:
            quote = 'RUB'
        else:
            quote = val2.upper()

        # Проверяем поддерживаемые валюты
        supported = ['USD', 'EUR', 'RUB']
        if base not in supported:
            raise APIException(f"Валюта {base} не поддерживается")
        if quote not in supported:
            raise APIException(f"Валюта {quote} не поддерживается")

        # Получаем результат
        result = Converter.get_price(base, quote, amount)

        # Форматируем ответ
        response = f"{amount} {base} = {result} {quote}"
        bot.send_message(message.chat.id, response)

    except APIException as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Что-то пошло не так: {e}")


# Запускаем бота
print("Бот запущен...")
bot.polling(none_stop=True)