import logging
import os
import uuid

import cv2
import numpy as np
from PIL import Image

from app.utils.image_utils import pil_to_cv2, cv2_to_pil
from app.utils.errors import AssetGenerationError

logger = logging.getLogger(__name__)


class SpriteExtractionService:
    def __init__(self):
        logger.info("SpriteExtractionService initialized")

    def extract_sprites(self, image_path, output_dir, min_area=500):
        logger.info("Extracting sprites — input=%s, output_dir=%s, min_area=%d", image_path, output_dir, min_area)
        os.makedirs(output_dir, exist_ok=True)

        pil_image = Image.open(image_path).convert('RGBA')
        cv_image = pil_to_cv2(pil_image)
        logger.info("Input image loaded — size=%s, cv_shape=%s", pil_image.size, cv_image.shape)

        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logger.info("Found %d contour(s) before filtering", len(contours))

        sprites = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if area < min_area:
                logger.debug("Skipping small contour %d — area=%d < min_area=%d", i, area, min_area)
                continue

            sprite_pil = pil_image.crop((x, y, x + w, y + h))
            name = f'sprite_{uuid.uuid4().hex[:8]}'
            out_path = os.path.join(output_dir, f'{name}.png')
            sprite_pil.save(out_path, 'PNG')
            logger.info("Extracted sprite %d/%d — bbox=(%d,%d,%d,%d), area=%d, saved=%s",
                        len(sprites) + 1, len(contours), x, y, w, h, area, out_path)

            sprites.append({
                'asset_id': name,
                'name': name,
                'file_path': out_path,
                'bbox': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
            })

        logger.info("Sprite extraction complete — extracted %d sprite(s) from %d contour(s)", len(sprites), len(contours))
        return sprites

    def generate_name(self, classification, confidence, index):
        type_label = classification if confidence > 0.5 else 'unknown'
        logger.debug("Generated name — classification=%s, confidence=%.3f, index=%d => %s",
                     classification, confidence, index, f'{type_label}_{index:03d}')
        return f'{type_label}_{index:03d}'
