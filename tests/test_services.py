import os
import pytest
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.storage.database import Base
from app.storage.project_repo import ProjectRepo
from app.storage.asset_repo import AssetRepo
from app.services.style_service import StyleService
from app.services.metadata_service import MetadataService
from app.services.project_service import ProjectService
from app.services.export_service import ExportService


@pytest.fixture
def db_session():
    engine = create_engine('sqlite://', echo=False, connect_args={'check_same_thread': False})
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_project(db_session):
    repo = ProjectRepo(db_session)
    proj = repo.create(name='Test Project', output_directory='/tmp/test_out')
    db_session.commit()
    return proj


class TestStyleService:
    def test_create_and_list(self, db_session):
        service = StyleService(db_session)
        profile = service.create_style_profile(
            name='test_style',
            base_prompt='fantasy art',
            negative_prompt='ugly',
            cfg_scale=7.5,
            steps=25,
            sampler='EulerDiscreteScheduler',
            seed_strategy='random',
        )
        db_session.commit()
        assert profile.name == 'test_style'
        profiles = service.list_style_profiles()
        assert any(p.name == 'test_style' for p in profiles)

    def test_get_style_profile(self, db_session):
        service = StyleService(db_session)
        profile = service.create_style_profile(name='get_test')
        db_session.commit()
        fetched = service.get_style_profile(profile.style_profile_id)
        assert fetched is not None
        assert fetched.name == 'get_test'

    def test_update_style_profile(self, db_session):
        service = StyleService(db_session)
        profile = service.create_style_profile(name='before')
        db_session.commit()
        service.update_style_profile(profile.style_profile_id, name='after', cfg_scale=12.0)
        db_session.commit()
        fetched = service.get_style_profile(profile.style_profile_id)
        assert fetched.name == 'after'
        assert fetched.cfg_scale == 12.0

    def test_compose_prompt(self, db_session):
        service = StyleService(db_session)
        profile = service.create_style_profile(
            name='composer',
            base_prompt='oil painting, detailed',
            palette_description='warm colors',
        )
        result = service.compose_prompt(profile, 'a knight')
        assert 'oil painting' in result
        assert 'detailed' in result
        assert 'warm colors' in result
        assert 'a knight' in result

    def test_compose_prompt_no_profile(self, db_session):
        service = StyleService(db_session)
        result = service.compose_prompt(None, 'a sword')
        assert result == 'a sword'

    def test_get_negative_prompt(self, db_session):
        service = StyleService(db_session)
        profile = service.create_style_profile(name='neg', negative_prompt='bad, blurry')
        result = service.get_negative_prompt(profile)
        assert result == 'bad, blurry'

    def test_get_negative_prompt_none(self, db_session):
        service = StyleService(db_session)
        result = service.get_negative_prompt(None)
        assert result is None or result == ''


class TestMetadataService:
    def test_generate_metadata(self, db_session):
        service = MetadataService(db_session)
        meta = service.generate_metadata(
            asset_id='a1',
            project_id='p1',
            name='hero',
            asset_type='character',
            style_profile_name='fantasy',
        )
        assert meta['asset_id'] == 'a1'
        assert meta['project_id'] == 'p1'
        assert meta['name'] == 'hero'
        assert meta['asset_type'] == 'character'
        assert meta['style_profile'] == 'fantasy'
        assert 'created_at' in meta

    def test_generate_metadata_defaults(self, db_session):
        service = MetadataService(db_session)
        meta = service.generate_metadata(
            asset_id='a2',
            project_id='p2',
            name='orc',
            asset_type='character',
        )
        assert meta['style_profile'] == ''
        assert not meta['animated']
        assert not meta['tileable']


class TestProjectService:
    def test_delete_project_cascades(self, db_session):
        asset_repo = AssetRepo(db_session)
        project_repo = ProjectRepo(db_session)
        service = ProjectService(db_session)

        project = project_repo.create(name='CascadeTest', output_directory='/tmp/cascade')
        db_session.commit()

        asset_repo.create(project_id=project.project_id, name='child', asset_type='prop', file_path='/tmp/c.png')
        db_session.commit()

        service.delete_project(project.project_id)
        db_session.commit()

        assert project_repo.get(project.project_id) is None
        assert len(asset_repo.get_by_project(project.project_id)) == 0


class TestExportService:
    def test_export_project_structure(self, tmp_path, db_session, sample_project):
        asset_repo = AssetRepo(db_session)
        asset_repo.create(
            project_id=sample_project.project_id,
            name='test_asset',
            asset_type='character',
            file_path=str(tmp_path / 'test.png'),
        )
        db_session.commit()

        export_dir = tmp_path / 'export'
        service = ExportService(db_session)
        result = service.export_project(sample_project, str(export_dir))

        assert result == str(export_dir)
        assert os.path.isdir(str(export_dir))
        assert os.path.isdir(os.path.join(str(export_dir), 'Characters'))
