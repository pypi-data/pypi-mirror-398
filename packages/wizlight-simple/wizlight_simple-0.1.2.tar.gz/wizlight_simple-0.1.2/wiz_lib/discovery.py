import asyncio
import socket
import json
import logging
from zeroconf import Zeroconf, ServiceBrowser
from typing import List, Dict
from .client import SimpleWizDevice

# Logging einrichten
logger = logging.getLogger(__name__)

class MatterListener:
    """Listener für die mDNS/Matter Erkennung."""
    def __init__(self, found_dict: Dict[str, Dict]):
        self.found_dict = found_dict

    def add_service(self, zc: Zeroconf, type_: str, name: str):
        info = zc.get_service_info(type_, name)
        if info:
            for addr in info.addresses:
                ip = socket.inet_ntoa(addr)
                if ip not in self.found_dict:
                    self.found_dict[ip] = {
                        "mac": "Unknown",
                        "source": "Matter/mDNS"
                    }
                    logger.debug(f"Gerät via Matter gefunden: {ip}")

    def update_service(self, zc, type_, name): pass
    def remove_service(self, zc, type_, name): pass

class SimpleWizScanner:
    """Scanner-Klasse zum Finden von WiZ-Geräten im lokalen Netzwerk."""

    @staticmethod
    async def discover(timeout: float = 3.0) -> List[SimpleWizDevice]:
        """
        Sucht parallel via UDP-Broadcast und mDNS nach Geräten.
        """
        found_devices: Dict[str, Dict] = {}
        loop = asyncio.get_running_loop()

        # 1. Matter/mDNS Discovery
        zc = Zeroconf()
        listener = MatterListener(found_devices)
        browser = ServiceBrowser(zc, "_matter._tcp.local.", listener)

        # 2. WiZ UDP-Broadcast Discovery
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)

        broadcast_msg = json.dumps({"method": "getSystemConfig", "params": {}}).encode()

        try:
            # Broadcast senden
            await loop.sock_sendto(sock, broadcast_msg, ("255.255.255.255", 38899))

            end_time = loop.time() + timeout
            while loop.time() < end_time:
                try:
                    # FIX: sock_recvfrom statt sock_recv nutzen, um (data, addr) zu erhalten
                    data, addr = await asyncio.wait_for(
                        loop.sock_recvfrom(sock, 1024),
                        timeout=0.5
                    )
                    res = json.loads(data.decode())
                    ip = addr[0]

                    # MAC Adresse aus der Antwort extrahieren
                    mac = res.get("result", {}).get("mac")

                    found_devices[ip] = {
                        "mac": mac,
                        "source": "WiZ-UDP"
                    }
                except (asyncio.TimeoutError, BlockingIOError):
                    continue
                except Exception as e:
                    logger.error(f"Fehler beim UDP Scan: {e}")

        finally:
            sock.close()
            browser.cancel()
            zc.close()

        return [
            SimpleWizDevice(ip, data["mac"], data["source"])
            for ip, data in found_devices.items()
        ]
