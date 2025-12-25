import socket
import threading
import json


# ====================================================
# ChatVPN SERVER  (built into this file)
# ====================================================
class ChatVPNServer:
    def __init__(self, host="0.0.0.0", port=9001):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.clients = set()
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        print(f"[ChatVPN-Server] running on {self.host}:{self.port}")
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            data, addr = self.sock.recvfrom(4096)

            if addr not in self.clients:
                self.clients.add(addr)
                print(f"[ChatVPN-Server] new client: {addr}")

            for c in self.clients:
                if c != addr:
                    self.sock.sendto(data, c)

    def stop(self):
        self.running = False
        self.sock.close()
        print("[ChatVPN-Server] stopped.")


# ====================================================
# ChatVPN CLIENT
# ====================================================
class ChatVPN:
    def __init__(self, server_ip: str, port: int = 9001):
        self.server = (server_ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False
        self._on_msg = None

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        print(f"[ChatVPN-Client] connected to {self.server}")

    def send(self, text: str):
        packet = json.dumps({"type": "text", "data": text}).encode()
        self.sock.sendto(packet, self.server)

    def on_msg(self, func):
        self._on_msg = func

    def _recv_loop(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
            except OSError:
                break

            try:
                obj = json.loads(data.decode())
                msg = obj.get("data", "")
            except:
                msg = data.decode()

            if self._on_msg:
                self._on_msg(msg)

