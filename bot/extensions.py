import requests
import json


class APIException(Exception):
    pass


class Converter:
    @staticmethod
    def get_price(base: str, quote: str, amount: str):
        """
        Получает цену валюты
        base - валюта, которую конвертируем
        quote - валюта, в которую конвертируем
        amount - количество
        """

        try:
            amount = float(amount)
            if amount <= 0:
                raise APIException("Количество должно быть больше 0")
        except ValueError:
            raise APIException(f"Неверное количество: '{amount}'")

        base = base.upper()
        quote = quote.upper()

        if base == quote:
            return amount

        try:
            # Бесплатный API от currencyapi.com (100 запросов в месяц бесплатно)
            # Можно зарегистрироваться на https://currencyapi.com/ для своего ключа
            # А пока используем демо-ключ (может иметь ограничения)
            api_key = "cur_live_jGkvv7GKMXWYwYSRn26AVtGDpiKX7J6blHmjEJF8"
            url = f"https://api.currencyapi.com/v3/latest?apikey={api_key}&base_currency={base}&currencies={quote}"

            response = requests.get(url, timeout=10)
            data = json.loads(response.text)

            if response.status_code != 200:
                # Пробуем запасной вариант
                return Converter.get_price_backup(base, quote, amount)

            if 'data' in data and quote in data['data']:
                rate = data['data'][quote]['value']
                return round(amount * rate, 2)
            else:
                return Converter.get_price_backup(base, quote, amount)

        except Exception as e:
            # Запасной метод если основной API не работает
            return Converter.get_price_backup(base, quote, amount)

    @staticmethod
    def get_price_backup(base: str, quote: str, amount: float):
        """Запасной метод конвертации с фиксированными курсами"""
        # Фиксированные курсы (примерные)
        rates = {
            'USD': {'EUR': 0.92, 'RUB': 92.5, 'GBP': 0.79, 'JPY': 147.5},
            'EUR': {'USD': 1.09, 'RUB': 100.5, 'GBP': 0.86, 'JPY': 160.0},
            'RUB': {'USD': 0.0108, 'EUR': 0.00995, 'GBP': 0.0085, 'JPY': 1.59},
            'GBP': {'USD': 1.27, 'EUR': 1.16, 'RUB': 117.5, 'JPY': 187.0},
            'JPY': {'USD': 0.0068, 'EUR': 0.00625, 'RUB': 0.63, 'GBP': 0.00535}
        }

        if base in rates and quote in rates[base]:
            return round(amount * rates[base][quote], 2)
        else:
            raise APIException(f"Не поддерживается конвертация {base} → {quote}")