import os
import json
import tempfile
from pathlib import Path

from app.utils.config import get_app_config, get_model_registry, resolve_path


def test_get_app_config_defaults():
    config = get_app_config()
    assert config.get('projects_directory') == 'projects'
    assert config.get('log_level') == 'INFO'
    assert config.get('vram_budget_gb') == 8.0


def test_get_model_registry():
    registry = get_model_registry()
    assert len(registry) >= 3
    assert 'sd15' in registry
    assert 'rembg_isnet' in registry
    assert 'clip_vit_large' in registry


def test_resolve_path_absolute():
    result = resolve_path('C:\\test')
    assert result == 'C:\\test'


def test_resolve_path_relative():
    result = resolve_path('test_folder')
    assert result == os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_folder'))
