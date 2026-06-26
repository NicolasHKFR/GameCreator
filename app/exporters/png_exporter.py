import logging
import os
import shutil

from PIL import Image


logger = logging.getLogger(__name__)


def export_png(source_path, dest_dir, filename=None):
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = os.path.basename(source_path)
    dest_path = os.path.join(dest_dir, filename)
    source_size = os.path.getsize(source_path)
    logger.info("Copying PNG from '%s' to '%s' (source size: %d bytes)", source_path, dest_path, source_size)
    try:
        shutil.copy2(source_path, dest_path)
        dest_size = os.path.getsize(dest_path)
        logger.info("PNG export succeeded: '%s' (%d bytes)", dest_path, dest_size)
    except Exception:
        logger.exception("PNG export failed from '%s' to '%s'", source_path, dest_path)
        raise
    return dest_path


def export_png_with_metadata(image: Image.Image, dest_dir, name):
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, f'{name}.png')
    logger.info("Saving PNG with metadata to '%s' (image mode=%s, size=%s)", path, image.mode, image.size)
    try:
        image.save(path, 'PNG')
        file_size = os.path.getsize(path)
        logger.info("PNG with metadata export succeeded: '%s' (%d bytes)", path, file_size)
    except Exception:
        logger.exception("PNG with metadata export failed to '%s'", path)
        raise
    return path
