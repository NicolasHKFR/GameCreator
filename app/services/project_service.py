import logging
import os
import shutil
from datetime import datetime

from app.storage.project_repo import ProjectRepo

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, session):
        self.session = session
        self.repo = ProjectRepo(session)
        logger.info("ProjectService initialized")

    def create_project(self, name, output_directory):
        logger.info("Creating project — name=%s, output_directory=%s", name, output_directory)
        project = self.repo.create(name=name, output_directory=output_directory)

        dirs = ['assets', 'animations', 'metadata', 'exports']
        for subdir in dirs:
            path = os.path.join(output_directory, project.project_id, subdir)
            os.makedirs(path, exist_ok=True)
            logger.info("Created project directory: %s", path)

        logger.info("Project created — id=%s, name=%s, base_dir=%s", project.project_id, name, output_directory)
        return project

    def load_project(self, project_id):
        logger.info("Loading project — id=%s", project_id)
        project = self.repo.get(project_id)
        if project:
            logger.info("Project loaded — id=%s, name=%s", project.project_id, project.name)
        else:
            logger.warning("Project not found — id=%s", project_id)
        return project

    def list_projects(self):
        projects = self.repo.get_all()
        logger.info("Listing projects — count=%d", len(projects))
        return projects

    def delete_project(self, project_id):
        logger.info("Deleting project — id=%s", project_id)
        project = self.repo.get(project_id)
        if project:
            project_dir = os.path.join(project.output_directory, project.project_id)
            if os.path.exists(project_dir):
                logger.info("Removing project directory tree: %s", project_dir)
                shutil.rmtree(project_dir, ignore_errors=True)
                logger.info("Project directory removed: %s", project_dir)
            self.repo.delete(project_id)
            logger.info("Project record deleted from DB — id=%s", project_id)
        else:
            logger.warning("Project not found for deletion — id=%s", project_id)
        return project

    def update_project(self, project_id, **kwargs):
        logger.info("Updating project — id=%s, fields=%s", project_id, set(kwargs.keys()))
        project = self.repo.update(project_id, **kwargs)
        if project:
            logger.info("Project updated — id=%s", project_id)
        else:
            logger.warning("Project not found for update — id=%s", project_id)
        return project
