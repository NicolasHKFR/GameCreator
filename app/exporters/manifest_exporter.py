import json
import logging
import os
from datetime import datetime


logger = logging.getLogger(__name__)


def generate_manifest(project_name, project_id, assets, animations, destination):
    manifest = {
        'project_name': project_name,
        'project_id': project_id,
        'exported_at': datetime.utcnow().isoformat(),
        'asset_count': len(assets),
        'animation_count': len(animations),
        'assets': [{
            'asset_id': a.asset_id,
            'name': a.name,
            'type': a.asset_type,
            'file': os.path.basename(a.file_path) if a.file_path else '',
        } for a in assets],
        'animations': [{
            'animation_id': a.animation_id,
            'asset_id': a.asset_id,
            'type': a.animation_type,
            'fps': a.fps,
            'frames': a.frame_count,
        } for a in animations],
    }
    os.makedirs(destination, exist_ok=True)
    path = os.path.join(destination, 'manifest.json')

    logger.info(
        "Generating manifest at '%s' — project='%s' (%s), %d assets, %d animations",
        path, project_name, project_id, len(assets), len(animations),
    )
    logger.debug("Manifest JSON structure: %s", json.dumps(manifest, indent=2))

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        file_size = os.path.getsize(path)
        logger.info("Manifest export succeeded: '%s' (%d bytes, %d assets, %d animations)", path, file_size, len(assets), len(animations))
    except (OSError, IOError) as e:
        logger.exception("Failed to write manifest file to '%s': %s", path, e)
        raise
    return path
