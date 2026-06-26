import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QDialog, QLineEdit, QFormLayout,
    QDialogButtonBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from app.storage.database import Database
from app.storage.project_repo import ProjectRepo

logger = logging.getLogger(__name__)


class DashboardScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db = main_window.app_instance.get_db()
        self.session = self.db.get_session()
        self.repo = ProjectRepo(self.session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QHBoxLayout()
        title = QLabel("Projects")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #fff;")
        header.addWidget(title)
        header.addStretch()

        create_btn = QPushButton("+ New Project")
        create_btn.setStyleSheet("""
            QPushButton { background-color: #4a9eff; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #3a8eef; }
        """)
        create_btn.clicked.connect(self.create_project_dialog)
        header.addWidget(create_btn)

        layout.addLayout(header)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet("QListWidget { font-size: 14px; } QListWidget::item { padding: 12px; border-bottom: 1px solid #333; }")
        self.project_list.itemDoubleClicked.connect(self.open_project)
        layout.addWidget(self.project_list)

        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Open Project")
        open_btn.clicked.connect(self.open_selected_project)
        delete_btn = QPushButton("Delete Project")
        delete_btn.setStyleSheet("QPushButton { background-color: #5c2e2e; } QPushButton:hover { background-color: #7a3a3a; }")
        delete_btn.clicked.connect(self.delete_selected_project)
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        self.project_list.clear()
        projects = self.repo.get_all()
        for p in projects:
            item = QListWidgetItem(f"{p.name}  —  Created: {p.created_at.strftime('%Y-%m-%d %H:%M')}")
            item.setData(Qt.UserRole, p.project_id)
            self.project_list.addItem(item)

    def create_project_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Project")
        dialog.setMinimumWidth(400)
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Project name")
        layout.addRow("Project Name:", name_input)

        dir_input = QLineEdit()
        dir_input.setPlaceholderText("Output directory")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: dir_input.setText(QFileDialog.getExistingDirectory(dialog, "Select Output Directory")))
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(dir_input)
        dir_layout.addWidget(browse_btn)
        layout.addRow("Output Directory:", dir_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._do_create_project(dialog, name_input, dir_input))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.exec()

    def _do_create_project(self, dialog, name_input, dir_input):
        name = name_input.text().strip()
        directory = dir_input.text().strip()
        if not name:
            logger.warning("Project creation failed: name is empty")
            QMessageBox.warning(dialog, "Error", "Project name cannot be empty.")
            return
        if not directory:
            logger.warning("Project creation failed: output directory is empty")
            QMessageBox.warning(dialog, "Error", "Output directory cannot be empty.")
            return

        self.repo.create(name=name, output_directory=directory)
        self.session.commit()
        logger.info("Created project: name='%s', directory='%s'", name, directory)
        self.refresh_list()
        dialog.accept()

    def get_selected_project_id(self):
        item = self.project_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def open_selected_project(self):
        pid = self.get_selected_project_id()
        if pid:
            logger.info("Opening project via button: project_id=%s", pid)
            self.open_project_by_id(pid)

    def open_project(self, item):
        pid = item.data(Qt.UserRole)
        logger.info("Opening project via double-click: project_id=%s", pid)
        self.open_project_by_id(pid)

    def open_project_by_id(self, project_id):
        project = self.repo.get(project_id)
        if project:
            logger.info("Opened project: id=%s, name='%s'", project_id, project.name)
            from app.ui.generation_screen import GenerationScreen
            if "generation" not in self.main_window.screens:
                self.main_window.register_screen("generation", GenerationScreen(self.main_window, project))
            self.main_window.navigate_to("generation")

    def delete_selected_project(self):
        pid = self.get_selected_project_id()
        if pid:
            project = self.repo.get(pid)
            name = project.name if project else "unknown"
            reply = QMessageBox.question(self, "Confirm Delete", "Delete this project? This cannot be undone.",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.repo.delete(pid)
                self.session.commit()
                logger.info("Deleted project: id=%s, name='%s'", pid, name)
                self.refresh_list()
