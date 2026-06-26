import logging
import uuid
from datetime import datetime

from app.storage.database import Asset, Animation

logger = logging.getLogger(__name__)


class AssetRepo:
    def __init__(self, session):
        self.session = session

    def create(self, project_id, name, asset_type, file_path, thumbnail_path=None, metadata_path=None, tileable=False):
        try:
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                project_id=project_id,
                name=name,
                asset_type=asset_type,
                file_path=file_path,
                thumbnail_path=thumbnail_path,
                metadata_path=metadata_path,
                tileable=tileable,
            )
            self.session.add(asset)
            self.session.commit()
            logger.info("Created asset: id=%s name='%s' type='%s' project=%s", asset.asset_id, name, asset_type, project_id)
            return asset
        except Exception:
            logger.exception("Failed to create asset name='%s' project=%s", name, project_id)
            raise

    def get(self, asset_id):
        try:
            asset = self.session.query(Asset).filter_by(asset_id=asset_id).first()
            if asset:
                logger.info("Retrieved asset: id=%s name='%s'", asset_id, asset.name)
            else:
                logger.info("Asset not found: id=%s", asset_id)
            return asset
        except Exception:
            logger.exception("Failed to get asset id=%s", asset_id)
            raise

    def get_by_project(self, project_id):
        try:
            assets = self.session.query(Asset).filter_by(project_id=project_id).order_by(Asset.created_at.desc()).all()
            logger.info("Retrieved %d asset(s) for project id=%s", len(assets), project_id)
            return assets
        except Exception:
            logger.exception("Failed to get assets for project id=%s", project_id)
            raise

    def update(self, asset_id, **kwargs):
        try:
            asset = self.get(asset_id)
            if asset:
                changed = {k: v for k, v in kwargs.items() if getattr(asset, k, None) != v}
                for key, value in kwargs.items():
                    setattr(asset, key, value)
                self.session.commit()
                if changed:
                    logger.info("Updated asset id=%s name='%s': %s", asset_id, asset.name, changed)
                else:
                    logger.info("Update called for asset id=%s with no field changes", asset_id)
            else:
                logger.info("Update skipped — asset not found: id=%s", asset_id)
            return asset
        except Exception:
            logger.exception("Failed to update asset id=%s", asset_id)
            raise

    def delete(self, asset_id):
        try:
            asset = self.get(asset_id)
            if asset:
                self.session.delete(asset)
                self.session.commit()
                logger.info("Deleted asset: id=%s name='%s'", asset_id, asset.name)
            else:
                logger.info("Delete skipped — asset not found: id=%s", asset_id)
            return asset
        except Exception:
            logger.exception("Failed to delete asset id=%s", asset_id)
            raise


class AnimationRepo:
    def __init__(self, session):
        self.session = session

    def create(self, project_id, asset_id, animation_type, fps, frame_count, file_path):
        try:
            animation = Animation(
                animation_id=str(uuid.uuid4()),
                project_id=project_id,
                asset_id=asset_id,
                animation_type=animation_type,
                fps=fps,
                frame_count=frame_count,
                file_path=file_path,
            )
            self.session.add(animation)
            self.session.commit()
            logger.info("Created animation: id=%s type='%s' asset=%s project=%s fps=%d frames=%d",
                        animation.animation_id, animation_type, asset_id, project_id, fps, frame_count)
            return animation
        except Exception:
            logger.exception("Failed to create animation type='%s' asset=%s", animation_type, asset_id)
            raise

    def get(self, animation_id):
        try:
            animation = self.session.query(Animation).filter_by(animation_id=animation_id).first()
            if animation:
                logger.info("Retrieved animation: id=%s type='%s' asset=%s", animation_id, animation.animation_type, animation.asset_id)
            else:
                logger.info("Animation not found: id=%s", animation_id)
            return animation
        except Exception:
            logger.exception("Failed to get animation id=%s", animation_id)
            raise

    def get_by_project(self, project_id):
        try:
            animations = self.session.query(Animation).filter_by(project_id=project_id).order_by(Animation.created_at.desc()).all()
            logger.info("Retrieved %d animation(s) for project id=%s", len(animations), project_id)
            return animations
        except Exception:
            logger.exception("Failed to get animations for project id=%s", project_id)
            raise

    def get_by_asset(self, asset_id):
        try:
            animations = self.session.query(Animation).filter_by(asset_id=asset_id).order_by(Animation.created_at.desc()).all()
            logger.info("Retrieved %d animation(s) for asset id=%s", len(animations), asset_id)
            return animations
        except Exception:
            logger.exception("Failed to get animations for asset id=%s", asset_id)
            raise

    def delete(self, animation_id):
        try:
            animation = self.get(animation_id)
            if animation:
                self.session.delete(animation)
                self.session.commit()
                logger.info("Deleted animation: id=%s type='%s'", animation_id, animation.animation_type)
            else:
                logger.info("Delete skipped — animation not found: id=%s", animation_id)
            return animation
        except Exception:
            logger.exception("Failed to delete animation id=%s", animation_id)
            raise
