from enum import IntEnum

class OpCode(IntEnum):
    HEARTBEAT_PING = 1     # Сервер нас спрашивает или мы его
    HEARTBEAT_PONG = 5     # Ответ сервера (иногда)
    HANDSHAKE = 6          # Рукопожатие при входе
    AUTH_SNAPSHOT = 19     # Авторизация и данные профиля
    DISPATCH = 128         # Новое событие (сообщение)