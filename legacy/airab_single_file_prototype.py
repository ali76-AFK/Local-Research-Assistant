import sys
import os
import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
import keyring
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QListWidget, 
                             QTextEdit, QLineEdit, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QMessageBox,
                             QMenuBar, QDialog, QLineEdit as QLine, QLabel)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction, QPalette, QGuiApplication
import pyttsx3
import vosk
import pyaudio  # pip install pyaudio
from PIL import Image
import fitz  # PyMuPDF

# Mock LLM (replace with real llama.cpp client)
def mock_llm(prompt, files_text=""):
    return f"AI response to: {prompt[:50]}... (files: {len(files_text)} chars)"

class SpeechThread(QThread):
    text_ready = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.vosk_model = vosk.Model("vosk-model/en-us")  # Download model
        self.rec = vosk.KaldiRecognizer(self.vosk_model, 16000)

    def run(self):
        # Simplified STT loop - implement mic recording
        self.text_ready.emit("Mock speech: Hello from Vosk!")

class TTSThread(QThread):
    finished = pyqtSignal()
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'english' in voice.name.lower() and ('american' in voice.name.lower() or 'british' in voice.name.lower()):
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 150)

    def run(self):
        self.engine.say(self.text)
        self.engine.runAndWait()
        self.finished.emit()

class AIRabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIrab")
        self.setGeometry(100, 100, 1200, 800)
        self.data_dir = Path.home() / "AIrab_data"
        self.data_dir.mkdir(exist_ok=True)
        self.chats = {}  # {chat_id: messages}
        self.current_chat = "default"
        self.password = None
        self.key = None
        self.load_key_or_prompt()
        self.init_ui()
        self.load_history()
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.apply_system_theme)
        self.theme_timer.start(1000)  # Check system theme

    def load_key_or_prompt(self):
        service = "AIrab"
        self.key = keyring.get_password(service, "app_key")
        if not self.key:
            dlg = PasswordDialog()
            if dlg.exec():
                self.password = dlg.password
                self.key = Fernet.generate_key()
                keyring.set_password(service, "app_key", self.key.decode())
            else:
                sys.exit("Password required")

    def hash_filename(self, fname):
        h = hashlib.sha256((fname + str(datetime.now().timestamp())).encode()).hexdigest()[:16]
        return f"{h}.{Path(fname).suffix}"

    def init_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Sidebar
        sidebar = QWidget()
        layout = QVBoxLayout()
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.switch_chat)
        layout.addWidget(self.chat_list)
        new_btn = QPushButton("New Chat")
        new_btn.clicked.connect(self.new_chat)
        layout.addWidget(new_btn)
        clear_btn = QPushButton("Clear All Data")
        clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(clear_btn)
        sidebar.setLayout(layout)
        splitter.addWidget(sidebar)

        # Main chat
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display)
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        mic_btn = QPushButton("🎤")
        mic_btn.clicked.connect(self.start_stt)
        input_layout.addWidget(mic_btn)
        file_btn = QPushButton("📎")
        file_btn.clicked.connect(self.upload_files)
        input_layout.addWidget(file_btn)
        main_layout.addLayout(input_layout)
        main_widget.setLayout(main_layout)
        splitter.addWidget(main_widget)
        splitter.setSizes([200, 1000])

        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        data_action = QAction("Select Data Dir", self)
        data_action.triggered.connect(self.select_data_dir)
        file_menu.addAction(data_action)
        settings_menu = menubar.addMenu("Settings")
        theme_action = QAction("Custom Theme", self)
        theme_action.triggered.connect(self.custom_theme)
        settings_menu.addAction(theme_action)

    def new_chat(self):
        chat_id = str(datetime.now().isoformat())
        self.chats[chat_id] = []
        self.chat_list.addItem(chat_id[:16])
        self.current_chat = chat_id
        self.chat_display.clear()

    def switch_chat(self, item):
        self.current_chat = self.chat_list.item(self.text())
        self.update_display()

    def send_message(self):
        prompt = self.input_box.text()
        if not prompt: return
        self.chats[self.current_chat].append({"role": "user", "content": prompt, "time": datetime.now().isoformat()})
        self.chat_display.append(f"<b>You:</b> {prompt}")
        self.input_box.clear()
        self.process_llm(prompt)

    def process_llm(self, prompt):
        files_text = self.get_files_text()  # Implement file extraction
        response = mock_llm(prompt, files_text)
        self.chats[self.current_chat].append({"role": "assistant", "content": response, "time": datetime.now().isoformat()})
        self.chat_display.append(f"<b>AIrab:</b> {response}")
        TTSThread(response).start()

    def get_files_text(self):
        # Stub: Extract from up to 3 files using PyMuPDF/Pillow
        return ""  # Implement PDF/TXT/image text

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Upload Files (max 3)", filter="PDF (*.pdf);;TXT (*.txt);;Image (*.png *.jpg)")
        if len(files) > 3: 
            QMessageBox.warning(self, "Limit", "Max 3 files")
            return
        for f in files:
            hashed = self.hash_filename(f)
            Path(hashed).write_bytes(Path(f).read_bytes())  # Copy w/ hash

    def start_stt(self):
        self.speech_thread = SpeechThread()
        self.speech_thread.text_ready.connect(self.input_box.setText)
        self.speech_thread.start()

    def update_display(self):
        self.chat_display.clear()
        for msg in self.chats.get(self.current_chat, []):
            self.chat_display.append(f"<b>{msg['role'].title()}:</b> {msg['content']}")

    def search_history(self, query):
        # Simple JSON search
        results = []
        for cid, msgs in self.chats.items():
            for msg in msgs:
                if query.lower() in msg['content'].lower():
                    results.append(cid)
        return results

    def save_history(self):
        json.dump(self.chats, open(self.data_dir / "history.json", 'w'))

    def load_history(self):
        hist_file = self.data_dir / "history.json"
        if hist_file.exists():
            self.chats = json.load(open(hist_file))
            for cid in self.chats:
                self.chat_list.addItem(cid[:16])

    def clear_all(self):
        if QMessageBox.question(self, "Confirm", "Clear all?") == QMessageBox.Yes:
            self.chats.clear()
            self.chat_list.clear()
            for f in self.data_dir.glob("*"):
                f.unlink()
            self.data_dir.mkdir(exist_ok=True)

    def select_data_dir(self):
        dir = QFileDialog.getExistingDirectory(self)
        if dir: self.data_dir = Path(dir)

    def custom_theme(self):
        # QSS for light brown theme
        qss = """
        QMainWindow { background-color: #f5f5f5; color: #333; }
        QPushButton { background-color: #D2B48C; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #c19e6f; }
        QListWidget { font-family: 'Times New Roman'; }
        QTextEdit { font-family: 'Times New Roman'; border: 1px solid #ccc; border-radius: 4px; }
        """
        self.setStyleSheet(qss)

    def apply_system_theme(self):
        pal = QGuiApplication.palette()
        is_dark = pal.color(QPalette.ColorRole.Window).lightness() < 128
        # Adjust QSS for system dark/light

    def closeEvent(self, event):
        self.save_history()
        event.accept()

class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Password")
        layout = QVBoxLayout()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Password for secure key:"))
        layout.addWidget(self.password)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Logo stub: Use QIcon("airab.png") later
    window = AIRabWindow()
    window.show()
    sys.exit(app.exec())
