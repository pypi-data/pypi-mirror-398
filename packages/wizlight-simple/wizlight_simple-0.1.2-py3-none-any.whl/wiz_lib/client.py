import asyncio
import json
import logging
import socket

logger = logging.getLogger(__name__)

class WizProtocol(asyncio.DatagramProtocol):
    """Protokoll für die aktive Anfrage-Antwort-Kommunikation (UDP)."""
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None
        self.response = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        self.response = data.decode()
        self.transport.close()

    def error_received(self, exc):
        logger.error(f"UDP Fehler bei Anfrage: {exc}")

    def connection_lost(self, exc):
        if not self.on_con_lost.done():
            self.on_con_lost.set_result(True)

class WizPushListener(asyncio.DatagramProtocol):
    """Protokoll zum Empfangen spontaner Status-Updates (syncPilot)."""
    def __init__(self, callback):
        self.callback = callback

    def datagram_received(self, data, addr):
        try:
            msg = json.loads(data.decode())
            # WiZ sendet 'syncPilot' bei manuellen Änderungen oder Status-Events
            if msg.get("method") == "syncPilot":
                ip = addr[0]
                params = msg.get("params", {})
                if asyncio.iscoroutinefunction(self.callback):
                    asyncio.create_task(self.callback(ip, params))
                else:
                    self.callback(ip, params)
        except Exception as e:
            logger.debug(f"Ungültiges Push-Paket von {addr}: {e}")

class SimpleWizDevice:
    def __init__(self, ip: str, mac: str = None, source: str = None):
        self.ip = ip
        self.mac = mac
        self.source = source
        self.port = 38899

    async def _send(self, method: str, params: dict = None, timeout: float = 2.0):
        """Kern-Methode für asynchrone Befehle via UDP."""
        if params is None: params = {}
        payload = json.dumps({"method": method, "params": params})

        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()

        try:
            transport, protocol = await asyncio.wait_for(
                loop.create_datagram_endpoint(
                    lambda: WizProtocol(payload, on_con_lost),
                    remote_addr=(self.ip, self.port)
                ),
                timeout=timeout
            )
            await on_con_lost
            return json.loads(protocol.response) if protocol.response else None
        except Exception as e:
            logger.debug(f"Kommunikationsfehler mit {self.ip}: {e}")
            return None

    # --- BASIS STEUERUNG ---
    async def turn_on(self):
        """Schaltet das Gerät ein."""
        return await self._send("setPilot", {"state": True})

    async def turn_off(self):
        """Schaltet das Gerät aus."""
        return await self._send("setPilot", {"state": False})

    async def set_brightness(self, level: int):
        """Setzt die Helligkeit (Dimming) von 10 bis 100."""
        level = max(10, min(100, level))
        return await self._send("setPilot", {"dimming": level})

    # --- FARBEN & SZENEN ---
    async def set_color(self, r: int, g: int, b: int):
        """Setzt eine RGB-Farbe (0-255)."""
        r, g, b = (max(0, min(255, val)) for val in (r, g, b))
        return await self._send("setPilot", {"r": r, "g": g, "b": b})

    async def set_color_temp(self, kelvin: int):
        """Setzt die Farbtemperatur in Kelvin (2200-6500)."""
        kelvin = max(2200, min(6500, kelvin))
        return await self._send("setPilot", {"temp": kelvin})

    async def set_scene(self, scene_id: int):
        """Aktiviert eine vordefinierte Lichtszene über ihre ID."""
        return await self._send("setPilot", {"sceneId": scene_id})

    # --- INTELLIGENTE MODI ---
    async def set_rhythm(self):
        """Aktiviert den zirkadianen Rhythmus-Modus."""
        return await self._send("setPilot", {"schdPwd": True})

    # --- ABFRAGEN ---
    async def get_status(self):
        """Fragt den aktuellen Status (Pilot-Daten) aktiv ab."""
        res = await self._send("getPilot")
        return res.get("result", {}) if res else {}

    async def get_power(self) -> float:
        """Gibt den aktuellen Verbrauch in Watt zurück."""
        status = await self.get_status()
        return status.get("pc", 0) / 1000

    # --- ROBUSTER PUSH LISTENER ---
    @staticmethod
    async def start_push_listener(callback):
        """
        Startet den UDP-Server für Echtzeit-Status-Updates.
        Nutzt SO_REUSEADDR und SO_REUSEPORT für maximale Stabilität.
        """
        loop = asyncio.get_running_loop()

        # Socket manuell für robustes Binding konfigurieren
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # SO_REUSEPORT für Unix-basierte Systeme (Linux/macOS)
        try:
            if hasattr(socket, 'SO_REUSEPORT'):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception:
            pass

        try:
            sock.bind(('', 38899))
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: WizPushListener(callback),
                sock=sock
            )
            logger.info("WiZ Push-Listener auf Port 38899 gestartet.")
            return transport
        except OSError as e:
            logger.error(f"Listener-Start fehlgeschlagen (Port belegt?): {e}")
            sock.close()
            return None
