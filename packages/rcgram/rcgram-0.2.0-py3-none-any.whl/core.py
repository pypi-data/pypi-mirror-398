import requests
import time

class Config:
    def __init__(self):
        self.echo = False

class TelegramPrinter:
    def __init__(self):
        self.token = None
        self.admin_id = None
        self.config = Config()
        self._last_update_id = 0

    @property
    def tobot(self):
        return "Используйте: print.tobot = 'сообщение'"

    @tobot.setter
    def tobot(self, message):
        if not self.token or not self.admin_id:
            print(f"[rcgram] Ошибка: Настройте токен и ID! Сообщение: {message}")
            return
        self._send_msg(self.admin_id, str(message))

    def _send_msg(self, chat_id, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
        except Exception as e:
            print(f"[rcgram] Ошибка отправки: {e}")

    def start_polling(self):
        """Метод для запуска эхо-бота"""
        if not self.token:
            print("[rcgram] Ошибка: Для эхо-бота нужен токен!")
            return
        
        print(f"[rcgram] Эхо-бот запущен (echo={self.config.echo})...")
        while True:
            if not self.config.echo:
                time.sleep(1)
                continue
                
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            try:
                resp = requests.get(url, params={"offset": self._last_update_id + 1}, timeout=10).json()
                if resp.get("ok"):
                    for update in resp.get("result", []):
                        self._last_update_id = update["update_id"]
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            text = update["message"]["text"]
                            # Отправляем эхо
                            self._send_msg(chat_id, text)
            except Exception as e:
                print(f"[rcgram] Ошибка опроса: {e}")
            time.sleep(1)

bot_printer = TelegramPrinter()
