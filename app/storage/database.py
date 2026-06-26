import logging
import os
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.utils.config import resolve_path

logger = logging.getLogger(__name__)

Base = declarative_base()


class Project(Base):
    __tablename__ = 'projects'

    project_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    style_profile_id = Column(String(64), ForeignKey('style_profiles.style_profile_id'), nullable=True)
    output_directory = Column(String(1024), nullable=False)


class StyleProfile(Base):
    __tablename__ = 'style_profiles'

    style_profile_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    base_prompt = Column(Text, default='')
    negative_prompt = Column(Text, default='')
    palette_description = Column(Text, default='')
    cfg_scale = Column(Float, default=7.5)
    steps = Column(Integer, default=25)
    sampler = Column(String(64), default='DPMSolverMultistepScheduler')
    seed_strategy = Column(String(32), default='random')
    created_at = Column(DateTime, default=datetime.utcnow)


class Asset(Base):
    __tablename__ = 'assets'

    asset_id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey('projects.project_id'), nullable=False)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(64), nullable=False)
    file_path = Column(String(1024), nullable=False)
    thumbnail_path = Column(String(1024), nullable=True)
    metadata_path = Column(String(1024), nullable=True)
    tileable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Animation(Base):
    __tablename__ = 'animations'

    animation_id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey('projects.project_id'), nullable=False)
    asset_id = Column(String(64), ForeignKey('assets.asset_id'), nullable=False)
    animation_type = Column(String(64), nullable=False)
    fps = Column(Integer, default=8)
    frame_count = Column(Integer, default=16)
    file_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(resolve_path(''), 'database.db')
        logger.info("Creating database engine for path: %s", db_path)
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully at: %s", db_path)
        except Exception:
            logger.exception("Failed to create database tables at: %s", db_path)
            raise

    def get_session(self):
        logger.info("Acquiring new database session")
        return self.Session()
