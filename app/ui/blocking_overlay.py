import logging

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer

logger = logging.getLogger(__name__)


class BlockingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Working...")
        self.label.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold; background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setMaximumWidth(300)
        self.progress.setStyleSheet("""
            QProgressBar { background-color: #444; border: none; border-radius: 4px; height: 8px; }
            QProgressBar::chunk { background-color: #4a9eff; border-radius: 4px; }
        """)
        layout.addWidget(self.progress, 0, Qt.AlignCenter)

        self._parent = parent
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_show)

    def show_overlay(self, message="Working..."):
        self.label.setText(message)
        if self._parent:
            self.setGeometry(self._parent.rect())
            self.show()
            self.raise_()
        self._timer.stop()

    def show_delayed(self, message="Working...", delay_ms=300):
        self.label.setText(message)
        self._timer.start(delay_ms)

    def _do_show(self):
        if self._parent:
            self.setGeometry(self._parent.rect())
            self.show()
            self.raise_()

    def hide_overlay(self):
        self._timer.stop()
        self.hide()
