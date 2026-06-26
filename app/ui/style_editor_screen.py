import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFormLayout, QDoubleSpinBox, QSpinBox,
    QComboBox, QMessageBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt

from app.services.style_service import StyleService

logger = logging.getLogger(__name__)


class StyleEditorScreen(QWidget):
    def __init__(self, main_window, project, edit_profile_id=None):
        super().__init__()
        self.main_window = main_window
        self.project = project
        self._edit_profile_id = edit_profile_id
        self.session = main_window.app_instance.track_session(main_window.app_instance.get_db().get_session())
        self.style_service = StyleService(self.session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        mode = "Edit" if edit_profile_id else "New"
        title = QLabel(f"{mode} Style Profile — {project.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['Custom', 'Sci-Fi', 'Realistic', 'Cartoon'])
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        layout.addWidget(self.preset_combo)

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

        if self._edit_profile_id:
            self._load_profile(self._edit_profile_id)

    PRESETS = {
        'Sci-Fi': {
            'name': 'sci_fi',
            'base_prompt': 'sci-fi, futuristic, cyberpunk, neon lights, metallic textures, holographic displays, sleek',
            'negative_prompt': 'organic, fantasy, medieval, rustic, low quality, blurry, deformed, sketch',
            'palette': 'neon blues, purples, cold metallics, holographic teals, electric magenta',
            'cfg_scale': 8.5,
            'steps': 28,
            'sampler': 'EulerDiscreteScheduler',
            'seed_strategy': 'random',
        },
        'Realistic': {
            'name': 'realistic',
            'base_prompt': 'photorealistic, highly detailed, 4k, realistic textures, PBR materials, game-ready, subsurface scattering',
            'negative_prompt': 'cartoon, stylized, low quality, blurry, deformed, sketch, cell shaded, flat colors',
            'palette': 'natural earth tones, realistic PBR textures, physically based materials',
            'cfg_scale': 7.0,
            'steps': 30,
            'sampler': 'DPMSolverMultistepScheduler',
            'seed_strategy': 'random',
        },
        'Cartoon': {
            'name': 'cartoon',
            'base_prompt': 'cartoon, cel-shaded, vibrant, stylized, bold outlines, flat colors, toon shading, game asset',
            'negative_prompt': 'photorealistic, grimdark, horror, low quality, blurry, deformed, realistic textures',
            'palette': 'bright, saturated, primary colors, playful palette',
            'cfg_scale': 9.0,
            'steps': 20,
            'sampler': 'DDIMScheduler',
            'seed_strategy': 'random',
        },
    }

    def _apply_preset(self, preset_name):
        if preset_name not in self.PRESETS:
            return
        p = self.PRESETS[preset_name]
        self.name_input.setText(p['name'])
        self.base_prompt.setPlainText(p['base_prompt'])
        self.negative_prompt.setPlainText(p['negative_prompt'])
        self.palette.setText(p['palette'])
        self.cfg_scale.setValue(p['cfg_scale'])
        self.steps.setValue(p['steps'])
        idx = self.sampler.findText(p['sampler'])
        if idx >= 0:
            self.sampler.setCurrentIndex(idx)
        idx = self.seed_strategy.findText(p['seed_strategy'])
        if idx >= 0:
            self.seed_strategy.setCurrentIndex(idx)

    def _load_profile(self, profile_id):
        profile = self.style_service.get_style_profile(profile_id)
        if profile:
            self.name_input.setText(profile.name)
            self.base_prompt.setPlainText(profile.base_prompt or '')
            self.negative_prompt.setPlainText(profile.negative_prompt or '')
            self.palette.setText(profile.palette_description or '')
            self.cfg_scale.setValue(profile.cfg_scale or 7.5)
            self.steps.setValue(profile.steps or 25)
            idx = self.sampler.findText(profile.sampler or 'DPMSolverMultistepScheduler')
            if idx >= 0:
                self.sampler.setCurrentIndex(idx)
            idx = self.seed_strategy.findText(profile.seed_strategy or 'random')
            if idx >= 0:
                self.seed_strategy.setCurrentIndex(idx)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Profile")
        save_btn.clicked.connect(self.save_profile)
        test_btn = QPushButton("Test Generation")
        test_btn.clicked.connect(self.test_generation)
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to('generation'))
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.clicked.connect(lambda: self.main_window.navigate_to('dashboard'))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(dashboard_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def save_profile(self):
        name = self.name_input.text().strip() or 'Untitled Style'
        base = self.base_prompt.toPlainText().strip()
        neg = self.negative_prompt.toPlainText().strip()
        palette = self.palette.text().strip()
        cfg = self.cfg_scale.value()
        steps = self.steps.value()
        sampler = self.sampler.currentText()
        seed = self.seed_strategy.currentText()

        if self._edit_profile_id:
            profile = self.style_service.update_style_profile(
                self._edit_profile_id,
                name=name, base_prompt=base, negative_prompt=neg,
                palette_description=palette, cfg_scale=cfg, steps=steps,
                sampler=sampler, seed_strategy=seed,
            )
            action = "updated"
        else:
            profile = self.style_service.create_style_profile(
                name=name, base_prompt=base, negative_prompt=neg,
                palette_description=palette, cfg_scale=cfg, steps=steps,
                sampler=sampler, seed_strategy=seed,
            )
            action = "created"
            if self.project.style_profile_id is None:
                from app.storage.project_repo import ProjectRepo
                repo = ProjectRepo(self.session)
                repo.update(self.project.project_id, style_profile_id=profile.style_profile_id)
                self.session.commit()
                logger.info("Linked style profile '%s' (id=%s) to project '%s'", profile.name, profile.style_profile_id, self.project.name)
        self.session.commit()
        logger.info("Style profile %s: name='%s'", action, profile.name)
        QMessageBox.information(self, "Success", f"Style profile '{profile.name}' {action}!")

    def test_generation(self):
        logger.info("Test generation requested with current style profile for project='%s'", self.project.name)
        from app.utils.config import get_app_config
        model_manager = self.main_window.app_instance.model_manager
        config = get_app_config()
        try:
            model = model_manager.load_model('sd15')
            if model is None:
                QMessageBox.critical(self, "Error", "SD model not loaded.")
                return
            base = self.base_prompt.toPlainText().strip() or 'a game asset'
            neg = self.negative_prompt.toPlainText().strip()
            from diffusers import DPMSolverMultistepScheduler
            model.scheduler = DPMSolverMultistepScheduler.from_config(model.scheduler.config)
            result = model(
                prompt=base,
                negative_prompt=neg if neg else None,
                num_inference_steps=self.steps.value(),
                guidance_scale=self.cfg_scale.value(),
                width=config.get('default_output_resolution', 512),
                height=config.get('default_output_resolution', 512),
            ).images[0]
            preview_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'model_cache', '_preview')
            os.makedirs(preview_dir, exist_ok=True)
            preview_path = os.path.join(preview_dir, f'test_{self.name_input.text().strip() or "style"}.png')
            result.save(preview_path)
            logger.info("Test generation succeeded — saved to %s", preview_path)
            QMessageBox.information(self, "Test Complete", f"Test image saved to:\n{preview_path}")
        except Exception as e:
            logger.exception("Test generation failed: %s", e)
            QMessageBox.critical(self, "Test Failed", str(e))
