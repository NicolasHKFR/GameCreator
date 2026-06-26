import logging

import torch
from PIL import Image

from app.utils.errors import AssetGenerationError

logger = logging.getLogger(__name__)

GAME_ASSET_CATEGORIES = [
    'tree', 'rock', 'sword', 'shield', 'house', 'character',
    'building', 'grass', 'water', 'wall', 'chest', 'door',
    'helmet', 'bow', 'potion', 'coin', 'key', 'torch',
    'environment', 'prop', 'weapon', 'background', 'effect',
]


class ClassificationService:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        logger.info("ClassificationService initialized")

    def classify_asset(self, image_path):
        logger.info("Classifying asset — input=%s", image_path)

        loaded = self.model_manager.load_model('clip_vit_large')
        if loaded is None:
            logger.error("Classification model (clip_vit_large) not loaded")
            raise AssetGenerationError("Classification model not loaded")
        logger.info("Classification model loaded")

        model = loaded['model']
        processor = loaded['processor']

        image = Image.open(image_path).convert('RGB')
        logger.info("Input image opened — size=%s, mode=%s", image.size, image.mode)

        inputs = processor(
            text=GAME_ASSET_CATEGORIES,
            images=image,
            return_tensors='pt',
            padding=True,
        ).to('cuda')

        logger.info("Running CLIP inference — %d categories", len(GAME_ASSET_CATEGORIES))
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        best_idx = int(probs.argmax())
        confidence = float(probs[best_idx])
        classification = GAME_ASSET_CATEGORIES[best_idx]

        logger.info(
            "Classification result — category=%s, confidence=%.4f",
            classification, confidence,
        )
        if confidence < 0.5:
            logger.warning(
                "Low confidence classification — category=%s, confidence=%.4f",
                classification, confidence,
            )

        return {
            'classification': classification,
            'confidence': confidence,
            'all_probs': {cat: float(probs[i]) for i, cat in enumerate(GAME_ASSET_CATEGORIES)},
        }
