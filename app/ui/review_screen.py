import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QSplitter,
    QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.storage.asset_repo import AssetRepo
from app.services.background_service import BackgroundRemovalService
from app.services.extraction_service import SpriteExtractionService
from app.services.texture_service import TextureService


logger = logging.getLogger(__name__)


class ReviewScreen(QWidget):
    def __init__(self, main_window, project):
        super().__init__()
        self.main_window = main_window
        self.project = project
        app = main_window.app_instance
        self.session = app.track_session(app.get_db().get_session())
        self.asset_repo = AssetRepo(self.session)
        self.model_manager = app.model_manager
        self.bg_service = BackgroundRemovalService(self.model_manager)
        self.extraction = SpriteExtractionService()
        self.texture = TextureService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Review Assets — {project.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.asset_list = QListWidget()
        self.asset_list.currentItemChanged.connect(self.on_select_asset)
        left_layout.addWidget(QLabel("Assets:"))
        left_layout.addWidget(self.asset_list)

        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.preview_label = QLabel("Select an asset to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(256, 256)
        self.preview_label.setStyleSheet("border: 1px solid #555; border-radius: 4px; background-color: #2a2a2a;")
        right_layout.addWidget(self.preview_label)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #aaa;")
        right_layout.addWidget(self.info_label)

        splitter.addWidget(right)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        remove_bg_btn = QPushButton("Remove Background")
        remove_bg_btn.clicked.connect(self.remove_bg)
        extract_btn = QPushButton("Extract Sprites")
        extract_btn.clicked.connect(self.extract_sprites)
        make_tile_btn = QPushButton("Make Tile")
        make_tile_btn.clicked.connect(self.make_tile)
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_asset)
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("QPushButton { background-color: #5c2e2e; } QPushButton:hover { background-color: #7a3a3a; }")
        delete_btn.clicked.connect(self.delete_asset)
        back_btn = QPushButton("Back to Generation")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to('generation'))
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.clicked.connect(lambda: self.main_window.navigate_to('dashboard'))

        btn_layout.addWidget(remove_bg_btn)
        btn_layout.addWidget(extract_btn)
        btn_layout.addWidget(make_tile_btn)
        btn_layout.addWidget(rename_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(dashboard_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.refresh_assets()

    def refresh_assets(self):
        self.asset_list.clear()
        assets = self.asset_repo.get_by_project(self.project.project_id)
        for a in assets:
            item = QListWidgetItem(f"{a.name} ({a.asset_type})")
            item.setData(Qt.UserRole, a.asset_id)
            self.asset_list.addItem(item)

    def get_selected_asset(self):
        item = self.asset_list.currentItem()
        if item:
            return self.asset_repo.get(item.data(Qt.UserRole))
        return None

    def on_select_asset(self, current, previous):
        if not current:
            return
        asset = self.asset_repo.get(current.data(Qt.UserRole))
        if asset and os.path.exists(asset.file_path):
            pixmap = QPixmap(asset.file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
            self.info_label.setText(f"Type: {asset.asset_type} | Path: {asset.file_path}")

    def remove_bg(self):
        asset = self.get_selected_asset()
        if not asset:
            return
        logger.info("Removing background: asset='%s', path='%s'", asset.name, asset.file_path)
        out_dir = os.path.dirname(asset.file_path)
        try:
            out_path, _ = self.bg_service.remove_background(asset.file_path, out_dir)
            self.asset_repo.update(asset.asset_id, file_path=out_path)
            self.refresh_assets()
            logger.info("Background removed: asset='%s', new_path='%s'", asset.name, out_path)
            QMessageBox.information(self, "Done", "Background removed!")
        except Exception as e:
            logger.exception("Failed to remove background for asset='%s': %s", asset.name, e)
            QMessageBox.critical(self, "Error", str(e))

    def extract_sprites(self):
        asset = self.get_selected_asset()
        if not asset:
            return
        logger.info("Extracting sprites: asset='%s', path='%s'", asset.name, asset.file_path)
        out_dir = os.path.join(os.path.dirname(asset.file_path), 'sprites')
        try:
            sprites = self.extraction.extract_sprites(asset.file_path, out_dir)
            for s in sprites:
                self.asset_repo.create(
                    project_id=self.project.project_id,
                    name=s['name'],
                    asset_type='sprite',
                    file_path=s['file_path'],
                )
            self.session.commit()
            self.refresh_assets()
            logger.info("Extracted %d sprite(s) from asset='%s'", len(sprites), asset.name)
            QMessageBox.information(self, "Done", f"Extracted {len(sprites)} sprites!")
        except Exception as e:
            logger.exception("Failed to extract sprites from asset='%s': %s", asset.name, e)
            QMessageBox.critical(self, "Error", str(e))

    def make_tile(self):
        asset = self.get_selected_asset()
        if not asset:
            return
        logger.info("Making tile: asset='%s', path='%s'", asset.name, asset.file_path)
        out_dir = os.path.dirname(asset.file_path)
        try:
            out_path, _ = self.texture.make_seamless(asset.file_path, out_dir)
            self.asset_repo.create(
                project_id=self.project.project_id,
                name=f'{asset.name}_tile',
                asset_type='tile',
                file_path=out_path,
                tileable=True,
            )
            self.session.commit()
            self.refresh_assets()
            logger.info("Tile created: asset='%s', tile_path='%s'", asset.name, out_path)
            QMessageBox.information(self, "Done", "Seamless tile created!")
        except Exception as e:
            logger.exception("Failed to create tile for asset='%s': %s", asset.name, e)
            QMessageBox.critical(self, "Error", str(e))

    def rename_asset(self):
        asset = self.get_selected_asset()
        if not asset:
            return
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Rename Asset", "New name:", text=asset.name)
        if ok and name.strip():
            old_name = asset.name
            self.asset_repo.update(asset.asset_id, name=name.strip())
            self.session.commit()
            self.refresh_assets()
            logger.info("Renamed asset: id=%s, '%s' -> '%s'", asset.asset_id, old_name, name.strip())

    def delete_asset(self):
        asset = self.get_selected_asset()
        if not asset:
            return
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete {asset.name}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            logger.info("Deleting asset: id=%s, name='%s', path='%s'", asset.asset_id, asset.name, asset.file_path)
            for del_path in [asset.file_path, asset.thumbnail_path, asset.metadata_path]:
                if del_path and os.path.exists(del_path):
                    os.remove(del_path)
                    logger.debug("Removed file: %s", del_path)
            self.asset_repo.delete(asset.asset_id)
            self.session.commit()
            self.refresh_assets()
            self.preview_label.clear()
            self.info_label.setText("")
