import logging
import os
import uuid

from PIL import Image

from app.utils.errors import AssetGenerationError
from app.utils.image_utils import ensure_rgba

logger = logging.getLogger(__name__)


class BackgroundRemovalService:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        logger.info("BackgroundRemovalService initialized")

    def remove_background(self, input_path, output_dir=None):
        logger.info("Removing background — input=%s, output_dir=%s", input_path, output_dir)

        session = self.model_manager.load_model('rembg_isnet')
        if session is None:
            logger.error("Background removal model not loaded")
            raise AssetGenerationError("Background removal model not loaded")
        logger.info("Background removal model loaded")

        image = Image.open(input_path)
        image = ensure_rgba(image)
        logger.info("Input image opened — mode=%s, size=%s", image.mode, image.size)

        try:
            from rembg import remove
            logger.info("Running rembg inference")
            output = remove(image, session=session)
            output = ensure_rgba(output)
            logger.info("Background removal complete — output size=%s", output.size)
        except Exception as e:
            logger.exception("Background removal failed for %s", input_path)
            raise AssetGenerationError(f"Background removal failed: {e}")

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            name = f'no_bg_{uuid.uuid4().hex[:8]}.png'
            out_path = os.path.join(output_dir, name)
            output.save(out_path, 'PNG')
            logger.info("Saved background-free image to %s", out_path)
            return out_path, output

        logger.info("No output_dir provided, returning in-memory result only")
        return None, output

    def batch_remove(self, input_paths, output_dir):
        logger.info("Batch background removal — count=%d, output_dir=%s", len(input_paths), output_dir)
        results = []
        for idx, path in enumerate(input_paths):
            logger.info("Batch item %d/%d: %s", idx + 1, len(input_paths), path)
            out_path, _ = self.remove_background(path, output_dir)
            results.append(out_path)
        logger.info("Batch background removal complete — %d result(s)", len(results))
        return results
