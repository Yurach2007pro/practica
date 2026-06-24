import socket
import threading

HOST = "0.0.0.0"  # слушать все интерфейсы
PORT = 5000
clients = []
clients_lock = threading.Lock()

def broadcast(message, sender_socket=None):
    with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    client.sendall(message)
                except Exception:
                    remove_client(client)

def remove_client(client_socket):
    with clients_lock:
        if client_socket in clients:
            clients.remove(client_socket)
    client_socket.close()

def handle_client(client_socket, address):
    print(f"[+] Клиент подключён: {address}")
    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            broadcast(data, sender_socket=client_socket)
    finally:
        remove_client(client_socket)
        print(f"[-] Клиент отключён: {address}")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[*] Сервер запущен на порту {PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        with clients_lock:
            clients.append(client_socket)
        thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        thread.start()

if __name__ == "__main__":
    main()
