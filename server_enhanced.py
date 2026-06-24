import socket
import threading
import json
import time
from datetime import datetime, timezone

HOST = "0.0.0.0"
PORT = 5000
clients = {}  # socket -> username
clients_lock = threading.Lock()

def make_message(username, msg_type, payload):
    return json.dumps({
        "username": username,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": msg_type,
        "payload": payload
    }) + "\n"

def broadcast(message, sender_socket=None):
    with clients_lock:
        for client_socket, _ in clients.items():
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(message.encode("utf-8"))
                except Exception:
                    remove_client(client_socket)

def remove_client(client_socket):
    username = None
    with clients_lock:
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]
    if username:
        status_msg = make_message("System", "status", f"{username} отключился")
        broadcast(status_msg)
    try:
        client_socket.close()
    except Exception:
        pass

def handle_client(client_socket, address):
    username = f"User_{address[1]}"
    print(f"[+] Клиент подключён: {address}, как {username}")

    # Отправляем приветственное сообщение самому клиенту
    welcome_msg = make_message("System", "status", "Вы успешно подключены")
    try:
        client_socket.sendall(welcome_msg.encode("utf-8"))
    except Exception:
        return

    with clients_lock:
        clients[client_socket] = username

    status_msg = make_message("System", "status", f"{username} вошёл в чат")
    broadcast(status_msg, sender_socket=client_socket)

    client_socket.settimeout(60.0)  # таймаут на чтение

    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break

            text = data.decode("utf-8").strip()
            if not text:
                continue

            # Предполагаем, что клиент присылает JSON с полем "payload"
            try:
                incoming = json.loads(text)
                payload = incoming.get("payload", "")
            except json.JSONDecodeError:
                payload = text  # fallback

            msg = make_message(username, "message", payload)
            broadcast(msg, sender_socket=client_socket)
    except socket.timeout:
        print(f"[!] Таймаут клиента {address}")
    except Exception as e:
        print(f"[!] Ошибка клиента {address}: {e}")
    finally:
        remove_client(client_socket)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[*] Сервер запущен на порту {PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        thread.start()

if __name__ == "__main__":
    main()
