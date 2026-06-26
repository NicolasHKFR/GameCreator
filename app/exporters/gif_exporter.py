import logging
import os

from PIL import Image


logger = logging.getLogger(__name__)


def export_gif(frames, dest_dir, name, fps=8):
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, f'{name}.gif')

    if not frames:
        logger.error("GIF export failed: frame list is empty for '%s'", path)
        return path

    frame_count = len(frames)
    duration_ms = 1000 // fps
    total_duration_s = (frame_count * duration_ms) / 1000
    logger.info(
        "Exporting GIF to '%s' — %d frames at %d fps (duration: %.2fs, %dms per frame)",
        path, frame_count, fps, total_duration_s, duration_ms,
    )
    try:
        frames[0].save(
            path, save_all=True, append_images=frames[1:],
            duration=duration_ms, loop=0, disposal=2,
        )
        file_size = os.path.getsize(path)
        logger.info("GIF export succeeded: '%s' (%d bytes, %d frames, %.2fs)", path, file_size, frame_count, total_duration_s)
    except Exception:
        logger.exception("GIF export failed to '%s'", path)
        raise
    return path
