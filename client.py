import socket
import threading

SERVER_IP = "192.168.1.5"  # замените на реальный IP сервера
SERVER_PORT = 5000

def receive_messages(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("\n[Сервер отключён]")
                break
            print(data.decode("utf-8"), end="")
    except Exception as e:
        print(f"\n[Ошибка приёма]: {e}")
    finally:
        sock.close()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    print("Подключено к серверу. Введите сообщения (Ctrl+C для выхода).")

    recv_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    recv_thread.start()

    try:
        while True:
            message = input()
            sock.sendall((message + "\n").encode("utf-8"))
    except KeyboardInterrupt:
        print("\nОтключение...")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
