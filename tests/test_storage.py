import pytest
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.storage.database import Base
from app.storage.project_repo import ProjectRepo
from app.storage.asset_repo import AssetRepo, AnimationRepo
from app.storage.style_repo import StyleRepo


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
def project_repo(db_session):
    return ProjectRepo(db_session)


@pytest.fixture
def asset_repo(db_session):
    return AssetRepo(db_session)


@pytest.fixture
def animation_repo(db_session):
    return AnimationRepo(db_session)


@pytest.fixture
def style_repo(db_session):
    return StyleRepo(db_session)


@pytest.fixture
def sample_project(project_repo, db_session):
    proj = project_repo.create(name='Test Project', output_directory='/tmp/test_out')
    db_session.commit()
    return proj


class TestProjectRepo:
    def test_create_and_get(self, project_repo, db_session):
        proj = project_repo.create(name='My Project', output_directory='/tmp/out')
        db_session.commit()
        fetched = project_repo.get(proj.project_id)
        assert fetched is not None
        assert fetched.name == 'My Project'
        assert fetched.output_directory == '/tmp/out'

    def test_get_all(self, project_repo, db_session):
        project_repo.create(name='A', output_directory='/tmp/a')
        project_repo.create(name='B', output_directory='/tmp/b')
        db_session.commit()
        all_projects = project_repo.get_all()
        assert len(all_projects) >= 2

    def test_update(self, project_repo, db_session):
        proj = project_repo.create(name='Original', output_directory='/tmp/orig')
        db_session.commit()
        project_repo.update(proj.project_id, name='Updated')
        db_session.commit()
        fetched = project_repo.get(proj.project_id)
        assert fetched.name == 'Updated'

    def test_delete(self, project_repo, db_session):
        proj = project_repo.create(name='ToDelete', output_directory='/tmp/del')
        db_session.commit()
        project_repo.delete(proj.project_id)
        db_session.commit()
        assert project_repo.get(proj.project_id) is None


class TestAssetRepo:
    def test_create_and_get(self, asset_repo, db_session, sample_project):
        asset = asset_repo.create(
            project_id=sample_project.project_id,
            name='test_asset',
            asset_type='character',
            file_path='/tmp/test.png',
        )
        db_session.commit()
        fetched = asset_repo.get(asset.asset_id)
        assert fetched is not None
        assert fetched.name == 'test_asset'
        assert fetched.asset_type == 'character'

    def test_get_by_project(self, asset_repo, db_session, sample_project):
        for i in range(3):
            asset_repo.create(
                project_id=sample_project.project_id,
                name=f'asset_{i}',
                asset_type='prop',
                file_path=f'/tmp/{i}.png',
            )
        db_session.commit()
        assets = asset_repo.get_by_project(sample_project.project_id)
        assert len(assets) == 3

    def test_update(self, asset_repo, db_session, sample_project):
        asset = asset_repo.create(
            project_id=sample_project.project_id,
            name='original',
            asset_type='weapon',
            file_path='/tmp/orig.png',
        )
        db_session.commit()
        asset_repo.update(asset.asset_id, name='renamed')
        db_session.commit()
        assert asset_repo.get(asset.asset_id).name == 'renamed'

    def test_delete(self, asset_repo, db_session, sample_project):
        asset = asset_repo.create(
            project_id=sample_project.project_id,
            name='doomed',
            asset_type='effect',
            file_path='/tmp/doom.png',
        )
        db_session.commit()
        aid = asset.asset_id
        asset_repo.delete(aid)
        db_session.commit()
        assert asset_repo.get(aid) is None

    def test_cascade_on_project_delete(self, asset_repo, project_repo, db_session, sample_project):
        asset_repo.create(
            project_id=sample_project.project_id,
            name='orphan',
            asset_type='tileset',
            file_path='/tmp/orphan.png',
        )
        db_session.commit()
        assets_before = asset_repo.get_by_project(sample_project.project_id)
        assert len(assets_before) == 1
        project_repo.delete(sample_project.project_id)
        db_session.commit()
        assets_after = asset_repo.get_by_project(sample_project.project_id)
        assert len(assets_after) == 0


class TestAnimationRepo:
    def _create_asset(self, asset_repo, project_id, name):
        return asset_repo.create(
            project_id=project_id,
            name=name,
            asset_type='character',
            file_path=f'/tmp/{name}.png',
        )

    def test_create_and_get(self, animation_repo, asset_repo, db_session, sample_project):
        asset = self._create_asset(asset_repo, sample_project.project_id, 'hero')
        db_session.commit()
        anim = animation_repo.create(
            project_id=sample_project.project_id,
            asset_id=asset.asset_id,
            animation_type='idle',
            fps=8,
            frame_count=16,
            file_path='/tmp/anim',
        )
        db_session.commit()
        fetched = animation_repo.get(anim.animation_id)
        assert fetched is not None
        assert fetched.animation_type == 'idle'

    def test_get_by_project(self, animation_repo, asset_repo, db_session, sample_project):
        asset = self._create_asset(asset_repo, sample_project.project_id, 'hero')
        db_session.commit()
        for atype in ['idle', 'walk', 'run']:
            animation_repo.create(
                project_id=sample_project.project_id,
                asset_id=asset.asset_id,
                animation_type=atype,
                fps=8,
                frame_count=16,
                file_path=f'/tmp/{atype}',
            )
        db_session.commit()
        anims = animation_repo.get_by_project(sample_project.project_id)
        assert len(anims) == 3


class TestStyleRepo:
    def test_create_and_get(self, style_repo, db_session):
        style = style_repo.create(name='fantasy')
        db_session.commit()
        fetched = style_repo.get(style.style_profile_id)
        assert fetched is not None
        assert fetched.name == 'fantasy'

    def test_list_all(self, style_repo, db_session):
        style_repo.create(name='s1')
        style_repo.create(name='s2')
        db_session.commit()
        profiles = style_repo.get_all()
        assert len(profiles) >= 2

    def test_update(self, style_repo, db_session):
        style = style_repo.create(name='old')
        db_session.commit()
        style_repo.update(style.style_profile_id, name='new', cfg_scale=10.0)
        db_session.commit()
        fetched = style_repo.get(style.style_profile_id)
        assert fetched.name == 'new'
        assert fetched.cfg_scale == 10.0
