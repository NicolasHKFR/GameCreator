import gc
import os
import logging
import threading

import torch

from app.models.model_registry import ModelRegistry
from app.utils.config import get_app_config
from app.utils.errors import ModelLoadError, GPUOutOfMemoryError

logger = logging.getLogger(__name__)

try:
    import pynvml
    pynvml.nvmlInit()
    _HAS_NVML = True
except Exception:
    logger.exception("Failed to initialize NVML — VRAM tracking disabled")
    _HAS_NVML = False


class ModelManager:
    def __init__(self):
        self.registry = ModelRegistry()
        self.config = get_app_config()
        self._loaded_model = None
        self._loaded_key = None
        self._loaded_type = None
        self._lock = threading.Lock()
        self._vram_budget = self.config.get('vram_budget_gb', 8.0)
        self._vram_warning = self.config.get('vram_warning_threshold_gb', 7.5)
        self._watchdog_stop = threading.Event()
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True, name='vram-watchdog')
        self._watchdog_thread.start()
        logger.info("ModelManager initialized with VRAM budget=%s GB, warning threshold=%s GB",
                     self._vram_budget, self._vram_warning)

    def _watchdog_loop(self):
        while not self._watchdog_stop.wait(2.0):
            try:
                used = self.get_used_vram_gb()
                if used > self._vram_warning:
                    logger.warning("VRAM watchdog: %.1f GB exceeds threshold %s GB — unloading", used, self._vram_warning)
                    self.unload_all()
            except Exception:
                logger.exception("VRAM watchdog error")

    @property
    def current_model_type(self):
        return self._loaded_type

    @property
    def current_model_key(self):
        return self._loaded_key

    def get_available_vram_gb(self):
        if not _HAS_NVML:
            return self._vram_budget
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            free_gb = info.free / (1024 ** 3)
            logger.info("Available VRAM: %.1f GB", free_gb)
            return free_gb
        except Exception:
            logger.exception("Failed to query available VRAM")
            return self._vram_budget

    def get_used_vram_gb(self):
        if not _HAS_NVML:
            return 0.0
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            used_gb = info.used / (1024 ** 3)
            logger.info("Used VRAM: %.1f GB", used_gb)
            return used_gb
        except Exception:
            logger.exception("Failed to query used VRAM")
            return 0.0

    def _unload_current(self):
        if self._loaded_model is not None:
            key = self._loaded_key
            logger.info("Unloading model '%s'", key)
            del self._loaded_model
            self._loaded_model = None
            self._loaded_key = None
            self._loaded_type = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Model '%s' unloaded and GPU cache cleared", key)

    def load_model(self, model_key):
        with self._lock:
            if self._loaded_key == model_key:
                logger.info("Model '%s' is already loaded — reusing", model_key)
                return self._loaded_model

            entry = self.registry.get_model(model_key)
            if not entry:
                logger.error("Model '%s' not found in registry", model_key)
                raise ModelLoadError(f"Model '{model_key}' not found in registry")

            model_vram = entry.get('vram_gb', 0)
            available = self.get_available_vram_gb()
            current_used = self.get_used_vram_gb()
            logger.info("Loading model '%s' (requires %.1f GB VRAM, available: %.1f GB, used: %.1f GB)",
                         model_key, model_vram, available, current_used)

            if available < model_vram and current_used > 0:
                logger.warning("Insufficient VRAM — unloading current model to free memory")
                self._unload_current()
                torch.cuda.empty_cache()
                available = self.get_available_vram_gb()

            if available < model_vram:
                logger.error("OOM: need %.1f GB but only %.1f GB available", model_vram, available)
                raise GPUOutOfMemoryError(
                    f"Need {model_vram} GB VRAM but only {available:.1f} GB available"
                )

            self._unload_current()

            model_type = entry['type']
            hf_id = entry['hf_model_id']
            model_path = entry.get('path', '')

            if model_type == 'generation':
                if model_path and os.path.isdir(model_path):
                    source = model_path
                    logger.info("Loading generation model '%s' from local path: %s", model_key, source)
                else:
                    source = hf_id
                    logger.info("Loading generation model '%s' from HuggingFace: %s", model_key, source)
            else:
                source = hf_id
                logger.info("Loading %s model '%s' from %s", model_type, model_key, source)

            try:
                if model_type == 'generation':
                    from diffusers import StableDiffusionPipeline
                    self._loaded_model = StableDiffusionPipeline.from_pretrained(
                        source, torch_dtype=torch.float16, safety_checker=None
                    ).to('cuda')
                elif model_type == 'background_removal':
                    from rembg import new_session
                    self._loaded_model = new_session(model_name='isnet-general-use')
                elif model_type == 'classification':
                    from transformers import CLIPProcessor, CLIPModel
                    self._loaded_model = {
                        'model': CLIPModel.from_pretrained(hf_id).to('cuda'),
                        'processor': CLIPProcessor.from_pretrained(hf_id),
                    }
                else:
                    raise ModelLoadError(f"Unknown model type: {model_type}")

                self._loaded_key = model_key
                self._loaded_type = model_type
                logger.info("Successfully loaded model '%s' (%s)", model_key, model_type)

            except Exception as e:
                logger.exception("Failed to load model '%s'", model_key)
                raise ModelLoadError(f"Failed to load {model_key}: {e}")

            return self._loaded_model

    def unload_all(self):
        with self._lock:
            logger.info("Unloading all models")
            self._unload_current()

    def check_vram_safe(self):
        used = self.get_used_vram_gb()
        if used > self._vram_warning:
            logger.warning("VRAM usage at %.1f GB (threshold: %s GB)", used, self._vram_warning)
            return False, f"VRAM usage at {used:.1f} GB (threshold: {self._vram_warning} GB)"
        logger.info("VRAM usage: %.1f GB (safe)", used)
        return True, f"VRAM usage: {used:.1f} GB"

    def cleanup(self):
        logger.info("Starting cleanup")
        self.unload_all()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        logger.info("Cleanup complete")
