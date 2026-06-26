import logging
from PIL import Image
import numpy as np
import cv2

logger = logging.getLogger(__name__)


def ensure_rgba(image: Image.Image) -> Image.Image:
    if image.mode != 'RGBA':
        logger.info("Converting image from mode '%s' to 'RGBA'", image.mode)
        try:
            image = image.convert('RGBA')
        except Exception:
            logger.exception("Failed to convert image to RGBA")
            raise
    return image


def pil_to_cv2(image: Image.Image) -> np.ndarray:
    logger.info("Converting PIL image (mode=%s, size=%s) to OpenCV BGR array", image.mode, image.size)
    try:
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception:
        logger.exception("PIL to OpenCV conversion failed")
        raise


def cv2_to_pil(image: np.ndarray) -> Image.Image:
    logger.info("Converting OpenCV array (shape=%s, dtype=%s) to PIL image", image.shape, image.dtype)
    try:
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    except Exception:
        logger.exception("OpenCV to PIL conversion failed")
        raise


def make_thumbnail(image: Image.Image, size=(128, 128)) -> Image.Image:
    logger.info("Creating thumbnail of size %s from image (mode=%s, size=%s)", size, image.mode, image.size)
    try:
        thumb = image.copy()
        thumb.thumbnail(size, Image.LANCZOS)
        logger.debug("Thumbnail created: new size=%s", thumb.size)
        return thumb
    except Exception:
        logger.exception("Thumbnail creation failed")
        raise
