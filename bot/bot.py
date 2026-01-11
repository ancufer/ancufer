import telebot
from config import TOKEN
from extensions import Converter, APIException

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = """
Привет! Я бот для конвертации валют.

Формат:
<валюта1> <валюта2> <количество>

Примеры:
доллар рубль 100
евро доллар 50
рубль евро 1000
usd eur 25

Доступные валюты: /values
"""
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['values'])
def values(message):
    text = """
Доступные валюты (пишите кодами):

USD - Доллар США
EUR - Евро
RUB - Российский рубль
GBP - Фунт стерлингов
JPY - Японская иена
CAD - Канадский доллар
AUD - Австралийский доллар
CHF - Швейцарский франк
CNY - Китайский юань

Или можно писать:
доллар, usd, $
евро, eur, €
рубль, rub, ₽
"""
    bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=['text'])
def convert(message):
    try:
        text = message.text.strip().lower()
        parts = text.split()

        if len(parts) != 3:
            raise APIException("Нужно 3 значения: валюта1 валюта2 количество")

        val1, val2, amount = parts

        # Конвертируем названия в коды валют
        currencies = {
            'доллар': 'USD', 'usd': 'USD', '$': 'USD',
            'евро': 'EUR', 'eur': 'EUR', 'euro': 'EUR', '€': 'EUR',
            'рубль': 'RUB', 'rub': 'RUB', 'р': 'RUB', '₽': 'RUB',
            'фунт': 'GBP', 'gbp': 'GBP',
            'иена': 'JPY', 'jpy': 'JPY',
            'юань': 'CNY', 'cny': 'CNY',
        }

        base = currencies.get(val1, val1.upper())
        quote = currencies.get(val2, val2.upper())

        result = Converter.get_price(base, quote, amount)

        response = f"{amount} {base} = {result} {quote}"
        bot.send_message(message.chat.id, response)

    except APIException as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}\n\nИспользуйте /help для инструкций")
    except Exception as e:
        bot.send_message(message.chat.id, f"Неизвестная ошибка: {e}")


print("Бот запускается...")
bot.polling(none_stop=True, interval=0)