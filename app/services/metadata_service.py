import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataService:
    def __init__(self, session):
        self.session = session
        logger.info("MetadataService initialized")

    def generate_metadata(self, asset_id, project_id, name, asset_type,
                          style_profile_name='', animated=False, tileable=False,
                          extra=None):
        metadata = {
            'asset_id': asset_id,
            'project_id': project_id,
            'name': name,
            'asset_type': asset_type,
            'style_profile': style_profile_name,
            'animated': animated,
            'tileable': tileable,
            'created_at': datetime.utcnow().isoformat(),
        }
        if extra:
            metadata.update(extra)
        logger.info("Generated metadata for asset=%s, name=%s, type=%s", asset_id, name, asset_type)
        return metadata

    def save_metadata(self, metadata, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        logger.info("Saved metadata to %s", file_path)
        return file_path

    def load_metadata(self, file_path):
        logger.info("Loading metadata from %s", file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("Loaded metadata from %s — keys: %s", file_path, list(data.keys()))
        return data
