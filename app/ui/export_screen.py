import logging
import os
import shutil
import zipfile

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QFileDialog, QMessageBox, QProgressBar
)

from app.services.export_service import ExportService
from app.storage.asset_repo import AssetRepo

logger = logging.getLogger(__name__)


class ExportScreen(QWidget):
    def __init__(self, main_window, project):
        super().__init__()
        self.main_window = main_window
        self.project = project
        app = main_window.app_instance
        self.session = app.track_session(app.get_db().get_session())
        self.export_service = ExportService(self.session)
        self.asset_repo = AssetRepo(self.session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Export — {project.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        assets = self.asset_repo.get_by_project(project.project_id)
        info = QLabel(f"Assets: {len(assets)}")
        info.setStyleSheet("color: #aaa; font-size: 14px;")
        layout.addWidget(info)

        dest_layout = QHBoxLayout()
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Select export destination...")
        dest_layout.addWidget(self.dest_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self.dest_input.setText(
            QFileDialog.getExistingDirectory(self, "Export Destination")
        ))
        dest_layout.addWidget(browse_btn)
        layout.addLayout(dest_layout)

        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['Folder', 'ZIP Archive'])
        fmt_layout.addWidget(self.format_combo)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export Entire Project")
        export_btn.setStyleSheet("""
            QPushButton { background-color: #4a9eff; color: #fff; border: none; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #3a8eef; }
        """)
        export_btn.clicked.connect(self.export_project)
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to('review'))
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.clicked.connect(lambda: self.main_window.navigate_to('dashboard'))

        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(dashboard_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def export_project(self):
        destination = self.dest_input.text().strip()
        if not destination:
            logger.warning("Export aborted: no destination selected")
            QMessageBox.warning(self, "Error", "Select an export destination.")
            return

        asset_count = len(self.asset_repo.get_by_project(self.project.project_id))
        export_format = self.format_combo.currentText()
        logger.info(
            "Export requested: project='%s', destination='%s', asset_count=%d, format='%s'",
            self.project.name, destination, asset_count, export_format
        )

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            if export_format == 'ZIP Archive':
                temp_dir = destination + '_tmp'
                export_path = self.export_service.export_project(self.project, temp_dir)
                zip_path = os.path.join(destination, f'{self.project.name}_export.zip')
                os.makedirs(os.path.dirname(zip_path), exist_ok=True)
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(temp_dir):
                        for fn in files:
                            fp = os.path.join(root, fn)
                            zf.write(fp, os.path.relpath(fp, temp_dir))
                shutil.rmtree(temp_dir, ignore_errors=True)
                export_path = zip_path
            else:
                export_path = self.export_service.export_project(self.project, destination)
            self.progress_bar.setValue(100)
            logger.info(
                "Export completed: project='%s', destination='%s', export_path='%s'",
                self.project.name, destination, export_path
            )
            QMessageBox.information(self, "Export Complete", f"Exported to:\n{export_path}")
        except Exception as e:
            logger.exception("Export failed for project='%s', destination='%s': %s", self.project.name, destination, e)
            QMessageBox.critical(self, "Export Failed", str(e))
