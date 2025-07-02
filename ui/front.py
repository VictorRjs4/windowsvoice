# windowsvoice/ui/front.py
# ------------------------
#
# Ventana PyQt5 + burbuja flotante.
# Arranca un AssistantService construido con windowsvoice.main.build().
#

from __future__ import annotations

import sys
import threading
import queue
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QDesktopWidget
)
from PyQt5.QtGui import QMovie, QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QObject

# ── RUTAS DE RECURSOS ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # …/windowsvoice
IMG_DIR = BASE_DIR / "imagenes"
GIF_PATH = IMG_DIR / "chromegif.gif"
MIC_PATH = IMG_DIR / "mic.png"

# Asegura que el paquete principal (windowsvoice) esté en sys.path
sys.path.insert(0, str(BASE_DIR.parent))

# ── BACKEND: factory para AssistantService ─────────────────────────
from main import build  
assistant_factory = build

# ── PUENTE DE SEÑALES ──────────────────────────────────────────────
class Bridge(QObject):
    speak = pyqtSignal(str)
    stopped = pyqtSignal()

# ── BURBUJA FLOTANTE ────────────────────────────────────────────────
class Bubble(QWidget):
    def __init__(self, on_restore) -> None:
        super().__init__(flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.on_restore = on_restore
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(240, 80)

        cont = QWidget(self, objectName="bg")
        cont.setStyleSheet("QWidget#bg{background:#1a237e;border-radius:18px;}")
        cont.setGeometry(0, 0, self.width(), self.height())

        lay = QHBoxLayout(cont)
        lay.setContentsMargins(14, 0, 6, 0)
        lay.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(QIcon(str(MIC_PATH)).pixmap(30, 30))
        lay.addWidget(icon)

        self.txt = QLabel("Inactivo")
        self.txt.setFont(QFont("Arial", 15, QFont.Bold))
        self.txt.setStyleSheet("color:#00e5ff;")
        lay.addWidget(self.txt)

        lay.addStretch()

        close = QPushButton("✕")
        close.setFixedSize(24, 24)
        close.setStyleSheet(
            "QPushButton{background:#d32f2f;color:white;border:none;border-radius:12px;}"
            "QPushButton:hover{background:#b71c1c;}"
        )
        close.clicked.connect(self._close_clicked)
        lay.addWidget(close)

        scr = QDesktopWidget().availableGeometry()
        self.move(
            scr.right() - self.width() - 24,
            scr.bottom() - self.height() - 24
        )

    def set_listening(self, on: bool) -> None:
        self.txt.setText("Escuchando…" if on else "Inactivo")

    def mousePressEvent(self, _):
        self._close_clicked()

    def _close_clicked(self):
        self.hide()
        self.on_restore()

# ── VENTANA PRINCIPAL ───────────────────────────────────────────────
class MainGUI(QMainWindow):
    def __init__(self, db_config: dict) -> None:
        super().__init__()
        self.db_config = db_config

        self.bridge = Bridge()
        self.bridge.speak.connect(self._set_status)
        self.bridge.stopped.connect(self._assistant_stopped)

        self.assistant = None
        self.assistant_thread = None
        self.cmd_queue = queue.Queue()

        self.bubble = Bubble(on_restore=self._restore_window)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Leya – IA Asistente")
        self.setWindowIcon(QIcon(str(MIC_PATH)))
        self.setFixedSize(1280, 720)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        central = QWidget(self)
        self.setCentralWidget(central)
        v = QVBoxLayout(central)
        v.setAlignment(Qt.AlignCenter)

        gif_lbl = QLabel(alignment=Qt.AlignCenter)
        if GIF_PATH.exists():
            movie = QMovie(str(GIF_PATH))
            gif_lbl.setMovie(movie)
            movie.start()
        v.addWidget(gif_lbl)

        self.status = QLabel("Status : Stand-by", alignment=Qt.AlignCenter)
        self.status.setFont(QFont("Arial", 16, QFont.Bold))
        self.status.setStyleSheet("color:#00e5ff;")
        v.addWidget(self.status)

        self.btn = QPushButton("ACTIVAR ASISTENTE")
        self.btn.setFont(QFont("Arial", 14))
        self.btn.setFixedSize(240, 46)
        self.btn.setStyleSheet(
            "QPushButton{background:#1a237e;color:white;border-radius:8px;}"
            "QPushButton:hover{background:#283593;}"
        )
        self.btn.clicked.connect(self._toggle_assistant)
        v.addWidget(self.btn)

    def _toggle_assistant(self) -> None:
        # Si el hilo ya está vivo, mandamos comandos para que se detenga
        if self.assistant_thread and self.assistant_thread.is_alive():
            self.cmd_queue.put("surge")
            self.cmd_queue.put("apagar sistema")
            self.btn.setEnabled(False)
            self._set_status("Status : Deteniendo…")
            return

        # Si no está vivo, arrancamos el asistente
        self._set_status("Status : Activando…")
        self.btn.setText("DETENER ASISTENTE")
        self.bubble.set_listening(True)

        # Construimos el asistente con los métodos GUI
        self.assistant = self._wrap_assistant()

        # Iniciamos el hilo usando nuestro envoltorio
        self.assistant_thread = threading.Thread(
            target=self._run_assistant_thread, daemon=True
        )
        self.assistant_thread.start()

    def _wrap_assistant(self):
        # Ahora pasamos db_config a assistant_factory para que lo use dentro de AssistantService
        svc = assistant_factory(db_config=self.db_config)
        q, bridge = self.cmd_queue, self.bridge

        orig_listen = svc.voice_in.listen
        orig_speak = svc.voice_out.speak

        def gui_listen(timeout=5):
            try:
                return q.get_nowait()
            except queue.Empty:
                return orig_listen(timeout)

        def gui_speak(txt: str):
            orig_speak(txt)
            bridge.speak.emit(txt)

        svc.voice_in.listen = gui_listen  # type: ignore
        svc.voice_out.speak = gui_speak   # type: ignore
        return svc

    def _run_assistant_thread(self):
        try:
            # Este es el bucle principal (bloqueante) del asistente
            self.assistant.run()
        finally:
            # Cuando finalice (por comando de apagado o error), emitimos la señal stopped
            self.bridge.stopped.emit()

    def _set_status(self, txt: str) -> None:
        self.status.setText(txt)

    def _assistant_stopped(self) -> None:
        # Este slot se ejecuta cuando bridge.stopped.emit() es llamado
        self.btn.setEnabled(True)
        self.btn.setText("ACTIVAR ASISTENTE")
        self._set_status("Status : Offline")
        self.bubble.set_listening(False)

    def changeEvent(self, e) -> None:
        if e.type() == QEvent.WindowStateChange:
            if self.isMinimized() and self.assistant_thread and self.assistant_thread.is_alive():
                self.hide()
                self.bubble.show()
            else:
                self.bubble.hide()
        super().changeEvent(e)

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

# ── ENTRY-POINT ────────────────────────────────────────────────────
def main() -> None:
    app = QApplication(sys.argv)
    win = MainGUI(db_config=None)  # ← POINTER: En general esta llamada se hará desde ui/main.py
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
