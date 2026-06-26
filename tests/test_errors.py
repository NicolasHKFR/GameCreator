from app.utils.errors import (
    AppError, ModelLoadError, GPUOutOfMemoryError,
    AssetGenerationError, AnimationError, ExportError,
)


def test_app_error_basic():
    err = AppError("APP-000", "test error")
    assert err.error_code == "APP-000"
    assert err.message == "test error"
    assert err.recovery_action is None


def test_app_error_with_recovery():
    err = AppError("APP-000", "test error", recovery_action="restart")
    assert err.recovery_action == "restart"


def test_app_error_to_dict():
    err = AppError("APP-000", "test", recovery_action="reboot")
    d = err.to_dict()
    assert d['error_code'] == "APP-000"
    assert d['message'] == "test"
    assert d['recovery_action'] == "reboot"


def test_model_load_error():
    err = ModelLoadError("model not found")
    assert err.error_code == "APP-001"
    assert "model not found" in str(err)


def test_gpu_oom_error():
    err = GPUOutOfMemoryError("GPU OOM")
    assert err.error_code == "APP-002"


def test_asset_generation_error():
    err = AssetGenerationError("gen failed")
    assert err.error_code == "APP-003"


def test_animation_error():
    err = AnimationError("anim failed")
    assert err.error_code == "APP-004"


def test_export_error():
    err = ExportError("export failed")
    assert err.error_code == "APP-005"


def test_error_inheritance():
    assert issubclass(ModelLoadError, AppError)
    assert issubclass(GPUOutOfMemoryError, AppError)
    assert issubclass(AssetGenerationError, AppError)
    assert issubclass(AnimationError, AppError)
    assert issubclass(ExportError, AppError)
