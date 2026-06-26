import logging

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.ui.dashboard_screen import DashboardScreen

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.setWindowTitle("AI Game Asset Factory")
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #252526; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(4)

        title = QLabel("AI Game Asset Factory")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #4a9eff; padding: 8px 4px;")
        sidebar_layout.addWidget(title)

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "Dashboard"),
            ("generation", "Generate Assets"),
            ("review", "Review Assets"),
            ("animation", "Animations"),
            ("export", "Export"),
        ]
        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; color: #ccc; border: none; padding: 8px 12px; text-align: left; font-size: 13px; }
                QPushButton:hover { background-color: #333; color: #fff; }
                QPushButton:pressed { background-color: #3a3a3a; }
            """)
            btn.clicked.connect(lambda checked, k=key: self.navigate_to(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        sidebar_layout.addStretch()

        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        sidebar_layout.addWidget(version)

        layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.screens = {}
        self.register_screen("dashboard", DashboardScreen(self))

        self.navigate_to("dashboard")

    def register_screen(self, name, widget):
        self.screens[name] = widget
        self.stack.addWidget(widget)
        logger.info("Registered screen: %s (%s)", name, widget.__class__.__name__)

    def navigate_to(self, name):
        if name in self.screens:
            self.stack.setCurrentWidget(self.screens[name])
            logger.info("Navigated to screen: %s", name)
            for key, btn in self.nav_buttons.items():
                btn.setStyleSheet("""
                    QPushButton { background-color: transparent; color: #ccc; border: none; padding: 8px 12px; text-align: left; font-size: 13px; }
                    QPushButton:hover { background-color: #333; color: #fff; }
                """ if key != name else """
                    QPushButton { background-color: #3a3a3a; color: #fff; border: none; border-left: 3px solid #4a9eff; padding: 8px 12px; text-align: left; font-size: 13px; }
                """)
