#!/usr/bin/env python3
"""Multi-client TCP chat server and client."""
import sys, socket, threading, time

class ChatServer:
    def __init__(self, host="127.0.0.1", port=9090):
        self.host = host; self.port = port; self.clients = {}; self.lock = threading.Lock()

    def broadcast(self, msg, exclude=None):
        with self.lock:
            for name, conn in list(self.clients.items()):
                if name != exclude:
                    try: conn.sendall(msg.encode())
                    except: del self.clients[name]

    def handle(self, conn, addr):
        try:
            conn.sendall(b"Enter your name: ")
            name = conn.recv(1024).decode().strip()
            with self.lock: self.clients[name] = conn
            self.broadcast(f"[{name} joined]\n", name)
            print(f"{name} connected from {addr}")
            while True:
                data = conn.recv(4096)
                if not data: break
                msg = data.decode().strip()
                if msg == "/quit": break
                if msg == "/who":
                    with self.lock: conn.sendall(f"Online: {', '.join(self.clients.keys())}\n".encode())
                elif msg.startswith("/msg "):
                    parts = msg.split(" ", 2)
                    if len(parts) == 3:
                        target = parts[1]
                        with self.lock:
                            if target in self.clients:
                                self.clients[target].sendall(f"[DM from {name}] {parts[2]}\n".encode())
                else: self.broadcast(f"{name}: {msg}\n", name)
        except: pass
        finally:
            with self.lock: self.clients.pop(name, None)
            self.broadcast(f"[{name} left]\n"); conn.close()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port)); sock.listen(10)
        print(f"Chat server on {self.host}:{self.port}")
        try:
            while True:
                conn, addr = sock.accept()
                threading.Thread(target=self.handle, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt: print("\nServer stopped"); sock.close()

def client(host="127.0.0.1", port=9090):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    def recv():
        while True:
            try:
                data = sock.recv(4096)
                if not data: break
                print(data.decode(), end="", flush=True)
            except: break
    threading.Thread(target=recv, daemon=True).start()
    try:
        while True:
            msg = input()
            if msg == "/quit": sock.sendall(b"/quit"); break
            sock.sendall(f"{msg}\n".encode())
    except (KeyboardInterrupt, EOFError): pass
    finally: sock.close()

def main():
    if len(sys.argv) < 2: print("Usage: tcp_chat.py server|client [host] [port]"); return
    mode = sys.argv[1]; host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 9090
    if mode == "server": ChatServer(host, port).run()
    elif mode == "client": client(host, port)

if __name__ == "__main__": main()
