import json
import os
import logging

logger = logging.getLogger(__name__)

_APP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'app_config.json')
_MODEL_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'model_registry.json')

_app_config = None
_model_registry = None


def _load_json(path):
    logger.info("Loading JSON config from: %s", path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.debug("Config contents from %s: %s", path, json.dumps(data, indent=2, default=str))
    return data


def get_app_config():
    global _app_config
    if _app_config is None:
        logger.info("Loading app config from: %s", _APP_CONFIG_PATH)
        _app_config = _load_json(_APP_CONFIG_PATH)
        if not isinstance(_app_config, dict):
            logger.warning("App config is not a dict, got %s", type(_app_config).__name__)
    return _app_config


def get_model_registry():
    global _model_registry
    if _model_registry is None:
        logger.info("Loading model registry from: %s", _MODEL_REGISTRY_PATH)
        _model_registry = _load_json(_MODEL_REGISTRY_PATH)
        if not isinstance(_model_registry, dict):
            logger.warning("Model registry is not a dict, got %s", type(_model_registry).__name__)
    return _model_registry


def resolve_path(relative_path):
    result = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', relative_path))
    logger.debug("Resolved relative path '%s' to: %s", relative_path, result)
    return result
