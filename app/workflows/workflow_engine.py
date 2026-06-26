import os
import json
import logging
import traceback

from app.services.generation_service import GenerationService
from app.services.background_service import BackgroundRemovalService
from app.services.extraction_service import SpriteExtractionService
from app.services.metadata_service import MetadataService
from app.services.texture_service import TextureService
from app.services.animation_service import AnimationService
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self, session, model_manager):
        self.session = session
        self.model_manager = model_manager
        self.generation = GenerationService(session, model_manager)
        self.bg_removal = BackgroundRemovalService(model_manager)
        self.extraction = SpriteExtractionService()
        self.metadata = MetadataService(session)
        self.texture = TextureService()
        self.animation = AnimationService(model_manager)
        self.export_service = ExportService(session)
        self._checkpoint = {}

    def run_pipeline(self, project, prompt, asset_type, style_profile=None,
                     quantity=1, enable_animation=False, progress_callback=None):
        def report(step, pct, msg=''):
            if progress_callback:
                progress_callback(step, pct, msg)

        try:
            logger.info('Pipeline started — project=%s, prompt=%s, asset_type=%s, quantity=%d, animation=%s',
                        project.project_id, prompt, asset_type, quantity, enable_animation)

            report('generation', 10, f'Generating {quantity} asset(s)...')
            self.model_manager.unload_all()
            logger.info('Generation step starting...')
            assets = self.generation.generate_asset(
                project, prompt, asset_type, style_profile, quantity
            )
            self._checkpoint['assets'] = [a.asset_id for a in assets]
            logger.info('Generation step complete — %d asset(s) generated', len(assets))

            report('background_removal', 30, 'Removing backgrounds...')
            self.model_manager.unload_all()
            logger.info('Background removal step starting...')
            for i, asset in enumerate(assets):
                out_dir = os.path.dirname(asset.file_path)
                self.bg_removal.remove_background(asset.file_path, out_dir)
                logger.info('BG removal complete for asset %s (%d/%d)', asset.asset_id, i + 1, len(assets))
                report('background_removal', 30 + (20 / len(assets)) * (i + 1), '')
            logger.info('Background removal step complete')

            report('metadata', 55, 'Generating metadata...')
            logger.info('Metadata generation step starting...')
            for i, asset in enumerate(assets):
                meta = self.metadata.generate_metadata(
                    asset.asset_id, project.project_id, asset.name,
                    asset.asset_type
                )
                meta_path = os.path.join(os.path.dirname(asset.file_path), f'{asset.name}_pipeline.json')
                self.metadata.save_metadata(meta, meta_path)
                logger.info('Metadata saved for asset %s (%d/%d)', asset.asset_id, i + 1, len(assets))
            logger.info('Metadata generation step complete')

            if enable_animation:
                report('animation', 70, 'Generating animations...')
                self.model_manager.unload_all()
                logger.info('Animation generation step starting...')
                for i, asset in enumerate(assets):
                    anim_dir = os.path.join(project.output_directory, project.project_id, 'animations')
                    self.animation.generate_animation(
                        asset.file_path, anim_dir, 'idle'
                    )
                    logger.info('Animation generated for asset %s (%d/%d)', asset.asset_id, i + 1, len(assets))
                logger.info('Animation generation step complete')

            report('export', 90, 'Exporting...')
            logger.info('Export step starting...')
            export_dir = os.path.join(project.output_directory, project.project_id, 'exports', 'pipeline_export')
            self.export_service.export_project(project, export_dir)
            logger.info('Export step complete — path=%s', export_dir)

            report('complete', 100, 'Pipeline complete!')
            logger.info('Pipeline completed successfully')
            return {'success': True, 'assets': assets, 'export_path': export_dir}

        except Exception as e:
            logger.error('Pipeline failed: %s', e, exc_info=True)
            logger.error('Failure traceback:\n%s', traceback.format_exc())
            report('error', 0, f'Failed: {e}')
            return {'success': False, 'error': str(e), 'checkpoint': self._checkpoint}
