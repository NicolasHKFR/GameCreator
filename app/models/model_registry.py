import logging

from app.utils.config import get_model_registry, resolve_path

logger = logging.getLogger(__name__)


class ModelRegistry:
    def __init__(self):
        self.registry = get_model_registry()
        logger.info("ModelRegistry initialized with %d entries", len(self.registry))

    def get_active_models(self):
        active = {k: v for k, v in self.registry.items() if v.get('active', False)}
        logger.info("Active models: %d of %d registered", len(active), len(self.registry))
        return active

    def get_model(self, model_key):
        entry = self.registry.get(model_key)
        if not entry:
            logger.warning("Model '%s' not found in registry", model_key)
        return entry

    def get_by_type(self, model_type):
        result = {k: v for k, v in self.registry.items()
                  if v.get('type') == model_type and v.get('active', False)}
        logger.info("Models of type '%s': %d found", model_type, len(result))
        return result

    def resolve_model_path(self, model_key):
        entry = self.registry.get(model_key)
        if not entry:
            logger.warning("Cannot resolve path — model '%s' not found in registry", model_key)
            return None
        resolved = resolve_path(entry['path'])
        logger.info("Resolved path for '%s': %s", model_key, resolved)
        return resolved

    def validate(self):
        issues = []
        for key, entry in self.registry.items():
            if not entry.get('hf_model_id'):
                issues.append(f"{key}: missing hf_model_id")
            if not entry.get('type'):
                issues.append(f"{key}: missing type")
            if not entry.get('vram_gb'):
                issues.append(f"{key}: missing vram_gb")
        if issues:
            for issue in issues:
                logger.warning("Validation issue: %s", issue)
        else:
            logger.info("Registry validation passed — all entries complete")
        return issues
