import asyncio
from logging import getLogger
from typing import Any, Callable, Coroutine, Dict, Optional

import websockets
from orjson import JSONDecodeError, loads

from .client import Client
from .utils.objects import Message


class Socket:
    def __init__(
        self,
        client: Client,
        message_handler: Callable[[Client, Message], Coroutine[Any, Any, None]],
        ws_url: str = "wss://ws.kyodo.app/",
        enable_trace_toggle: bool = False,
    ):
        self.ws: Optional[websockets.ClientConnection] = None
        self.logger = getLogger(__name__)
        self.client = client
        self.ws_url = ws_url
        self.message_handler = message_handler
        self.running = False
        self.ping_task = None
        self.listener_task = None
        if enable_trace_toggle:
            self.logger.info(
                "Trace enabled requested, but websockets library doesn't support enableTrace"
            )

    async def on_message(self, message: str | bytes) -> None:
        self.logger.debug("Received message: %s", message)
        try:
            data: Dict[str, Any] = loads(message)
            if data.get("o", 0) == 1:
                await self.message_handler(self.client, Message(data.get("d") or {}))
        except JSONDecodeError:
            self.logger.warning("!!Cannot decode message: %s", message)

    async def on_close(self, code: int, reason: str) -> None:
        self.logger.debug("Socket closed with code %s and reason %s", code, reason)

    async def run(self) -> None:
        uri = f"{self.ws_url}?token={self.client.auth_token}&deviceId={self.client.device_id}"
        self.running = True
        while self.running:
            try:
                async with websockets.connect(
                    uri, ping_interval=10, ping_timeout=5, close_timeout=5
                ) as websocket:
                    self.ws = websocket
                    self.logger.info("Connected to WebSocket server! Listening...")
                    while self.running:
                        try:
                            message = await websocket.recv()
                            await self.on_message(message)
                        except websockets.exceptions.ConnectionClosed as e:
                            await self.on_close(e.code, e.reason)
                            break
            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(1)  # Reconnect delay

    async def failsafe_ping(self):
        while self.running and self.ws:
            try:
                await self.ws.send('{"o":7,"d":{}}')
            except Exception as e:
                self.logger.debug(f"Ping error: {e}")
            await asyncio.sleep(10)

    def listen_forever(self, failsafe_ping_enabled: bool = False) -> asyncio.Task:
        loop = asyncio.get_event_loop()
        self.listener_task = loop.create_task(self.run())
        if failsafe_ping_enabled:
            self.ping_task = loop.create_task(self.failsafe_ping())
        return self.listener_task
