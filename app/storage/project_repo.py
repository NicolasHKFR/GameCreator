import logging
import uuid
from datetime import datetime

from app.storage.database import Project, StyleProfile

logger = logging.getLogger(__name__)


class ProjectRepo:
    def __init__(self, session):
        self.session = session

    def create(self, name, output_directory, style_profile_id=None):
        try:
            project = Project(
                project_id=str(uuid.uuid4()),
                name=name,
                output_directory=output_directory,
                style_profile_id=style_profile_id,
            )
            self.session.add(project)
            self.session.commit()
            logger.info("Created project: id=%s name='%s'", project.project_id, name)
            return project
        except Exception:
            logger.exception("Failed to create project name='%s'", name)
            raise

    def get(self, project_id):
        try:
            project = self.session.query(Project).filter_by(project_id=project_id).first()
            if project:
                logger.info("Retrieved project: id=%s name='%s'", project_id, project.name)
            else:
                logger.info("Project not found: id=%s", project_id)
            return project
        except Exception:
            logger.exception("Failed to get project id=%s", project_id)
            raise

    def get_all(self):
        try:
            projects = self.session.query(Project).order_by(Project.updated_at.desc()).all()
            logger.info("Retrieved %d project(s)", len(projects))
            return projects
        except Exception:
            logger.exception("Failed to get all projects")
            raise

    def update(self, project_id, **kwargs):
        try:
            project = self.get(project_id)
            if project:
                changed = {k: v for k, v in kwargs.items() if getattr(project, k, None) != v}
                for key, value in kwargs.items():
                    setattr(project, key, value)
                project.updated_at = datetime.utcnow()
                self.session.commit()
                if changed:
                    logger.info("Updated project id=%s: %s", project_id, changed)
                else:
                    logger.info("Update called for project id=%s with no field changes", project_id)
            else:
                logger.info("Update skipped — project not found: id=%s", project_id)
            return project
        except Exception:
            logger.exception("Failed to update project id=%s", project_id)
            raise

    def delete(self, project_id):
        try:
            project = self.get(project_id)
            if project:
                self.session.delete(project)
                self.session.commit()
                logger.info("Deleted project: id=%s name='%s'", project_id, project.name)
            else:
                logger.info("Delete skipped — project not found: id=%s", project_id)
            return project
        except Exception:
            logger.exception("Failed to delete project id=%s", project_id)
            raise
