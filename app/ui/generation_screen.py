import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFormLayout, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QMessageBox, QGroupBox,
    QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt

from app.services.generation_service import GenerationService
from app.services.style_service import StyleService
from app.workflows.progress_tracker import ProgressTracker
from app.workflows.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class GenerationScreen(QWidget):
    def __init__(self, main_window, project):
        super().__init__()
        self.main_window = main_window
        self.project = project
        app = main_window.app_instance
        self.session = app.track_session(app.get_db().get_session())
        self.model_manager = app.model_manager
        self.gen_service = GenerationService(self.session, self.model_manager)
        self.style_service = StyleService(self.session)
        self.progress_tracker = ProgressTracker()
        self.progress_tracker.progress_updated.connect(self._on_progress)
        self.progress_tracker.step_changed.connect(self._on_step_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Generate Assets — {project.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        form_layout = QHBoxLayout()

        left = QWidget()
        left_form = QFormLayout(left)

        self.category = QComboBox()
        self.category.addItems(['character', 'prop', 'weapon', 'building', 'environment', 'background', 'tileset', 'effect'])
        left_form.addRow("Asset Category:", self.category)

        self.model_combo = QComboBox()
        self.model_combo.addItem('SD 1.5 (HF)', 'sd15')
        self.model_combo.addItem('DreamShaper', 'dreamshaper')
        self.model_combo.addItem('EpicRealism', 'epicrealism')
        self.model_combo.addItem('RealCartoon3D', 'realcartoon3d')
        self.model_combo.addItem('RevAnimated', 'revanimated')
        self.model_combo.addItem('Juggernaut', 'juggernaut')
        left_form.addRow("SD Model:", self.model_combo)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Describe the asset...")
        self.prompt_input.setMaximumHeight(100)
        left_form.addRow("Prompt:", self.prompt_input)

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 10)
        self.quantity.setValue(1)
        left_form.addRow("Quantity:", self.quantity)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        left_form.addRow(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        left_form.addRow(self.status_label)

        form_layout.addWidget(left, 2)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        style_title = QLabel("Style Profiles")
        style_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(style_title)

        self.style_list = QListWidget()
        self.style_list.setMinimumWidth(250)
        self.refresh_styles()
        right_layout.addWidget(self.style_list)

        form_layout.addWidget(right, 1)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("Generate")
        gen_btn.setStyleSheet("""
            QPushButton { background-color: #4a9eff; color: #fff; border: none; padding: 10px 30px; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #3a8eef; }
            QPushButton:disabled { background-color: #555; }
        """)
        gen_btn.clicked.connect(self.generate)
        self.gen_btn = gen_btn

        pipeline_btn = QPushButton("Run Pipeline")
        pipeline_btn.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: #fff; border: none; padding: 10px 30px; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:disabled { background-color: #555; }
        """)
        pipeline_btn.clicked.connect(self.run_pipeline)
        self.pipeline_btn = pipeline_btn

        style_btn = QPushButton("Edit Style Profile")
        style_btn.clicked.connect(self.edit_style)
        review_btn = QPushButton("Review Assets")
        review_btn.clicked.connect(self.go_review)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.go_export)
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.clicked.connect(lambda: self.main_window.navigate_to('dashboard'))

        btn_layout.addWidget(gen_btn)
        btn_layout.addWidget(pipeline_btn)
        btn_layout.addWidget(style_btn)
        btn_layout.addWidget(review_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(dashboard_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_progress(self, value, message):
        self.progress_bar.setValue(int(value))
        if message:
            self.status_label.setText(message)

    def _on_step_changed(self, step_name):
        self.status_label.setText(step_name)

    def _selected_model_key(self):
        return self.model_combo.currentData()

    def run_pipeline(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            logger.warning("Pipeline aborted: prompt is empty")
            QMessageBox.warning(self, "Error", "Please enter a prompt.")
            return

        asset_type = self.category.currentText()
        quantity = self.quantity.value()
        profile = self.get_selected_profile()
        profile_name = profile.name if profile else "None"
        model_key = self._selected_model_key()

        logger.info(
            "Pipeline requested: prompt='%s', type='%s', quantity=%d, style_profile='%s', model='%s', project='%s'",
            prompt, asset_type, quantity, profile_name, model_key, self.project.name
        )

        self.gen_btn.setEnabled(False)
        self.pipeline_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting pipeline...")
        self.main_window.show_blocking_overlay("Pipeline running...")

        engine = WorkflowEngine(self.session, self.model_manager)
        try:
            engine.run_pipeline(
                project=self.project,
                prompt=prompt,
                asset_type=asset_type,
                style_profile=profile,
                quantity=quantity,
                model_key=model_key,
                enable_animation=None,
                progress_callback=self.progress_tracker,
            )
            self.session.commit()
            self.progress_bar.setValue(100)
            self.status_label.setText("Pipeline complete!")
            logger.info("Pipeline completed for project='%s'", self.project.name)
            from app.ui.review_screen import ReviewScreen
            self.main_window.register_screen("review", ReviewScreen(self.main_window, self.project))
            self.main_window.navigate_to("review")
        except Exception as e:
            self.status_label.setText(f"Pipeline failed: {e}")
            logger.exception("Pipeline failed for project='%s': %s", self.project.name, e)
            QMessageBox.critical(self, "Pipeline Failed", str(e))
        finally:
            self.main_window.hide_blocking_overlay()
            self.gen_btn.setEnabled(True)
            self.pipeline_btn.setEnabled(True)

    def refresh_styles(self):
        self.style_list.clear()
        profiles = self.style_service.list_style_profiles()
        for p in profiles:
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, p.style_profile_id)
            self.style_list.addItem(item)

    def get_selected_profile(self):
        item = self.style_list.currentItem()
        if item:
            return self.style_service.get_style_profile(item.data(Qt.UserRole))
        return None

    def generate(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            logger.warning("Generation aborted: prompt is empty")
            QMessageBox.warning(self, "Error", "Please enter a prompt.")
            return

        asset_type = self.category.currentText()
        quantity = self.quantity.value()
        profile = self.get_selected_profile()
        profile_name = profile.name if profile else "None"
        model_key = self._selected_model_key()

        logger.info(
            "Generation requested: prompt='%s', type='%s', quantity=%d, style_profile='%s', model='%s', project='%s'",
            prompt, asset_type, quantity, profile_name, model_key, self.project.name
        )

        self.gen_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_tracker.set_step('generation')
        self.progress_tracker.set_progress(0, 'Generating...')

        try:
            self.progress_tracker.set_progress(10, 'Running SD 1.5 inference...')
            assets = self.gen_service.generate_asset(
                self.project, prompt, asset_type, profile, quantity, model_key=model_key,
            )
            self.session.commit()
            self.progress_tracker.set_progress(100, f'Generated {len(assets)} asset(s)')
            logger.info(
                "Generation succeeded: %d asset(s) created for project='%s'",
                len(assets), self.project.name
            )
            from app.ui.review_screen import ReviewScreen
            self.main_window.register_screen("review", ReviewScreen(self.main_window, self.project))
            self.main_window.navigate_to("review")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            logger.exception("Generation failed for project='%s': %s", self.project.name, e)
            QMessageBox.critical(self, "Generation Failed", str(e))
        finally:
            self.gen_btn.setEnabled(True)

    def edit_style(self):
        logger.info("Navigating to style editor, project='%s'", self.project.name)
        profile = self.get_selected_profile()
        profile_id = profile.style_profile_id if profile else None
        from app.ui.style_editor_screen import StyleEditorScreen
        self.main_window.register_screen("style_editor", StyleEditorScreen(self.main_window, self.project, edit_profile_id=profile_id))
        self.main_window.navigate_to("style_editor")

    def go_review(self):
        logger.info("Navigating to review, project='%s'", self.project.name)
        from app.ui.review_screen import ReviewScreen
        self.main_window.register_screen("review", ReviewScreen(self.main_window, self.project))
        self.main_window.navigate_to("review")

    def go_export(self):
        logger.info("Navigating to export, project='%s'", self.project.name)
        from app.ui.export_screen import ExportScreen
        self.main_window.register_screen("export", ExportScreen(self.main_window, self.project))
        self.main_window.navigate_to("export")
