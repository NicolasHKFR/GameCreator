import logging
import os
import uuid
from datetime import datetime

import torch
from PIL import Image

from app.utils.config import get_app_config
from app.utils.image_utils import make_thumbnail
from app.storage.asset_repo import AssetRepo
from app.services.metadata_service import MetadataService
from app.services.style_service import StyleService
from app.utils.errors import AssetGenerationError

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self, session, model_manager):
        self.session = session
        self.model_manager = model_manager
        self.asset_repo = AssetRepo(session)
        self.metadata_service = MetadataService(session)
        self.style_service = StyleService(session)
        self.config = get_app_config()
        logger.info("GenerationService initialized")

    def generate_asset(self, project, prompt, asset_type, style_profile=None, quantity=1, progress_callback=None, model_key='sd15'):
        logger.info(
            "Generating asset(s) — project=%s, prompt=%r, asset_type=%s, style_profile=%s, quantity=%d, model=%s",
            project.project_id, prompt, asset_type, style_profile.name if style_profile else None, quantity, model_key,
        )

        model = self.model_manager.load_model(model_key)
        if model is None:
            logger.error("SD model failed to load")
            raise AssetGenerationError("SD model not loaded")
        logger.info("SD model loaded successfully")

        composed = self.style_service.compose_prompt(style_profile, prompt)
        negative = self.style_service.get_negative_prompt(style_profile)
        resolution = self.config.get('default_output_resolution', 512)
        steps = self.config.get('gen_steps_default', 25)
        cfg = self.config.get('gen_cfg_default', 7.5)

        logger.info(
            "Inference params — prompt=%r, negative_prompt=%r, resolution=%d, steps=%d, cfg_scale=%.1f",
            composed, negative, resolution, steps, cfg,
        )

        seed_strategy = getattr(style_profile, 'seed_strategy', 'random') if style_profile else 'random'
        fixed_seed = 42 if seed_strategy == 'fixed' else None

        assets = []
        for i in range(quantity):
            if progress_callback:
                pct = (i / max(quantity, 1)) * 100
                progress_callback.set_progress(pct, f'Generating asset {i+1}/{quantity}')
            name = f'{asset_type}_{uuid.uuid4().hex[:8]}'
            asset_dir = os.path.join(project.output_directory, project.project_id, 'assets')
            os.makedirs(asset_dir, exist_ok=True)

            try:
                seed = fixed_seed + i if fixed_seed is not None else torch.randint(0, 2**31, (1,)).item()
                generator = torch.Generator(device='cuda').manual_seed(seed) if seed is not None else None
                logger.info("Running inference for asset %d/%d: %s (seed=%s)", i + 1, quantity, name, seed)
                result = model(
                    prompt=composed,
                    negative_prompt=negative,
                    width=resolution,
                    height=resolution,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    generator=generator,
                )
                image = result.images[0]
                logger.info("Inference complete — image size: %s", image.size)

                if image.mode != 'RGBA':
                    image = image.convert('RGBA')

                file_path = os.path.join(asset_dir, f'{name}.png')
                image.save(file_path, 'PNG')
                logger.info("Saved generated image to %s", file_path)

                thumb_path = os.path.join(asset_dir, f'{name}_thumb.png')
                make_thumbnail(image).save(thumb_path, 'PNG')
                logger.info("Saved thumbnail to %s", thumb_path)

                profile_name = style_profile.name if style_profile else ''
                meta = self.metadata_service.generate_metadata(
                    asset_id=str(uuid.uuid4()),
                    project_id=project.project_id,
                    name=name,
                    asset_type=asset_type,
                    style_profile_name=profile_name,
                )
                meta_path = os.path.join(asset_dir, f'{name}.json')
                self.metadata_service.save_metadata(meta, meta_path)
                logger.info("Saved metadata to %s — content: %s", meta_path, meta)

                asset_record = self.asset_repo.create(
                    project_id=project.project_id,
                    name=name,
                    asset_type=asset_type,
                    file_path=file_path,
                    thumbnail_path=thumb_path,
                    metadata_path=meta_path,
                )
                assets.append(asset_record)
                logger.info("Created asset record in DB — id=%s, name=%s", asset_record.asset_id, name)

            except Exception as e:
                logger.exception("Generation failed for %s", name)
                raise AssetGenerationError(f"Generation failed for {name}: {e}")

        logger.info("Asset generation complete — generated %d asset(s)", len(assets))
        return assets
