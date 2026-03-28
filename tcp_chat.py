#!/usr/bin/env python3
"""tcp_chat - TCP chat server and client."""
import argparse, socket, threading, sys

def server(host, port):
    clients = []; lock = threading.Lock()
    def broadcast(msg, sender=None):
        with lock:
            for c in clients:
                if c != sender:
                    try: c.sendall(msg)
                    except: pass
    def handle(conn, addr):
        name = conn.recv(1024).decode().strip()
        broadcast(f"[{name} joined]\n".encode())
        print(f"{name} connected from {addr}")
        with lock: clients.append(conn)
        try:
            while True:
                data = conn.recv(4096)
                if not data: break
                broadcast(f"{name}: {data.decode()}".encode(), conn)
        except: pass
        with lock: clients.remove(conn)
        broadcast(f"[{name} left]\n".encode())
        conn.close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port)); sock.listen(5)
    print(f"Chat server on {host}:{port}")
    try:
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt: sock.close()

def client(host, port, name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port)); sock.sendall(f"{name}\n".encode())
    def recv():
        while True:
            data = sock.recv(4096)
            if not data: break
            sys.stdout.write(data.decode()); sys.stdout.flush()
    threading.Thread(target=recv, daemon=True).start()
    try:
        while True:
            msg = input()
            sock.sendall(f"{msg}\n".encode())
    except (KeyboardInterrupt, EOFError): sock.close()

def main():
    p = argparse.ArgumentParser(description="TCP chat")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("server"); s.add_argument("-H", "--host", default="0.0.0.0"); s.add_argument("-p", "--port", type=int, default=9999)
    c = sub.add_parser("client"); c.add_argument("-H", "--host", default="localhost"); c.add_argument("-p", "--port", type=int, default=9999)
    c.add_argument("-n", "--name", default="anon")
    args = p.parse_args()
    if args.cmd == "server": server(args.host, args.port)
    elif args.cmd == "client": client(args.host, args.port, args.name)

if __name__ == "__main__":
    main()
