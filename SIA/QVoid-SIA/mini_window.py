import sys
import asyncio
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QHBoxLayout,
                             QSystemTrayIcon, QMenu, QAction, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QFont
from sia import SIA
from modules.real_stt import recognize_speech
from modules.voice_manager import tts_manager

class MiniSIAWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tts_state = 'gtts'  # Track current TTS engine
        self.setWindowTitle(f'SIA Mini ({self.tts_state})')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(400, 420)
        self.setStyleSheet('''
            QWidget { background: #23272e; color: #f8f8f2; font-family: Segoe UI, Arial, sans-serif; }
            QTextEdit, QLineEdit { background: #282c34; color: #f8f8f2; border-radius: 6px; font-size: 14px; }
            QLabel { font-size: 15px; }
            QPushButton { background: #ffffff; color: #23272e; border: none; border-radius: 6px; padding: 6px 12px; font-size: 13px; }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #cccccc; }
        ''')

        # SIA logo/avatar
        logo = QLabel()
        try:
            pixmap = QPixmap('sia_icon.png').scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        except Exception:
            logo.setText('🤖')
            logo.setFont(QFont('Segoe UI Emoji', 32))
        logo.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel('Status: Sleeping')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('font-weight: bold; font-size: 16px;')

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setStyleSheet('background: #1e2127; color: #f8f8f2; border-radius: 8px; font-size: 15px;')
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText('Type your question or command...')
        self.input_line.returnPressed.connect(self.handle_text_query)
        self.input_line.setStyleSheet('padding: 8px;')

        # Button icons only, no text labels
        self.listen_btn = QPushButton(QIcon('icons/listen.png'), '')
        self.listen_btn.setToolTip('Start Listening')
        self.listen_btn.clicked.connect(self.handle_start_listening)
        self.stop_btn = QPushButton(QIcon('icons/stop.png'), '')
        self.stop_btn.setToolTip('Stop Listening')
        self.stop_btn.clicked.connect(self.handle_stop_listening)
        self.tts_btn = QPushButton(QIcon('icons/tts.png'), '')
        self.tts_btn.setToolTip('Switch TTS')
        self.tts_btn.clicked.connect(self.handle_switch_tts)
        self.clear_btn = QPushButton(QIcon('icons/clear.png'), '')
        self.clear_btn.setToolTip('Clear Chat')
        self.clear_btn.clicked.connect(self.handle_clear)
        self.exit_btn = QPushButton(QIcon('icons/exit.png'), '')
        self.exit_btn.setToolTip('Exit')
        self.exit_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.listen_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.tts_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.exit_btn)
        btn_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout = QVBoxLayout()
        layout.addWidget(logo)
        layout.addWidget(self.status_label)
        layout.addWidget(self.response_area)
        layout.addWidget(self.input_line)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # SIA backend instance
        self.sia = SIA()
        self.loop = asyncio.get_event_loop()
        self.listening = False
        self.listen_thread = None
        self._stop_listen_flag = threading.Event()

        self.update_tts_title()
        self.update_button_states()

        # System tray integration
        self.tray_icon = QSystemTrayIcon(self)
        try:
            self.tray_icon.setIcon(QIcon('sia_icon.png'))
        except Exception:
            self.tray_icon.setIcon(self.style().standardIcon(QSystemTrayIcon.SP_ComputerIcon))
        self.tray_menu = QMenu()
        self.show_action = QAction('Show', self)
        self.show_action.triggered.connect(self.show_window)
        self.hide_action = QAction('Hide', self)
        self.hide_action.triggered.connect(self.hide)
        self.exit_action = QAction('Exit', self)
        self.exit_action.triggered.connect(self.exit_app)
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.hide_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def handle_text_query(self):
        query = self.input_line.text().strip()
        if query:
            self.status_label.setText('Status: Processing...')
            self.append_user_message(query)
            self.input_line.clear()
            asyncio.ensure_future(self.get_sia_response(query))
            self.auto_scroll()

    async def get_sia_response(self, query):
        try:
            await self.sia._process_input(query)
            response = self.sia.last_response or '(No response)'
        except Exception as e:
            response = f'(Error: {e})'
        self.append_sia_message(response)
        self.status_label.setText('Status: Ready')
        self.auto_scroll()

    def handle_start_listening(self):
        if self.listening:
            return
        self.status_label.setText('Status: Listening...')
        self._stop_listen_flag.clear()
        self.listening = True
        self.listen_thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.listen_thread.start()
        self.update_button_states()

    def handle_stop_listening(self):
        if not self.listening:
            return
        self.status_label.setText('Status: Stopped')
        self._stop_listen_flag.set()
        self.listening = False
        self.update_button_states()

    def listen_loop(self):
        while not self._stop_listen_flag.is_set():
            recognized = recognize_speech()
            if recognized:
                text = recognized.strip()
                self.append_user_message(text, voice=True)
                asyncio.run_coroutine_threadsafe(self.get_sia_response(text), self.loop)
                self.auto_scroll()

    def handle_switch_tts(self):
        if self.tts_state == 'gtts':
            tts_manager.switch_engine('pyttsx3')
            self.tts_state = 'pyttsx3'
            self.status_label.setText('Status: Switched to offline (pyttsx3) voice')
        else:
            tts_manager.switch_engine('gtts')
            self.tts_state = 'gtts'
            self.status_label.setText('Status: Switched to online (gTTS) voice')
        self.update_tts_title()

    def handle_clear(self):
        self.response_area.clear()
        self.status_label.setText(f'Status: Ready')

    def update_tts_title(self):
        self.setWindowTitle(f'SIA Mini ({self.tts_state})')

    def update_button_states(self):
        self.listen_btn.setEnabled(not self.listening)
        self.stop_btn.setEnabled(self.listening)

    def auto_scroll(self):
        self.response_area.moveCursor(self.response_area.textCursor().End)

    def append_user_message(self, text, voice=False):
        prefix = '🎤 You (voice):' if voice else 'You:'
        self.response_area.append(f'<span style="color:#8be9fd;font-weight:bold;">{prefix}</span> <span style="color:#f8f8f2;">{text}</span>')

    def append_sia_message(self, text):
        self.response_area.append(f'<span style="color:#bd93f9;font-weight:bold;">SIA:</span> <span style="color:#f1fa8c;">{text}</span>')

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage('SIA Mini', 'SIA is minimized to tray. Double-click the tray icon to restore.', QSystemTrayIcon.Information, 2000)

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        self._stop_listen_flag.set()
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
        QApplication.quit()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MiniSIAWindow()
    window.show()
    sys.exit(app.exec_()) 