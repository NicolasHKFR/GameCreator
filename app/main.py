import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.utils.config import get_app_config, resolve_path
from app.utils.logger import setup_logger
from app.storage.database import Database

logger = None


class Application:
    def __init__(self):
        global logger
        logger = setup_logger()
        self.config = get_app_config()

        logger.info("Starting AI Game Asset Factory")
        logger.info(f"Config: {self.config}")

        os.makedirs(resolve_path(self.config.get('projects_directory', 'projects')), exist_ok=True)
        os.makedirs(resolve_path(self.config.get('model_cache_directory', 'model_cache')), exist_ok=True)

        self.db = Database()
        logger.info("Database initialized")

    def get_db(self):
        return self.db


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AI Game Asset Factory")
    app.setOrganizationName("GameCreator")

    if get_app_config().get('theme', 'dark') == 'dark':
        app.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e1e; color: #e0e0e0; }
            QPushButton { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555; padding: 6px 16px; border-radius: 4px; }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2a2a2a; color: #e0e0e0; border: 1px solid #555; padding: 4px; border-radius: 3px;
            }
            QListWidget, QTableWidget { background-color: #2a2a2a; color: #e0e0e0; border: 1px solid #555; }
            QLabel { color: #e0e0e0; }
            QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 8px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QProgressBar { background-color: #2a2a2a; border: 1px solid #555; border-radius: 3px; text-align: center; color: #e0e0e0; }
            QProgressBar::chunk { background-color: #4a9eff; border-radius: 2px; }
            QScrollBar:vertical { background-color: #2a2a2a; width: 10px; }
            QScrollBar::handle:vertical { background-color: #555; border-radius: 5px; min-height: 20px; }
        """)

    app_instance = Application()
    logger.info("Application initialized successfully")

    from app.ui.main_window import MainWindow
    window = MainWindow(app_instance)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
