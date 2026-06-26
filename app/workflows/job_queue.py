import threading
import uuid
import logging
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class Job:
    def __init__(self, name, func, *args, **kwargs):
        self.job_id = str(uuid.uuid4())
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = JobStatus.PENDING
        self.result = None
        self.error = None
        self.progress = 0.0
        self.progress_message = ''
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None


class JobQueue:
    def __init__(self, max_concurrent=1):
        self.max_concurrent = max_concurrent
        self._queue = []
        self._running = []
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._listeners = []
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def add_listener(self, callback):
        self._listeners.append(callback)

    def _notify(self, job):
        for cb in self._listeners:
            try:
                cb(job)
            except Exception:
                pass

    def enqueue(self, name, func, *args, **kwargs):
        job = Job(name, func, *args, **kwargs)
        with self._lock:
            self._queue.append(job)
            queue_size = len(self._queue)
            running_size = len(self._running)
        logger.info('Job enqueued — id=%s, name=%s, queue_size=%d, running=%d',
                    job.job_id, name, queue_size, running_size)
        self._event.set()
        return job

    def _worker_loop(self):
        while True:
            self._event.wait()
            self._event.clear()

            job = None
            with self._lock:
                if self._queue:
                    job = self._queue.pop(0)
                    self._running.append(job)

            if job:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()
                logger.info('Job started — id=%s, name=%s', job.job_id, job.name)
                self._notify(job)
                try:
                    job.result = job.func(*job.args, **job.kwargs)
                    job.status = JobStatus.COMPLETED
                    logger.info('Job completed — id=%s, name=%s', job.job_id, job.name)
                except Exception as e:
                    job.error = str(e)
                    job.status = JobStatus.FAILED
                    logger.exception('Job failed — id=%s, name=%s, error=%s', job.job_id, job.name, e)
                job.completed_at = datetime.utcnow()
                self._notify(job)

                with self._lock:
                    if job in self._running:
                        self._running.remove(job)
                        logger.debug('Job removed from running — id=%s, pending=%d', job.job_id, len(self._queue))

            if self._queue:
                self._event.set()

    def cancel(self, job_id):
        with self._lock:
            for job in self._queue:
                if job.job_id == job_id:
                    job.status = JobStatus.CANCELLED
                    self._queue.remove(job)
                    logger.warning('Job cancelled — id=%s, name=%s', job.job_id, job.name)
                    self._notify(job)
                    return True
        logger.warning('Cancel requested but job not found — id=%s', job_id)
        return False

    def get_status(self):
        with self._lock:
            return {
                'queue': [{'id': j.job_id, 'name': j.name, 'status': j.status.value} for j in self._queue],
                'running': [{'id': j.job_id, 'name': j.name, 'status': j.status.value} for j in self._running],
            }
