import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFormLayout, QDoubleSpinBox, QSpinBox,
    QComboBox, QMessageBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt

from app.services.style_service import StyleService

logger = logging.getLogger(__name__)


class StyleEditorScreen(QWidget):
    def __init__(self, main_window, project):
        super().__init__()
        self.main_window = main_window
        self.project = project
        self.session = main_window.app_instance.get_db().get_session()
        self.style_service = StyleService(self.session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Style Profile — {project.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form = QFormLayout(scroll_widget)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., storybook_fantasy")
        form.addRow("Style Name:", self.name_input)

        self.base_prompt = QTextEdit()
        self.base_prompt.setPlaceholderText("e.g., storybook fantasy, hand painted, soft warm palette")
        self.base_prompt.setMaximumHeight(80)
        form.addRow("Base Prompt:", self.base_prompt)

        self.negative_prompt = QTextEdit()
        self.negative_prompt.setPlaceholderText("e.g., ugly, blurry, low quality, deformed")
        self.negative_prompt.setMaximumHeight(80)
        form.addRow("Negative Prompt:", self.negative_prompt)

        self.palette = QLineEdit()
        self.palette.setPlaceholderText("e.g., warm earth tones, soft greens")
        form.addRow("Color Palette:", self.palette)

        self.cfg_scale = QDoubleSpinBox()
        self.cfg_scale.setRange(1.0, 30.0)
        self.cfg_scale.setValue(7.5)
        self.cfg_scale.setSingleStep(0.5)
        form.addRow("CFG Scale:", self.cfg_scale)

        self.steps = QSpinBox()
        self.steps.setRange(1, 100)
        self.steps.setValue(25)
        form.addRow("Steps:", self.steps)

        self.sampler = QComboBox()
        self.sampler.addItems(['DPMSolverMultistepScheduler', 'EulerDiscreteScheduler', 'DDIMScheduler', 'PNDMScheduler'])
        form.addRow("Sampler:", self.sampler)

        self.seed_strategy = QComboBox()
        self.seed_strategy.addItems(['random', 'fixed'])
        form.addRow("Seed Strategy:", self.seed_strategy)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Profile")
        save_btn.clicked.connect(self.save_profile)
        test_btn = QPushButton("Test Generation")
        test_btn.clicked.connect(self.test_generation)
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to('generation'))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def save_profile(self):
        profile = self.style_service.create_style_profile(
            name=self.name_input.text().strip() or 'Untitled Style',
            base_prompt=self.base_prompt.toPlainText().strip(),
            negative_prompt=self.negative_prompt.toPlainText().strip(),
            palette_description=self.palette.text().strip(),
            cfg_scale=self.cfg_scale.value(),
            steps=self.steps.value(),
            sampler=self.sampler.currentText(),
            seed_strategy=self.seed_strategy.currentText(),
        )
        self.session.commit()
        if self.project.style_profile_id is None:
            from app.storage.project_repo import ProjectRepo
            repo = ProjectRepo(self.session)
            repo.update(self.project.project_id, style_profile_id=profile.style_profile_id)
            self.session.commit()
            logger.info("Linked style profile '%s' (id=%s) to project '%s'", profile.name, profile.style_profile_id, self.project.name)
        logger.info("Style profile saved: name='%s', base_prompt='%s', negative_prompt='%s', palette='%s', cfg=%.1f, steps=%d, sampler='%s', seed='%s'",
            profile.name,
            self.base_prompt.toPlainText().strip(),
            self.negative_prompt.toPlainText().strip(),
            self.palette.text().strip(),
            self.cfg_scale.value(),
            self.steps.value(),
            self.sampler.currentText(),
            self.seed_strategy.currentText(),
        )
        QMessageBox.information(self, "Success", f"Style profile '{profile.name}' saved!")

    def test_generation(self):
        logger.info("Test generation requested with current style profile for project='%s'", self.project.name)
        QMessageBox.information(self, "Test", "Connect generation service to test with this profile.")
