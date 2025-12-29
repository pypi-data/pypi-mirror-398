class Message:
    def __init__(self, payload: dict):
        """
        Парсит входящее сообщение (Opcode 128).
        Структура payload:
        {
            "chatId": -696...,
            "unread": 1,
            "message": {
                "sender": 960...,
                "text": "Привет",
                "id": "...",
                "time": 176...
            }
        }
        """
        self._raw = payload

        self.chat_id = payload.get('chatId')
        self.unread_count = payload.get('unread')

        msg_body = payload.get('message', {})

        self.id = msg_body.get('id')
        self.text = msg_body.get('text', '')      # Текст сообщения
        self.sender_id = msg_body.get('sender')   # Кто написал
        self.timestamp = msg_body.get('time')     # Время (Unix timestamp в мс)
        self.type = msg_body.get('type')          # Обычно "USER"

        self.is_self = False

def __repr__(self):
    return f"<Message chat={self.chat_id} from={self.sender_id} text='{self.text}'>"