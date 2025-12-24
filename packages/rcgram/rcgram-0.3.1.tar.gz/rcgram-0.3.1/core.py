# rcgram/core.py
import httpx
import asyncio

class Config:
    def __init__(self):
        self.echo = False

class TelegramPrinter:
    def __init__(self):
        self.token = None
        self.admin_id = None
        self.config = Config()
        self._last_update_id = 0
        self._client = httpx.AsyncClient(timeout=10)

    @property
    def tobot(self):
        return "Используйте: rcgram.tobot = 'сообщение'"

    @tobot.setter
    def tobot(self, message):
        """Отправка сообщения без блокировки основного потока"""
        if not self.token or not self.admin_id:
            print(f"[rcgram] Ошибка: Настройте токен и ID! Сообщение: {message}")
            return
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._send_msg(self.admin_id, str(message)))
            else:
                asyncio.run(self._send_msg(self.admin_id, str(message)))
        except RuntimeError:
            asyncio.run(self._send_msg(self.admin_id, str(message)))

    async def _send_msg(self, chat_id, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            await self._client.post(url, json={"chat_id": chat_id, "text": text})
        except Exception as e:
            print(f"[rcgram] Ошибка отправки: {e}")

    async def start_polling(self):
        if not self.token:
            print("[rcgram] Ошибка: Для работы нужен токен!")
            return
        
        print(f"[rcgram] Асинхронный бот запущен (echo={self.config.echo})...")
        while True:
            if not self.config.echo:
                await asyncio.sleep(1)
                continue
                
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            try:
                resp = await self._client.get(url, params={"offset": self._last_update_id + 1})
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        self._last_update_id = update["update_id"]
                        if "message" in update and "text" in update["message"]:
                            await self._send_msg(update["message"]["chat"]["id"], update["message"]["text"])
            except Exception as e:
                print(f"[rcgram] Ошибка опроса: {e}")
            await asyncio.sleep(0.5)

# Создаем объект
bot_instance = TelegramPrinter()