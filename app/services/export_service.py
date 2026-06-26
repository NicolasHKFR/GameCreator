import json
import logging
import os
import shutil
from datetime import datetime

from app.storage.asset_repo import AssetRepo, AnimationRepo
from app.utils.errors import ExportError

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(self, session):
        self.session = session
        self.asset_repo = AssetRepo(session)
        self.animation_repo = AnimationRepo(session)
        logger.info("ExportService initialized")

    def export_project(self, project, destination):
        logger.info("Exporting project — project=%s, destination=%s", project.project_id, destination)
        os.makedirs(destination, exist_ok=True)

        structure = {
            'Characters': 'character',
            'Props': 'prop',
            'Weapons': 'weapon',
            'Buildings': 'building',
            'Tiles': 'tile',
            'Backgrounds': 'background',
            'Animations': None,
            'Metadata': None,
        }

        assets = self.asset_repo.get_by_project(project.project_id)
        animations = self.animation_repo.get_by_project(project.project_id)
        logger.info("Export data — %d asset(s), %d animation(s)", len(assets), len(animations))

        manifest = {
            'project_name': project.name,
            'project_id': project.project_id,
            'exported_at': datetime.utcnow().isoformat(),
            'asset_count': len(assets),
            'animation_count': len(animations),
            'assets': [],
            'animations': [],
        }

        for folder, asset_filter in structure.items():
            folder_path = os.path.join(destination, folder)
            os.makedirs(folder_path, exist_ok=True)

            if folder == 'Animations':
                for anim in animations:
                    anim_dir = os.path.join(folder_path, f'{anim.animation_type}_{anim.animation_id}')
                    if os.path.exists(anim.file_path):
                        shutil.copytree(anim.file_path, anim_dir, dirs_exist_ok=True)
                        logger.info("Copied animation directory: %s -> %s", anim.file_path, anim_dir)
                    manifest['animations'].append({
                        'animation_id': anim.animation_id,
                        'asset_id': anim.asset_id,
                        'type': anim.animation_type,
                        'fps': anim.fps,
                        'frames': anim.frame_count,
                    })
                continue

            if folder == 'Metadata':
                for asset in assets:
                    if asset.metadata_path and os.path.exists(asset.metadata_path):
                        meta_dest = os.path.join(folder_path, f'{asset.name}.json')
                        shutil.copy2(asset.metadata_path, meta_dest)
                        logger.info("Copied metadata: %s -> %s", asset.metadata_path, meta_dest)
                        manifest['assets'].append({
                            'asset_id': asset.asset_id,
                            'name': asset.name,
                            'type': asset.asset_type,
                            'file': f'{folder}/{asset.name}.png',
                            'metadata': f'Metadata/{asset.name}.json',
                        })
                continue

            for asset in assets:
                if asset_filter and asset.asset_type != asset_filter:
                    continue
                if os.path.exists(asset.file_path):
                    dest = os.path.join(folder_path, os.path.basename(asset.file_path))
                    shutil.copy2(asset.file_path, dest)
                    logger.info("Copied asset: %s -> %s", asset.file_path, dest)

        manifest_path = os.path.join(destination, 'manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info("Wrote manifest to %s", manifest_path)

        logger.info("Project export complete — destination=%s", destination)
        return destination

    def export_assets(self, assets, destination):
        logger.info("Exporting assets — count=%d, destination=%s", len(assets), destination)
        os.makedirs(destination, exist_ok=True)
        exported = []
        for asset in assets:
            if os.path.exists(asset.file_path):
                dest = os.path.join(destination, os.path.basename(asset.file_path))
                shutil.copy2(asset.file_path, dest)
                exported.append(dest)
                logger.info("Copied asset: %s -> %s", asset.file_path, dest)
        logger.info("Asset export complete — %d file(s) exported", len(exported))
        return exported
