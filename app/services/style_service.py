import logging

from app.storage.style_repo import StyleRepo

logger = logging.getLogger(__name__)


class StyleService:
    def __init__(self, session):
        self.session = session
        self.repo = StyleRepo(session)
        logger.info("StyleService initialized")

    def create_style_profile(self, name, base_prompt='', negative_prompt='',
                             palette_description='', cfg_scale=7.5, steps=25,
                             sampler='DPMSolverMultistepScheduler', seed_strategy='random'):
        logger.info("Creating style profile — name=%s, cfg_scale=%.1f, steps=%d, sampler=%s",
                    name, cfg_scale, steps, sampler)
        profile = self.repo.create(
            name=name, base_prompt=base_prompt, negative_prompt=negative_prompt,
            palette_description=palette_description, cfg_scale=cfg_scale,
            steps=steps, sampler=sampler, seed_strategy=seed_strategy,
        )
        logger.info("Style profile created — id=%s, name=%s", profile.id, name)
        return profile

    def update_style_profile(self, profile_id, **kwargs):
        logger.info("Updating style profile — id=%s, fields=%s", profile_id, set(kwargs.keys()))
        profile = self.repo.update(profile_id, **kwargs)
        if profile:
            logger.info("Style profile updated — id=%s", profile_id)
        else:
            logger.warning("Style profile not found for update — id=%s", profile_id)
        return profile

    def get_style_profile(self, profile_id):
        logger.info("Getting style profile — id=%s", profile_id)
        profile = self.repo.get(profile_id)
        if profile:
            logger.info("Style profile found — id=%s, name=%s", profile.id, profile.name)
        else:
            logger.warning("Style profile not found — id=%s", profile_id)
        return profile

    def list_style_profiles(self):
        profiles = self.repo.get_all()
        logger.info("Listing style profiles — count=%d", len(profiles))
        return profiles

    def delete_style_profile(self, profile_id):
        logger.info("Deleting style profile — id=%s", profile_id)
        profile = self.repo.get(profile_id)
        if profile:
            self.repo.delete(profile_id)
            logger.info("Style profile deleted — id=%s, name=%s", profile_id, profile.name)
        else:
            logger.warning("Style profile not found for deletion — id=%s", profile_id)
        return profile

    def compose_prompt(self, profile, user_prompt):
        parts = [user_prompt]
        if profile and profile.base_prompt:
            parts.append(profile.base_prompt)
        if profile and profile.palette_description:
            parts.append(profile.palette_description)
        combined = ', '.join(parts)
        logger.debug("Composed prompt — profile=%s, base=%r, palette=%r => %r",
                     profile.name if profile else None,
                     profile.base_prompt if profile else None,
                     profile.palette_description if profile else None,
                     combined)
        return combined

    def get_negative_prompt(self, profile):
        if profile and profile.negative_prompt:
            logger.debug("Using profile negative prompt for profile=%s", profile.name)
            return profile.negative_prompt
        logger.debug("No profile negative prompt, returning empty string")
        return ''
