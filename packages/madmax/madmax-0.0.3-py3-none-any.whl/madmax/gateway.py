import asyncio
import aiohttp
import json
import logging
from .enums import OpCode

log = logging.getLogger("madmax.gateway")

class MaxWebSocket:
    def __init__(self, token: str, device_id: str, dispatch_callback):
        self.token = token
        self.device_id = device_id
        self.dispatch = dispatch_callback
        self.ws = None
        self.seq = 0
        self._keep_alive_task = None

    async def send_json(self, opcode: int, payload: dict = None):
        """Упаковка и отправка пакета"""
        if not self.ws or self.ws.closed:
            return
            
        data = {
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": opcode,
            "payload": payload
        }
        self.seq += 1
        await self.ws.send_json(data)

    async def _heartbeat(self):
        """Задача которая не дает серверу убить нас"""
        log.debug("❤️ Heartbeat task started")
        while True:
            await asyncio.sleep(30)
            try:
                if self.ws and not self.ws.closed:
    
                    await self.send_json(OpCode.HEARTBEAT_PING, {"interactive": False})
                else:
                    break
            except Exception:
                break

    async def connect(self):
        """Главный цикл подключения"""
        headers = {
            "Origin": "https://web.max.ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cache-Control": "no-cache"
        }
        url = "wss://ws-api.oneme.ru/websocket"

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    log.info("Connecting to Gateway...")
                    async with session.ws_connect(url, headers=headers, ssl=False) as ws:
                        self.ws = ws
                        self.seq = 0
                        log.info("Connected! Handshaking...")

                        # 1. Отправляем Handshake
                        await self.send_json(OpCode.HANDSHAKE, {
                            "deviceId": self.device_id,
                            "userAgent": {"deviceType": "WEB", "deviceName": "Chrome"},
                            "appVersion": "25.12.11"
                        })

                        # 2. Запускаем сердцебиение
                        self._keep_alive_task = asyncio.create_task(self._heartbeat())

                        # 3. Слушаем ответы
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                op = data.get('opcode')
                                cmd = data.get('cmd')
                                payload = data.get('payload', {})

                                # Если пришел ответ на Handshake: Шлем авторизацию
                                if op == OpCode.HANDSHAKE and cmd == 1:
                                    log.info("Handshake OK. Authorizing...")
                                    await self.send_json(OpCode.AUTH_SNAPSHOT, {
                                        "chatsCount": 10,
                                        "interactive": True,
                                        "token": self.token
                                    })

                                # Если пришла авторизация (snapshot): Мы готовы
                                elif op == OpCode.AUTH_SNAPSHOT and cmd == 1:
                                    log.info(f"Authorized! Ready.")
                                    # ID из профиля
                                    my_id = payload.get('profile', {}).get('id')
                                    # Cобытие "READY"
                                    await self.dispatch("READY", {"my_id": my_id})

                                # Если пришло сообщение: Кидаем наверх
                                elif op == OpCode.DISPATCH:
                                    await self.dispatch("MESSAGE", payload)

                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                log.warning("WebSocket closed unexpectedly.")
                                break
                                
                except Exception as e:
                    log.error(f"Connection error: {e}")
                    log.info("Reconnecting in 5s...")
                    await asyncio.sleep(5)
                finally:
                    if self._keep_alive_task:
                        self._keep_alive_task.cancel()