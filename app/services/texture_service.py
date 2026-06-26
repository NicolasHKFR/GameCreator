import logging
import os
import uuid

import cv2
import numpy as np
from PIL import Image

from app.utils.image_utils import pil_to_cv2, cv2_to_pil
from app.utils.errors import AssetGenerationError

logger = logging.getLogger(__name__)


class TextureService:
    def __init__(self):
        logger.info("TextureService initialized")

    def make_seamless(self, image_path, output_dir=None):
        logger.info("Making texture seamless — input=%s, output_dir=%s", image_path, output_dir)

        pil_image = Image.open(image_path).convert('RGB')
        cv_image = pil_to_cv2(pil_image)
        h, w = cv_image.shape[:2]
        logger.info("Input image — size=(%d,%d)", w, h)

        offset_x = w // 2
        offset_y = h // 2

        rolled = np.roll(cv_image, shift=offset_y, axis=0)
        rolled = np.roll(rolled, shift=offset_x, axis=1)

        mask = np.zeros((h, w), dtype=np.uint8)
        seam_width = min(w, h) // 8
        mask[seam_width:-seam_width, seam_width:-seam_width] = 255

        result = cv2.inpaint(rolled, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        result = np.roll(result, shift=-offset_y, axis=0)
        result = np.roll(result, shift=-offset_x, axis=1)

        seamless = cv2_to_pil(result)
        logger.info("Seamless texture generated — size=%s", seamless.size)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            name = f'tile_{uuid.uuid4().hex[:8]}.png'
            out_path = os.path.join(output_dir, name)
            seamless.save(out_path, 'PNG')
            logger.info("Saved seamless texture to %s", out_path)
            return out_path, seamless

        logger.info("No output_dir provided, returning in-memory result only")
        return None, seamless

    def validate_tile(self, image_path, tolerance=15):
        logger.info("Validating tile seamlessness — input=%s, tolerance=%d", image_path, tolerance)

        pil_image = Image.open(image_path).convert('RGB')
        cv_image = pil_to_cv2(pil_image)
        h, w = cv_image.shape[:2]
        logger.info("Validation image — size=(%d,%d)", w, h)

        left_edge = cv_image[:, 0, :]
        right_edge = cv_image[:, -1, :]
        top_edge = cv_image[0, :, :]
        bottom_edge = cv_image[-1, :, :]

        h_diff = float(np.mean(np.abs(left_edge.astype(int) - right_edge.astype(int))))
        v_diff = float(np.mean(np.abs(top_edge.astype(int) - bottom_edge.astype(int))))

        passes = h_diff < tolerance and v_diff < tolerance

        logger.info(
            "Tile validation — horizontal_seam=%.3f, vertical_seam=%.3f, passes=%s",
            h_diff, v_diff, passes,
        )
        if not passes:
            logger.warning(
                "Tile validation FAILED — h_diff=%.3f (limit=%d), v_diff=%.3f (limit=%d)",
                h_diff, tolerance, v_diff, tolerance,
            )

        return {
            'horizontal_seam_score': float(h_diff),
            'vertical_seam_score': float(v_diff),
            'passes': passes,
        }
