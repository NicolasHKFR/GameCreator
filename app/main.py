import sys
import os
import logging
import warnings

warnings.filterwarnings("ignore", message="Failed to load image Python extension")
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_cublas_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.venv', 'Lib', 'site-packages', 'nvidia', 'cu13', 'bin', 'x86_64')
_cublas_path = os.path.normpath(_cublas_path)
if os.path.isdir(_cublas_path):
    os.environ['PATH'] = _cublas_path + os.pathsep + os.environ.get('PATH', '')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.utils.config import get_app_config, resolve_path
from app.utils.logger import setup_logger
from app.storage.database import Database
from app.workflows.job_queue import JobQueue

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
        self.job_queue = JobQueue(max_concurrent=1)
        self._model_manager = None
        self._sessions = []
        logger.info("Database initialized, JobQueue ready")

    def get_db(self):
        return self.db

    @property
    def model_manager(self):
        if self._model_manager is None:
            from app.models.model_manager import ModelManager
            self._model_manager = ModelManager()
            logger.info("Singleton ModelManager created")
        return self._model_manager

    def track_session(self, session):
        self._sessions.append(session)
        return session

    def close_all_sessions(self):
        for s in self._sessions:
            try:
                s.close()
            except Exception:
                pass
        self._sessions.clear()
        logger.info("All tracked sessions closed")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AI Game Asset Factory")
    app.setOrganizationName("GameCreator")

    if get_app_config().get('theme', 'dark') == 'dark':
        qss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'dark_theme.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())

    app_instance = Application()
    logger.info("Application initialized successfully")

    from app.ui.main_window import MainWindow
    window = MainWindow(app_instance)
    window.show()

    exit_code = app.exec()
    app_instance.close_all_sessions()
    if app_instance._model_manager:
        app_instance._model_manager.cleanup()
    logger.info("Application shut down")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
