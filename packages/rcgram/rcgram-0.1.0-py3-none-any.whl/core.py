import requests

class TelegramPrinter:
    def __init__(self):
        self.token = None
        self.admin_id = None

    @property
    def tobot(self):
        return "Используйте: print.tobot = 'сообщение'"

    @tobot.setter
    def tobot(self, message):
        if not self.token or not self.admin_id:
            # Если конфиги не заданы, просто выводим в консоль
            print(f"[rcgram] Ошибка: Настройте print.token и print.admin_id! Сообщение: {message}")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.admin_id, "text": str(message)}
        
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[rcgram] Ошибка сети: {e}")

# Создаем объект внутри модуля
bot_printer = TelegramPrinter()
