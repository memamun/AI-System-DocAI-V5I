"""
AI-System-DocAI - Qt Dialogs for LLM Configuration
Provides configuration dialogs for different LLM backends
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QCheckBox,
                             QTextEdit, QGroupBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
import os


class BaseLLMDialog(QDialog):
    """Base class for LLM configuration dialogs"""

    def __init__(self, parent=None, title="LLM Configuration"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 400)

        self.values_cache = {}

    def values(self):
        """Return dialog values - override in subclasses"""
        return "", "", "", False


class OpenAIDialog(BaseLLMDialog):
    """OpenAI API configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent, "OpenAI API Configuration")

        layout = QVBoxLayout(self)

        # API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        if os.getenv("OPENAI_API_KEY"):
            self.api_key.setText(os.getenv("OPENAI_API_KEY"))
        key_layout.addWidget(self.api_key)
        layout.addLayout(key_layout)

        # Base URL (optional)
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Base URL (optional):"))
        self.base_url = QLineEdit()
        self.base_url.setPlaceholderText("https://api.openai.com/v1")
        if os.getenv("OPENAI_BASE_URL"):
            self.base_url.setText(os.getenv("OPENAI_BASE_URL"))
        url_layout.addWidget(self.base_url)
        layout.addLayout(url_layout)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model = QComboBox()
        self.model.addItems([
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ])
        current_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.model.setCurrentText(current_model)
        model_layout.addWidget(self.model)
        layout.addLayout(model_layout)

        # Remember checkbox
        self.remember = QCheckBox("Remember these settings")
        layout.addWidget(self.remember)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def values(self):
        """Return (api_key, base_url, model, remember)"""
        return (
            self.api_key.text().strip(),
            self.base_url.text().strip(),
            self.model.currentText(),
            self.remember.isChecked()
        )


class AnthropicDialog(BaseLLMDialog):
    """Anthropic Claude configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent, "Anthropic Claude Configuration")

        layout = QVBoxLayout(self)

        # API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        if os.getenv("ANTHROPIC_API_KEY"):
            self.api_key.setText(os.getenv("ANTHROPIC_API_KEY"))
        key_layout.addWidget(self.api_key)
        layout.addLayout(key_layout)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model = QComboBox()
        self.model.addItems([
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ])
        current_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.model.setCurrentText(current_model)
        model_layout.addWidget(self.model)
        layout.addLayout(model_layout)

        # Remember checkbox
        self.remember = QCheckBox("Remember these settings")
        layout.addWidget(self.remember)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def values(self):
        """Return (api_key, base_url, model, remember)"""
        return (
            self.api_key.text().strip(),
            "",  # No base URL for Anthropic
            self.model.currentText(),
            self.remember.isChecked()
        )


class GeminiDialog(BaseLLMDialog):
    """Google Gemini configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent, "Google Gemini Configuration")

        layout = QVBoxLayout(self)

        # API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        if os.getenv("GEMINI_API_KEY"):
            self.api_key.setText(os.getenv("GEMINI_API_KEY"))
        key_layout.addWidget(self.api_key)
        layout.addLayout(key_layout)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model = QComboBox()
        self.model.addItems([
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro"
        ])
        current_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model.setCurrentText(current_model)
        model_layout.addWidget(self.model)
        layout.addLayout(model_layout)

        # Remember checkbox
        self.remember = QCheckBox("Remember these settings")
        layout.addWidget(self.remember)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def values(self):
        """Return (api_key, base_url, model, remember)"""
        return (
            self.api_key.text().strip(),
            "",  # No base URL for Gemini
            self.model.currentText(),
            self.remember.isChecked()
        )


class OllamaDialog(BaseLLMDialog):
    """Ollama configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent, "Ollama Configuration")

        layout = QVBoxLayout(self)

        # Base URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Base URL:"))
        self.base_url = QLineEdit()
        self.base_url.setPlaceholderText("http://localhost:11434")
        current_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url.setText(current_url)
        url_layout.addWidget(self.base_url)
        layout.addLayout(url_layout)

        # Model name
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model = QLineEdit()
        self.model.setPlaceholderText("llama2, mistral, codellama, etc.")
        current_model = os.getenv("OLLAMA_MODEL", "llama2")
        self.model.setText(current_model)
        model_layout.addWidget(self.model)
        layout.addLayout(model_layout)

        # Instructions
        instructions = QLabel(
            "Make sure Ollama is running locally.\n"
            "You can start it with: 'ollama serve'"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Remember checkbox
        self.remember = QCheckBox("Remember these settings")
        layout.addWidget(self.remember)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def values(self):
        """Return (api_key, base_url, model, remember)"""
        return (
            "",  # No API key for Ollama
            self.base_url.text().strip(),
            self.model.text().strip(),
            self.remember.isChecked()
        )


class HuggingFaceDialog(BaseLLMDialog):
    """HuggingFace Local Model configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent, "HuggingFace Local Model Configuration")

        layout = QVBoxLayout(self)

        # Model ID
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model ID:"))
        self.model_id = QLineEdit()
        self.model_id.setPlaceholderText("microsoft/DialoGPT-medium, facebook/blenderbot-400M-distill, etc.")
        current_model = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")
        self.model_id.setText(current_model)
        model_layout.addWidget(self.model_id)
        layout.addLayout(model_layout)

        # Instructions
        instructions = QLabel(
            "Enter a HuggingFace model ID.\n"
            "Popular choices:\n"
            "• microsoft/DialoGPT-medium\n"
            "• facebook/blenderbot-400M-distill\n"
            "• microsoft/DialoGPT-small"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Remember checkbox
        self.remember = QCheckBox("Remember these settings")
        layout.addWidget(self.remember)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def values(self):
        """Return (api_key, base_url, model, remember)"""
        return (
            "",  # No API key for HF local
            "",  # No base URL
            self.model_id.text().strip(),
            self.remember.isChecked()
        )


class LlamaCppDialog(BaseLLMDialog):
    """LlamaCpp configuration dialog"""

    def __init__(self, parent=None):
        super().__init__(parent, "LlamaCpp Configuration")

        layout = QVBoxLayout(self)

        # Model path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Model Path:"))
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("path/to/model.gguf")
        if os.getenv("LLAMA_CPP_MODEL_PATH"):
            self.model_path.setText(os.getenv("LLAMA_CPP_MODEL_PATH"))
        path_layout.addWidget(self.model_path)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_model)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)

        # Instructions
        instructions = QLabel(
            "Select a GGUF model file.\n"
            "You can download models from:\n"
            "• https://huggingface.co/models (search for GGUF)\n"
            "• https://github.com/ggerganov/llama.cpp (releases)"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Remember checkbox
        self.remember = QCheckBox("Remember these settings")
        layout.addWidget(self.remember)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def browse_model(self):
        """Browse for model file"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select GGUF Model",
            "",
            "GGUF files (*.gguf);;All files (*.*)"
        )
        if filename:
            self.model_path.setText(filename)

    def values(self):
        """Return (api_key, base_url, model, remember)"""
        return (
            "",  # No API key
            "",  # No base URL
            self.model_path.text().strip(),
            self.remember.isChecked()
        )

