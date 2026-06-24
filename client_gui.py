import socket
import threading
import json
import tkinter as tkimport ssl
from tkinter import simpledialog, scrolledtext, messagebox
from datetime import datetime, timezone
from tkinter import filedialog

CA_CERT = "cert.pem"  # путь к сертификату сервера
SERVER_IP = "192.168.1.5"  # замените на IP сервера
SERVER_PORT = 5000

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Локальный чат")
        self.sock = None
        self.username = ""
        self.receiving_file = None
        self.remaining_bytes = 0

        # Поле вывода сообщений
        self.chat_area = scrolledtext.ScrolledText(root, state='disabled', wrap=tk.WORD)
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ввод сообщения
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.message_entry = tk.Entry(self.input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.send_button = tk.Button(self.input_frame, text="Отправить", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Запрос имени
        self.username = simpledialog.askstring("Имя пользователя", "Введите ваше имя:")
        if not self.username:
            self.username = "Anonymous"

        self.connect()

    def connect(self):
        try:
            base_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Создаём SSL-контекст клиента
            context = ssl.create_default_context(cafile=CA_CERT)
            self.sock = context.wrap_socket(base_sock, server_hostname=SERVER_IP)
            
            self.sock.connect((SERVER_IP, SERVER_PORT))
            self.log("Подключено к серверу (SSL).")
            threading.Thread(target=self.receive_loop, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", str(e))
            self.root.quit()


    def send_message(self, event=None):
        text = self.message_entry.get().strip()
        if not text or not self.sock:
            return

        if text.startswith("/"):
            cmd = text[1:].split(" ", 1)
            command = cmd[0].lower()
            arg = cmd[1] if len(cmd) > 1 else ""

            if command == "nick":
                if arg:
                    old = self.username
                    self.username = arg
                    self.log(f"Никнейм изменён с '{old}' на '{self.username}'")
                    # Можно отправить системное сообщение на сервер, чтобы все видели
                    status_msg = {
                        "username": "System",
                        "type": "status",
                        "payload": f"{old} сменил ник на {self.username}"
                    }
                    self.sock.sendall((json.dumps(status_msg) + "\n").encode("utf-8"))
                else:
                    self.log("Использование: /nick НовоеИмя")
                self.message_entry.delete(0, tk.END)
                return
            else:
                self.log(f"Неизвестная команда: /{command}")
                self.message_entry.delete(0, tk.END)
                return

        # Обычная отправка сообщения
        payload = {
            "username": self.username,
            "type": "message",
            "payload": text
        }
        try:
            self.sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            self.message_entry.delete(0, tk.END)
        except Exception as e:
            self.log(f"[Ошибка отправки]: {e}")
            self.disconnect()


    def receive_loop(self):
        try:
            while True:
                data = self.sock.recv(4096)
                if not data:
                    break
                text = data.decode("utf-8").strip()
                if not text:
                    continue
                self.process_incoming(text)
        except Exception as e:
            self.log(f"[Ошибка приёма]: {e}")
        finally:
            self.disconnect()

        def process_incoming(self, text):
        # Если мы в режиме приёма файла — это бинарные данные, а не JSON
        if self.receiving_file is not None:
            data_len = len(text.encode("latin1"))  # text здесь — бинарные данные как строка
            write_len = min(data_len, self.remaining_bytes)
            self.receiving_file.write(text.encode("latin1")[:write_len])
            self.remaining_bytes -= write_len

            if self.remaining_bytes <= 0:
                self.receiving_file.close()
                self.log(f"Файл сохранён: {self.current_filename}")
                self.receiving_file = None
                self.current_filename = None
            return

        # Обычный JSON
        try:
            msg = json.loads(text)
            username = msg.get("username", "System")
            msg_type = msg.get("type")
            payload = msg.get("payload", "")
            timestamp = msg.get("timestamp", "")

            if msg_type == "file_info":
                filename = msg["filename"]
                size = msg["size"]
                self.current_filename = filename
                self.receiving_file = open(filename, "wb")
                self.remaining_bytes = size
                self.log(f"[Файл] Начало приёма: {filename} ({size} байт)")
                return

            if msg_type == "file_end":
                # Дублируем проверку на случай рассинхронизации
                if self.receiving_file:
                    self.receiving_file.close()
                    self.log(f"Файл завершён: {self.current_filename}")
                    self.receiving_file = None
                    self.current_filename = None
                return

            line = f"[{timestamp}] {username}: {payload}"
            self.log(line)
        except json.JSONDecodeError:
            # Если не JSON и не в режиме файла — странная ситуация
            self.log(f"[Неизвестный формат]: {text}")


    def log(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

     def send_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        filename = path.split("/")[-1]  # упрощённо
        try:
            with open(path, "rb") as f:
                data = f.read()
            size = len(data)

            # 1. Отправляем информацию о файле
            info = {
                "username": self.username,
                "type": "file_info",
                "filename": filename,
                "size": size
            }
            self.sock.sendall((json.dumps(info) + "\n").encode("utf-8"))

            # 2. Отправляем бинарные данные
            self.sock.sendall(data)

            # 3. Отправляем маркер конца
            end_marker = {
                "username": self.username,
                "type": "file_end"
            }
            self.sock.sendall((json.dumps(end_marker) + "\n").encode("utf-8"))
            self.log(f"Файл '{filename}' отправлен.")
        except Exception as e:
            self.log(f"[Ошибка отправки файла]: {e}")

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.log("Отключено от сервера.")

    def on_close(self):
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

        self.file_button = tk.Button(self.input_frame, text="Файл", command=self.send_file)
        self.file_button.pack(side=tk.RIGHT, padx=(5, 0))

