"""
WebSocket Server for Mahalla Damas Bot
Haydovchilar joylashuvini real vaqtda kuzatish va vaqt oralig'ida
haydovchilarga "Qayerdasiz yoki qaysi astanovkadasiz?" so'rovini boshqarish.
"""
import asyncio
import json
import logging
import threading
from typing import Set, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from config import WS_HOST, WS_PORT, LOCATION_PROMPT_INTERVAL_MINUTES

logger = logging.getLogger(__name__)


class DriverWebSocketServer:
    def __init__(self, host: str = WS_HOST, port: int = WS_PORT):
        self.host = host
        self.port = port
        self.bot = None
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._server = None
        self.is_running = False

    def start(self, bot=None):
        if self.is_running:
            logger.info("WebSocket server allaqachon ishlayapti.")
            return

        if bot:
            self.bot = bot

        self.is_running = True
        self._thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="DriverWebSocketThread"
        )
        self._thread.start()
        logger.info(f"🌐 WebSocket Server ishga tushirilmoqda (ws://{self.host}:{self.port})...")

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def runner():
            try:
                async with websockets.serve(self._handle_client, self.host, self.port):
                    logger.info(f"✅ WebSocket Server muvaffaqiyatli ishga tushdi: ws://{self.host}:{self.port}")
                    # Keep server running forever
                    await asyncio.Future()
            except Exception as e:
                logger.error(f"WebSocket serverda xatolik: {e}")
                self.is_running = False

        try:
            self.loop.run_until_complete(runner())
        except Exception as e:
            logger.error(f"WebSocket loop to'xtadi: {e}")
            self.is_running = False

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        self.connected_clients.add(websocket)
        client_ip = websocket.remote_address
        logger.info(f"🔌 Yangi WebSocket mijozi ulandi: {client_ip} (Jami: {len(self.connected_clients)} ta)")

        try:
            # Ulanganda salomlashish va joriy status ma'lumotlarini yuboramiz
            import api_client
            from scheduler import now_tashkent, today_tashkent

            working_drivers = api_client.get_today_statuses(status='working')
            welcome_packet = {
                "event": "connected",
                "message": "Mahalla Damas Bot WebSocket Server",
                "date": today_tashkent(),
                "time": now_tashkent(),
                "prompt_interval_minutes": LOCATION_PROMPT_INTERVAL_MINUTES,
                "working_drivers_count": len(working_drivers),
                "working_drivers": working_drivers
            }
            await websocket.send(json.dumps(welcome_packet, ensure_ascii=False))

            async for message in websocket:
                await self._handle_incoming_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.warning(f"WebSocket mijoz xatosi ({client_ip}): {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🔌 WebSocket mijozi uzildi: {client_ip} (Qoldi: {len(self.connected_clients)} ta)")

    async def _handle_incoming_message(self, websocket: WebSocketServerProtocol, raw_message: str):
        try:
            data = json.loads(raw_message)
        except Exception:
            await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON format"}))
            return

        action = data.get("action")
        logger.info(f"📥 WebSocket orqali so'rov keldi: action='{action}'")

        if action == "ping":
            await websocket.send(json.dumps({"event": "pong"}))
            return

        if action == "get_status":
            import api_client
            from scheduler import now_tashkent
            working = api_client.get_today_statuses(status='working')
            await websocket.send(json.dumps({
                "event": "status_response",
                "time": now_tashkent(),
                "working_drivers_count": len(working),
                "working_drivers": working
            }, ensure_ascii=False))
            return

        if action in ("ping_drivers", "request_locations"):
            # Haydovchilarga "qayerdasiz yoki qaysi astanovkadasiz?" so'rovini zudlik bilan yuborish
            if not self.bot:
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "Bot obyekti ulanmagan"
                }))
                return

            from scheduler import prompt_active_drivers_location
            # TeleBot so'rovlarini alohida oqimda ishlatamiz
            loop = asyncio.get_running_loop()
            count = await loop.run_in_executor(None, prompt_active_drivers_location, self.bot)

            await websocket.send(json.dumps({
                "event": "prompt_result",
                "status": "success",
                "sent_count": count,
                "message": f"{count} ta haydovchiga joylashuv so'rovi yuborildi."
            }, ensure_ascii=False))
            return

        if action == "send_message":
            telegram_id = data.get("telegram_id")
            text = data.get("text")
            if telegram_id and text and self.bot:
                try:
                    self.bot.send_message(telegram_id, text, parse_mode="HTML")
                    await websocket.send(json.dumps({
                        "status": "success",
                        "message": f"{telegram_id} ga xabar yuborildi."
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": str(e)
                    }))
            else:
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "'telegram_id' va 'text' parametrlari kerak."
                }))
            return

        await websocket.send(json.dumps({
            "status": "error",
            "message": f"Noma'lum action: '{action}'"
        }))

    def broadcast(self, payload: dict):
        """
        Telebot yoki boshqa modullardan thread-safe chaqiriladigan metod.
        Barcha ulangan WebSocket mijozlariga real vaqtda hodisa yuboradi.
        """
        if not self.is_running or not self.loop or not self.loop.is_running():
            return

        if not self.connected_clients:
            return

        message_str = json.dumps(payload, ensure_ascii=False)
        asyncio.run_coroutine_threadsafe(self._async_broadcast(message_str), self.loop)

    async def _async_broadcast(self, message_str: str):
        if not self.connected_clients:
            return

        tasks = []
        for client in list(self.connected_clients):
            try:
                tasks.append(client.send(message_str))
            except Exception:
                pass

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global yagona instansiya
ws_server = DriverWebSocketServer()
