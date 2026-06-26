import logging
import os
import uuid

from PIL import Image

from app.exporters.gif_exporter import export_gif
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
        import numpy as np
        source = Image.open(source_image_path).convert('RGBA')
        w, h = source.size
        frames = []

        for i in range(frame_count):
            t = i / max(frame_count - 1, 1)
            angle = t * 2 * np.pi

            if animation_type == 'idle':
                offset_y = int(2 * np.sin(angle))
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(source, (0, offset_y))
                frames.append(canvas)

            elif animation_type == 'walk':
                offset_x = int(4 * np.sin(angle))
                body_sway = int(1 * np.sin(angle * 2))
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(source, (offset_x, body_sway))
                frames.append(canvas)

            elif animation_type == 'run':
                offset_x = int(8 * np.sin(angle))
                stretch = 1.0 + 0.05 * np.sin(angle)
                new_w = max(int(w * stretch), 1)
                new_h = max(int(h * stretch), 1)
                resized = source.resize((new_w, new_h), Image.LANCZOS)
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(resized, (offset_x, 0))
                frames.append(canvas)

            elif animation_type == 'attack':
                swing_x = int(16 * np.sin(angle))
                tilt = int(8 * (1 - abs(np.cos(angle))) * np.sign(np.sin(angle)))
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(source, (swing_x, tilt))
                frames.append(canvas)

            elif animation_type == 'jump':
                height = int(20 * np.abs(np.sin(angle)))
                squash = 1.0 + 0.15 * (1 - np.abs(np.sin(angle)))
                new_h = max(int(h / squash), 1)
                resized = source.resize((w, new_h), Image.LANCZOS)
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(resized, (0, h - new_h - height))
                frames.append(canvas)

            elif animation_type == 'hurt':
                shake_x = int(6 * np.sin(angle * 4))
                shake_y = int(3 * np.cos(angle * 4))
                alpha = max(0, 1.0 - 0.3 * np.abs(np.sin(angle)))
                tinted = source.copy()
                tinted.putalpha(int(alpha * 255))
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(tinted, (shake_x, shake_y))
                frames.append(canvas)

            elif animation_type == 'death':
                fade = 1.0 - t * 0.8
                sink = int(16 * t)
                alpha = max(0, int(fade * 255))
                faded = source.copy()
                faded.putalpha(alpha)
                canvas = Image.new('RGBA', source.size, (0, 0, 0, 0))
                canvas.paste(faded, (0, sink))
                frames.append(canvas)

            else:
                frames.append(source.copy())

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

        gif_name = f'{animation_type}_{anim_id}'
        gif_path = export_gif(frames, output_dir, gif_name, fps=fps)

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
