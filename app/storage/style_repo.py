import logging
import uuid

from app.storage.database import StyleProfile

logger = logging.getLogger(__name__)


class StyleRepo:
    def __init__(self, session):
        self.session = session

    def create(self, name, base_prompt='', negative_prompt='', palette_description='',
               cfg_scale=7.5, steps=25, sampler='DPMSolverMultistepScheduler', seed_strategy='random'):
        try:
            profile = StyleProfile(
                style_profile_id=str(uuid.uuid4()),
                name=name,
                base_prompt=base_prompt,
                negative_prompt=negative_prompt,
                palette_description=palette_description,
                cfg_scale=cfg_scale,
                steps=steps,
                sampler=sampler,
                seed_strategy=seed_strategy,
            )
            self.session.add(profile)
            self.session.commit()
            logger.info("Created style profile: id=%s name='%s' sampler='%s' steps=%d cfg=%.1f",
                        profile.style_profile_id, name, sampler, steps, cfg_scale)
            return profile
        except Exception:
            logger.exception("Failed to create style profile name='%s'", name)
            raise

    def get(self, style_profile_id):
        try:
            profile = self.session.query(StyleProfile).filter_by(style_profile_id=style_profile_id).first()
            if profile:
                logger.info("Retrieved style profile: id=%s name='%s'", style_profile_id, profile.name)
            else:
                logger.info("Style profile not found: id=%s", style_profile_id)
            return profile
        except Exception:
            logger.exception("Failed to get style profile id=%s", style_profile_id)
            raise

    def get_all(self):
        try:
            profiles = self.session.query(StyleProfile).order_by(StyleProfile.name).all()
            logger.info("Retrieved %d style profile(s)", len(profiles))
            return profiles
        except Exception:
            logger.exception("Failed to get all style profiles")
            raise

    def update(self, style_profile_id, **kwargs):
        try:
            profile = self.get(style_profile_id)
            if profile:
                changed = {k: v for k, v in kwargs.items() if getattr(profile, k, None) != v}
                for key, value in kwargs.items():
                    setattr(profile, key, value)
                self.session.commit()
                if changed:
                    logger.info("Updated style profile id=%s name='%s': %s", style_profile_id, profile.name, changed)
                else:
                    logger.info("Update called for style profile id=%s with no field changes", style_profile_id)
            else:
                logger.info("Update skipped — style profile not found: id=%s", style_profile_id)
            return profile
        except Exception:
            logger.exception("Failed to update style profile id=%s", style_profile_id)
            raise

    def delete(self, style_profile_id):
        try:
            profile = self.get(style_profile_id)
            if profile:
                self.session.delete(profile)
                self.session.commit()
                logger.info("Deleted style profile: id=%s name='%s'", style_profile_id, profile.name)
            else:
                logger.info("Delete skipped — style profile not found: id=%s", style_profile_id)
            return profile
        except Exception:
            logger.exception("Failed to delete style profile id=%s", style_profile_id)
            raise
