import socket
import threading
import json
import tkinter as tkimport ssl
from tkinter import simpledialog, scrolledtext, messagebox
from datetime import datetime, timezone

CA_CERT = "cert.pem"  # путь к сертификату сервера
SERVER_IP = "192.168.1.5"  # замените на IP сервера
SERVER_PORT = 5000

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Локальный чат")
        self.sock = None
        self.username = ""

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
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, SERVER_PORT))
            self.log("Подключено к серверу.")
            threading.Thread(target=self.receive_loop, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", str(e))
            self.root.quit()

    def send_message(self, event=None):
        text = self.message_entry.get().strip()
        if not text or not self.sock:
            return
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
        try:
            msg = json.loads(text)
            username = msg.get("username", "System")
            msg_type = msg.get("type", "message")
            payload = msg.get("payload", "")
            timestamp = msg.get("timestamp", "")

            line = f"[{timestamp}] {username}: {payload}"
            self.log(line)
        except json.JSONDecodeError:
            self.log(f"[Неизвестный формат]: {text}")

    def log(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

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
