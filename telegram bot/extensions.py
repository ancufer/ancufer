import requests
import json


# Свой класс для ошибок
class APIException(Exception):
    pass


# Класс для работы с API
class Converter:
    @staticmethod
    def get_price(base: str, quote: str, amount: str):
        """
        Получает цену валюты
        base - валюта, которую конвертируем
        quote - валюта, в которую конвертируем
        amount - количество
        """

        # Проверяем, что количество - число
        try:
            amount = float(amount)
        except ValueError:
            raise APIException(f"Не удалось обработать количество '{amount}'")

        # Если валюты одинаковые
        if base == quote:
            return amount

        # Делаем запрос к API
        try:
            # Используем бесплатный API без ключа
            url = f"https://api.exchangerate-api.com/v4/latest/{base}"
            response = requests.get(url)
            data = json.loads(response.text)

            # Проверяем успешность запроса
            if response.status_code != 200:
                raise APIException(f"Ошибка API: {response.status_code}")

            # Получаем курс
            if quote in data['rates']:
                rate = data['rates'][quote]
                return round(amount * rate, 2)
            else:
                raise APIException(f"Валюта {quote} не найдена")

        except requests.exceptions.RequestException as e:
            raise APIException(f"Ошибка соединения: {e}")
        except Exception as e:
            raise APIException(f"Ошибка: {e}")