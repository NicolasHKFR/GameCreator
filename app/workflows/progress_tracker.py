import logging

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ProgressTracker(QObject):
    progress_updated = Signal(float, str)
    step_changed = Signal(str)
    job_completed = Signal(object)
    job_failed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = ''
        self.progress = 0.0

    def set_step(self, step_name):
        self.current_step = step_name
        logger.debug('Step changed — step=%s', step_name)
        self.step_changed.emit(step_name)

    def set_progress(self, value, message=''):
        self.progress = value
        logger.info('Progress updated — step=%s, value=%.1f%%, message=%s',
                     self.current_step, value, message)
        self.progress_updated.emit(value, message)

    def on_complete(self, result):
        logger.info('Job completed — step=%s, result=%s', self.current_step, result)
        self.set_progress(100.0, 'Complete')
        self.job_completed.emit(result)

    def on_error(self, step_name, error_message):
        logger.error('Job failed — step=%s, error=%s', step_name, error_message)
        self.job_failed.emit(step_name, error_message)
