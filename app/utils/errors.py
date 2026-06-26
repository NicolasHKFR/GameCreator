import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, error_code, message, recovery_action=None):
        self.error_code = error_code
        self.message = message
        self.recovery_action = recovery_action
        super().__init__(self.message)
        logger.error("[%s] %s", self.error_code, self.message)

    def to_dict(self):
        return {
            'error_code': self.error_code,
            'message': self.message,
            'recovery_action': self.recovery_action,
        }


class ModelLoadError(AppError):
    def __init__(self, message="Failed to load AI model", recovery_action="Check model files and try again"):
        super().__init__('APP-001', message, recovery_action)


class GPUOutOfMemoryError(AppError):
    def __init__(self, message="GPU memory exhausted", recovery_action="Reduce batch size or use a smaller model"):
        super().__init__('APP-002', message, recovery_action)


class AssetGenerationError(AppError):
    def __init__(self, message="Asset generation failed", recovery_action="Check prompt and try again"):
        super().__init__('APP-003', message, recovery_action)


class AnimationError(AppError):
    def __init__(self, message="Animation generation failed", recovery_action="Check source asset and try again"):
        super().__init__('APP-004', message, recovery_action)


class ExportError(AppError):
    def __init__(self, message="Export failed", recovery_action="Check disk space and permissions"):
        super().__init__('APP-005', message, recovery_action)
