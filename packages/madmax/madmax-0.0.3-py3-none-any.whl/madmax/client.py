import asyncio
import logging
from .gateway import MaxWebSocket
from .types.message import Message

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')

class Client:
    def __init__(self, token: str, device_id: str):
        self.token = token
        self.device_id = device_id
        
        # Инициализируем Gateway
        self.ws = MaxWebSocket(token, device_id, self._on_event)
        
        # Хранилище обработчиков (декораторов)
        self._handlers = {
            "message": []
        }
        self.my_id = None

    def event(self, func):
        """Декоратор для регистрации событий. 
        Пример: @client.event 
        async def on_message(msg): ...
        """
        event_name = func.__name__.replace('on_', '')
        if event_name not in self._handlers:
            self._handlers[event_name] = []

        self._handlers[event_name].append(func)
        return func

    async def _on_event(self, event_type, data):
        """Этот метод вызывает Gateway, когда что-то случилось"""
        
        if event_type == "READY":
            self.my_id = data.get('my_id')
            logging.info(f"Logged in as ID: {self.my_id}")

        elif event_type == "MESSAGE":
            # Превращаем JSON в Объект
            msg = Message(data)
            
            # Проставляем флаг, если это наше сообщение
            if self.my_id and msg.sender_id == self.my_id:
                msg.is_self = True

            # Вызываем пользовательские функции
            if "message" in self._handlers:
                for handler in self._handlers["message"]:
                    # Запускаем в фоне, чтобы не тормозить сокет
                    asyncio.create_task(handler(msg))

    def run(self):
        """Блокирующий запуск"""
        try:
            asyncio.run(self.ws.connect())
        except KeyboardInterrupt:
            print("MadMax stopped.")

    async def start(self):
        """Асинхронный запуск (для работы в паре с другими ботами)"""
        await self.ws.connect()