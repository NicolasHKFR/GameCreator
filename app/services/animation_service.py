import logging
import os
import uuid

from PIL import Image

from app.utils.config import get_app_config
from app.utils.errors import AnimationError

logger = logging.getLogger(__name__)


class AnimationService:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.config = get_app_config()
        logger.info("AnimationService initialized")

    def _generate_frames(self, source_image_path, animation_type, frame_count, fps):
        logger.info(
            "Generating animation frames — source=%s, type=%s, frames=%d, fps=%d",
            source_image_path, animation_type, frame_count, fps,
        )
        source = Image.open(source_image_path).convert('RGBA')
        frames = []

        for i in range(frame_count):
            progress = i / max(frame_count - 1, 1)
            frame = source.copy()

            if animation_type in ('idle',):
                offset_y = int(2 * np.sin(progress * 2 * np.pi))
                import numpy as np
                frame = source.copy()
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(frame, (0, offset_y))
                frame = canvas
            elif animation_type == 'walk':
                import numpy as np
                leg_angle = np.sin(progress * 2 * np.pi) * 5
                offset_x = int(4 * np.sin(progress * 2 * np.pi))
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(source, (offset_x, 0))
                frame = canvas

            frames.append(frame)

        logger.info("Generated %d frame(s) for animation type '%s'", len(frames), animation_type)
        return frames

    def _validate_loop(self, frames):
        if len(frames) < 2:
            logger.debug("Loop validation skipped — fewer than 2 frames")
            return True, 1.0

        import numpy as np
        first = np.array(frames[0]).astype(float)
        last = np.array(frames[-1]).astype(float)
        mse = np.mean((first - last) ** 2)
        similarity = 1.0 - min(mse / (255 ** 2), 1.0)
        valid = similarity >= 0.95

        logger.info("Loop validation — similarity=%.4f, valid=%s", similarity, valid)
        if not valid:
            logger.warning("Loop quality below 95%% threshold — similarity=%.4f", similarity)

        return valid, similarity

    def generate_animation(self, source_image_path, output_dir, animation_type,
                          frame_count=16, fps=8):
        logger.info(
            "Generating animation — source=%s, output_dir=%s, type=%s, frames=%d, fps=%d",
            source_image_path, output_dir, animation_type, frame_count, fps,
        )
        import numpy as np
        os.makedirs(output_dir, exist_ok=True)

        try:
            frames = self._generate_frames(source_image_path, animation_type, frame_count, fps)
        except Exception as e:
            logger.exception("Frame generation failed for %s", source_image_path)
            raise AnimationError(f"Frame generation failed: {e}")

        is_valid, similarity = self._validate_loop(frames)
        if not is_valid:
            logger.warning("Loop quality=%.4f — accepting with warning (not failing)", similarity)

        anim_id = uuid.uuid4().hex[:8]
        frame_dir = os.path.join(output_dir, f'{animation_type}_{anim_id}')
        os.makedirs(frame_dir, exist_ok=True)

        frame_paths = []
        for i, frame in enumerate(frames):
            path = os.path.join(frame_dir, f'frame_{i:04d}.png')
            frame.save(path, 'PNG')
            frame_paths.append(path)

        logger.info("Saved %d frame(s) to %s", len(frame_paths), frame_dir)

        gif_path = os.path.join(output_dir, f'{animation_type}_{anim_id}.gif')
        frames[0].save(
            gif_path, save_all=True, append_images=frames[1:],
            duration=1000 // fps, loop=0, disposal=2,
        )
        logger.info("Saved animation GIF to %s", gif_path)

        result = {
            'animation_id': anim_id,
            'animation_type': animation_type,
            'fps': fps,
            'frame_count': len(frames),
            'frame_paths': frame_paths,
            'gif_path': gif_path,
            'loop_similarity': float(similarity),
            'valid_loop': bool(is_valid),
        }
        logger.info("Animation generation complete — id=%s, type=%s, frames=%d", anim_id, animation_type, len(frames))
        return result
