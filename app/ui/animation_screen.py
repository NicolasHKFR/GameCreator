import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QListWidget, QListWidgetItem, QMessageBox,
    QGroupBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QMovie

from app.services.animation_service import AnimationService
from app.storage.asset_repo import AssetRepo, AnimationRepo
from app.utils.config import get_app_config

logger = logging.getLogger(__name__)


class AnimationScreen(QWidget):
    def __init__(self, main_window, project):
        super().__init__()
        self.main_window = main_window
        self.project = project
        app = main_window.app_instance
        self.session = app.track_session(app.get_db().get_session())
        self.model_manager = app.model_manager
        self.animation_service = AnimationService(self.model_manager)
        self.asset_repo = AssetRepo(self.session)
        self.animation_repo = AnimationRepo(self.session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Animations — {project.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        if not get_app_config().get('enable_animation', False):
            logger.warning("Animation screen disabled: enable_animation is false in config")
            disabled = QLabel("Animation is disabled. Set enable_animation: true in config.")
            disabled.setStyleSheet("color: #ffaa00; font-size: 14px; padding: 16px;")
            layout.addWidget(disabled)
            back_btn = QPushButton("Back")
            back_btn.clicked.connect(lambda: self.main_window.navigate_to('review'))
            layout.addWidget(back_btn)
            return

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Assets:"))

        self.asset_list = QListWidget()
        assets = self.asset_repo.get_by_project(project.project_id)
        for a in assets:
            item = QListWidgetItem(f"{a.name} ({a.asset_type})")
            item.setData(Qt.UserRole, a.asset_id)
            self.asset_list.addItem(item)
        left_layout.addWidget(self.asset_list)

        splitter.addWidget(left_panel)

        center = QWidget()
        center_layout = QVBoxLayout(center)

        self.anim_type = QComboBox()
        self.anim_type.addItems(['idle', 'walk', 'run', 'attack', 'jump', 'hurt', 'death'])
        center_layout.addWidget(QLabel("Animation Type:"))
        center_layout.addWidget(self.anim_type)

        self.fps = QSpinBox()
        self.fps.setRange(4, 24)
        self.fps.setValue(8)
        center_layout.addWidget(QLabel("FPS:"))
        center_layout.addWidget(self.fps)

        self.frame_count = QSpinBox()
        self.frame_count.setRange(4, 64)
        self.frame_count.setValue(16)
        center_layout.addWidget(QLabel("Frame Count:"))
        center_layout.addWidget(self.frame_count)

        splitter.addWidget(center)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(256, 256)
        self.preview_label.setStyleSheet("border: 1px solid #555; border-radius: 4px; background-color: #2a2a2a;")
        self.preview_label.setText("Preview")
        self._movie = None

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.addWidget(QLabel("Preview:"))
        preview_layout.addWidget(self.preview_label)
        splitter.addWidget(preview_container)

        splitter.setSizes([250, 250, 300])
        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("Generate Animation")
        gen_btn.clicked.connect(self.generate_animation)
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to('review'))
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.clicked.connect(lambda: self.main_window.navigate_to('dashboard'))
        btn_layout.addWidget(gen_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(dashboard_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _show_gif_preview(self, gif_path):
        if self._movie:
            self._movie.stop()
            self._movie.deleteLater()
        if os.path.exists(gif_path):
            self._movie = QMovie(gif_path)
            self._movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self._movie.setScaledSize(self.preview_label.size() * 0.8)
            self.preview_label.setMovie(self._movie)
            self._movie.start()

    def generate_animation(self):
        item = self.asset_list.currentItem()
        if not item:
            logger.warning("Animation generation aborted: no asset selected")
            QMessageBox.warning(self, "Error", "Select an asset first.")
            return

        asset = self.asset_repo.get(item.data(Qt.UserRole))
        if not asset or not os.path.exists(asset.file_path):
            logger.warning("Animation generation aborted: asset file not found (id=%s)", item.data(Qt.UserRole))
            QMessageBox.warning(self, "Error", "Asset file not found.")
            return

        anim_type = self.anim_type.currentText()
        fps = self.fps.value()
        frames = self.frame_count.value()

        logger.info(
            "Animation requested: asset='%s', type='%s', fps=%d, frames=%d, project='%s'",
            asset.name, anim_type, fps, frames, self.project.name
        )

        output_dir = os.path.join(self.project.output_directory, self.project.project_id, 'animations')

        try:
            result = self.animation_service.generate_animation(
                asset.file_path, output_dir, anim_type, frames, fps
            )
            self.animation_repo.create(
                project_id=self.project.project_id,
                asset_id=asset.asset_id,
                animation_type=anim_type,
                fps=fps,
                frame_count=frames,
                file_path=os.path.dirname(result['gif_path']),
            )
            self.session.commit()

            loop_quality = result['loop_similarity'] * 100
            valid = result['valid_loop']
            logger.info(
                "Animation generated: asset='%s', type='%s', loop_quality=%.1f%%, valid_loop=%s",
                asset.name, anim_type, loop_quality, valid
            )

            self._show_gif_preview(result['gif_path'])

            msg = f"Animation '{anim_type}' generated!\nLoop quality: {loop_quality:.0f}%"
            if not valid:
                msg += "\nWarning: loop quality below 95% threshold."
                logger.warning("Low loop quality for asset='%s', type='%s': %.1f%%", asset.name, anim_type, loop_quality)
            QMessageBox.information(self, "Complete", msg)
        except Exception as e:
            logger.exception("Animation generation failed for asset='%s', type='%s': %s", asset.name, anim_type, e)
            QMessageBox.critical(self, "Error", str(e))
