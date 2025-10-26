"""
Enhanced UI for AI-System-DocAI V5I
Main and Diagnostics tabs with GPU status, model selection, and JSON reasoning display
"""
from __future__ import annotations
import os
import sys
import json
import platform
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QProgressBar, QComboBox, QMessageBox, QLineEdit, QTextBrowser,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox, QGroupBox, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView, QScrollArea, QFrame,
    QRadioButton, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices, QFont, QIcon, QSyntaxHighlighter, QTextCharFormat, QColor

from indexer import Indexer
from retrieval import Retriever
from llm import create_llm, get_available_backends
from reasoning import ReasoningEngine, ReasoningResult
from config import config_manager, EMBED_MODELS, INDEX_TYPES, DEFAULTS, IndexConfig
from enterprise_logging import enterprise_logger, log_info, log_warning, log_error, log_operation
from index_manager import IndexManager

# Import thread classes from original app
# from app_qt import AskThread  # Using new reasoning engine instead

class JSONHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for JSON display"""
    
    def __init__(self, document):
        super().__init__(document)
        self.setup_formats()
    
    def setup_formats(self):
        """Setup syntax highlighting formats"""
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(127, 0, 85))
        keyword_format.setFontWeight(700)
        self.keyword_format = keyword_format
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(0, 128, 0))
        self.string_format = string_format
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 0, 255))
        self.number_format = number_format
        
        # Braces
        brace_format = QTextCharFormat()
        brace_format.setForeground(QColor(0, 0, 0))
        brace_format.setFontWeight(700)
        self.brace_format = brace_format
    
    def highlightBlock(self, text):
        """Highlight JSON syntax"""
        import re
        
        # Keywords
        keyword_pattern = r'\b(true|false|null)\b'
        for match in re.finditer(keyword_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)
        
        # Strings
        string_pattern = r'"[^"\\]*(\\.[^"\\]*)*"'
        for match in re.finditer(string_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # Numbers
        number_pattern = r'\b\d+\.?\d*\b'
        for match in re.finditer(number_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)
        
        # Braces
        brace_pattern = r'[{}[\]]'
        for match in re.finditer(brace_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.brace_format)

class EnterpriseIndexThread(QThread):
    """Enhanced index thread with config_manager path"""
    status = pyqtSignal(str)
    progress = pyqtSignal(int)
    done = pyqtSignal(int, int)
    
    def __init__(self, folder: Path, cfg: IndexConfig, index_dir: Path):
        super().__init__()
        self.folder = folder
        self.cfg = cfg
        self.index_dir = index_dir
        self._cancel = False
    
    def cancel(self):
        self._cancel = True
    
    def run(self):
        def should_cancel():
            return self._cancel
        
        idx = Indexer(self.index_dir, self.cfg, 
                     on_status=self.status.emit, 
                     on_progress=self.progress.emit, 
                     should_cancel=should_cancel)
        files, vecs = idx.build(self.folder)
        self.done.emit(files, vecs)

class AskThread(QThread):
    """Thread for asking questions and getting answers with reasoning."""
    ready = pyqtSignal(ReasoningResult)
    error = pyqtSignal(str)

    def __init__(self, query: str, retriever: Retriever, llm_backend: Any): # llm_backend is now BaseLLM
        super().__init__()
        self.query = query
        self.retriever = retriever
        self.llm_backend = llm_backend

    def run(self):
        try:
            # 1. Retrieve relevant snippets (returns List[Tuple[int, float]])
            hits = self.retriever.search(self.query, k=config_manager.config.retrieval.top_k)
            
            # 2. Convert hits to context format using the gather method
            context = self.retriever.gather(hits)
            
            # 3. Perform reasoning
            reasoning_engine = ReasoningEngine()
            result = reasoning_engine.process_query(
                query=self.query,
                context=context,
                llm_backend=self.llm_backend,
                device_string=get_device_string()
            )
            
            self.ready.emit(result)
        except Exception as e:
            log_error("Answer Generation Failed", e)
            self.error.emit(str(e))

class StreamingAskThread(QThread):
    """Thread for streaming question answering with live thinking process."""
    reasoning_update = pyqtSignal(object)  # StreamingReasoningResult
    error = pyqtSignal(str)

    def __init__(self, query: str, retriever: Retriever, llm_backend: Any):
        super().__init__()
        self.query = query
        self.retriever = retriever
        self.llm_backend = llm_backend

    def run(self):
        try:
            # Import here to avoid circular imports
            from streaming_reasoning import StreamingReasoningEngine, StreamingReasoningResult
            
            # 1. Retrieve relevant snippets
            hits = self.retriever.search(self.query, k=config_manager.config.retrieval.top_k)
            context = self.retriever.gather(hits)
            
            # 2. Create streaming reasoning engine
            reasoning_engine = StreamingReasoningEngine(self.llm_backend)
            
            # 3. Stream the reasoning process
            for result in reasoning_engine.process_query_stream(self.query, context):
                self.reasoning_update.emit(result)
                
                # Small delay to make streaming visible
                import time
                time.sleep(0.1)  # Increased delay for better visibility
                
        except Exception as e:
            log_error("Streaming Answer Generation Failed", e)
            self.error.emit(str(e))

class DiagnosticsWidget(QWidget):
    """Enhanced diagnostics tab with GPU information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_info()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_system_info)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create splitter for main content
        splitter = QSplitter()
        layout.addWidget(splitter)
        
        # Left panel - System Info
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # System Information Group
        sys_group = QGroupBox("System Information")
        sys_layout = QGridLayout(sys_group)
        
        self.sys_labels = {}
        sys_info = [
            ("OS", "os"),
            ("OS Version", "os_version"),
            ("Architecture", "architecture"),
            ("Processor", "processor"),
            ("Python Version", "python_version"),
            ("RAM Total", "ram_total"),
            ("RAM Available", "ram_available"),
            ("RAM Usage", "ram_usage"),
            ("CPU Cores", "cpu_cores"),
            ("CPU Usage", "cpu_usage"),
            ("Disk Space", "disk_space")
        ]
        
        for i, (label, key) in enumerate(sys_info):
            sys_layout.addWidget(QLabel(f"{label}:"), i, 0)
            value_label = QLabel("Loading...")
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            sys_layout.addWidget(value_label, i, 1)
            self.sys_labels[key] = value_label
        
        left_layout.addWidget(sys_group)
        
        # GPU Information Group
        gpu_group = QGroupBox("GPU Information")
        gpu_layout = QGridLayout(gpu_group)
        
        self.gpu_labels = {}
        gpu_info = [
            ("GPU Status", "gpu_status"),
            ("GPU Name", "gpu_name"),
            ("VRAM", "vram"),
            ("CUDA Version", "cuda_version"),
            ("Device String", "device_string")
        ]
        
        for i, (label, key) in enumerate(gpu_info):
            gpu_layout.addWidget(QLabel(f"{label}:"), i, 0)
            value_label = QLabel("Loading...")
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            gpu_layout.addWidget(value_label, i, 1)
            self.gpu_labels[key] = value_label
        
        left_layout.addWidget(gpu_group)
        
        # Model Information Group
        model_group = QGroupBox("Model Information")
        model_layout = QGridLayout(model_group)
        
        self.model_labels = {}
        model_info = [
            ("LLM Backend", "llm_backend"),
            ("Embedding Model", "embed_model"),
            ("Index Status", "index_status"),
            ("Index Vectors", "index_vectors"),
            ("Available Backends", "available_backends")
        ]
        
        for i, (label, key) in enumerate(model_info):
            model_layout.addWidget(QLabel(f"{label}:"), i, 0)
            value_label = QLabel("Loading...")
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            model_layout.addWidget(value_label, i, 1)
            self.model_labels[key] = value_label
        
        left_layout.addWidget(model_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_info)
        button_layout.addWidget(self.refresh_btn)
        
        self.reveal_logs_btn = QPushButton("Reveal Logs")
        self.reveal_logs_btn.clicked.connect(self.reveal_logs)
        button_layout.addWidget(self.reveal_logs_btn)
        
        self.view_logs_btn = QPushButton("View Logs")
        self.view_logs_btn.clicked.connect(self.view_logs)
        button_layout.addWidget(self.view_logs_btn)
        
        left_layout.addLayout(button_layout)
        left_layout.addStretch()
        
        # Right panel - Logs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        logs_group = QGroupBox("System Logs")
        logs_layout = QVBoxLayout(logs_group)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 9))
        logs_layout.addWidget(self.logs_text)
        
        right_layout.addWidget(logs_group)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
    
    def refresh_info(self):
        """Refresh all system information"""
        self.refresh_system_info()
        self.refresh_gpu_info()
        self.refresh_model_info()
        self.refresh_logs()
    
    def refresh_system_info(self):
        """Refresh system information"""
        try:
            # OS Information
            self.sys_labels["os"].setText(platform.system())
            self.sys_labels["os_version"].setText(platform.version())
            self.sys_labels["architecture"].setText(platform.architecture()[0])
            self.sys_labels["processor"].setText(platform.processor())
            self.sys_labels["python_version"].setText(platform.python_version())
            
            # Memory Information
            memory = psutil.virtual_memory()
            self.sys_labels["ram_total"].setText(f"{memory.total / (1024**3):.1f} GB")
            self.sys_labels["ram_available"].setText(f"{memory.available / (1024**3):.1f} GB")
            self.sys_labels["ram_usage"].setText(f"{memory.percent:.1f}%")
            
            # CPU Information
            self.sys_labels["cpu_cores"].setText(f"{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
            self.sys_labels["cpu_usage"].setText(f"{psutil.cpu_percent(interval=1):.1f}%")
            
            # Disk Information
            disk = psutil.disk_usage('/')
            self.sys_labels["disk_space"].setText(f"{disk.free / (1024**3):.1f} GB free")
            
        except Exception as e:
            log_error(f"Failed to refresh system info: {e}")
    
    def refresh_gpu_info(self):
        """Refresh device information (CPU-only)"""
        try:
            # CPU-only mode
            self.gpu_labels["gpu_status"].setText("CPU Mode")
            self.gpu_labels["gpu_status"].setStyleSheet("font-weight: bold; color: #3498db;")
            self.gpu_labels["gpu_name"].setText("N/A (CPU-only)")
            self.gpu_labels["vram"].setText("N/A")
            self.gpu_labels["cuda_version"].setText("N/A")
            self.gpu_labels["device_string"].setText("CPU")
            
        except Exception as e:
            log_error(f"Failed to refresh device info: {e}")
    
    def refresh_model_info(self):
        """Refresh model information"""
        try:
            # LLM Backend
            config = config_manager.config
            self.model_labels["llm_backend"].setText(config.llm.backend)
            
            # Embedding Model
            self.model_labels["embed_model"].setText(config.embeddings.model)
            
            # Index Status
            idx_path = config_manager.get_index_path() / "index.faiss"
            if idx_path.exists():
                try:
                    retriever = Retriever(config_manager.get_index_path())
                    info = retriever.get_index_info()
                    self.model_labels["index_status"].setText("Available")
                    self.model_labels["index_status"].setStyleSheet("font-weight: bold; color: #27ae60;")
                    self.model_labels["index_vectors"].setText(str(info["total_vectors"]))
                except Exception:
                    self.model_labels["index_status"].setText("Error")
                    self.model_labels["index_status"].setStyleSheet("font-weight: bold; color: #e74c3c;")
                    self.model_labels["index_vectors"].setText("N/A")
            else:
                self.model_labels["index_status"].setText("Not Found")
                self.model_labels["index_status"].setStyleSheet("font-weight: bold; color: #f39c12;")
                self.model_labels["index_vectors"].setText("N/A")
            
            # Available Backends
            backends = get_available_backends()
            self.model_labels["available_backends"].setText(", ".join(backends))
            
        except Exception as e:
            log_error(f"Failed to refresh model info: {e}")
    
    def refresh_logs(self):
        """Refresh log display"""
        try:
            logs_dir = config_manager.get_logs_path()
            if not logs_dir.exists():
                self.logs_text.setText("No logs directory found")
                return
            
            # Read recent log entries
            log_files = list(logs_dir.glob("*.log"))
            if not log_files:
                self.logs_text.setText("No log files found")
                return
            
            # Get the most recent log file
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # Read last 50 lines
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                self.logs_text.setText("".join(recent_lines))
            
        except Exception as e:
            self.logs_text.setText(f"Error reading logs: {e}")
    
    def reveal_logs(self):
        """Reveal logs directory in file explorer"""
        try:
            logs_dir = config_manager.get_logs_path()
            if logs_dir.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_dir)))
            else:
                QMessageBox.information(self, "Logs", "Logs directory not found")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open logs directory: {e}")
    
    def view_logs(self):
        """Open log viewer dialog"""
        try:
            logs_dir = config_manager.get_logs_path()
            if not logs_dir.exists():
                QMessageBox.information(self, "Logs", "Logs directory not found")
                return
            
            # Create log viewer dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Log Viewer")
            dialog.setModal(True)
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Log file selector
            file_layout = QHBoxLayout()
            file_layout.addWidget(QLabel("Log File:"))
            file_combo = QComboBox()
            log_files = list(logs_dir.glob("*.log"))
            for log_file in log_files:
                file_combo.addItem(log_file.name, str(log_file))
            file_layout.addWidget(file_combo)
            layout.addLayout(file_layout)
            
            # Log content
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setFont(QFont("Consolas", 9))
            layout.addWidget(log_text)
            
            def load_log():
                if file_combo.currentData():
                    with open(file_combo.currentData(), 'r', encoding='utf-8') as f:
                        log_text.setText(f.read())
            
            file_combo.currentTextChanged.connect(load_log)
            load_log()  # Load initial log
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open log viewer: {e}")

class EnterpriseApp(QWidget):
    """Main application window with enhanced features"""
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.retriever = None
        self.reasoning_engine = ReasoningEngine()
        self.index_manager = IndexManager()
        self.setup_ui()
        self.setup_initial_state()
        
        # Load saved LLM configuration
        self._load_llm_config()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("AI-System-DocAI V5I - Enterprise Edition")
        self.setGeometry(100, 100, 1200, 800)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Setup tabs
        self.setup_main_tab()
        self.setup_diagnostics_tab()
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.gpu_status_label = QLabel("")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.gpu_status_label)
        layout.addLayout(status_layout)
        
        # Update GPU status
        self.update_gpu_status()
    
    def setup_main_tab(self):
        """Setup the main tab with enhanced functionality"""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget for Main functionality
        main_tabs = QTabWidget()
        layout.addWidget(main_tabs)
        
        # Tab 1: Indexing
        self.setup_indexing_tab(main_tabs)
        
        # Tab 2: Chat
        self.setup_chat_tab(main_tabs)
        
        # Tab 3: Index Management
        self.setup_index_management_tab(main_tabs)
        
        self.tabs.addTab(main_widget, "Main")
    
    def setup_indexing_tab(self, parent_tabs):
        """Setup the indexing tab"""
        indexing_widget = QWidget()
        layout = QVBoxLayout(indexing_widget)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Folder:"))
        self.eFolder = QLineEdit()
        self.eFolder.setPlaceholderText("Select a folder to index...")
        folder_layout.addWidget(self.eFolder, 1)
        
        self.bPickFolder = QPushButton("Browse...")
        self.bPickFolder.clicked.connect(self.pick_folder)
        folder_layout.addWidget(self.bPickFolder)
        layout.addLayout(folder_layout)
        
        # Configuration options
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Embedding:"))
        self.cbEmbed = QComboBox()
        for key, value in EMBED_MODELS.items():
            self.cbEmbed.addItem(value["display"], key)
        config_layout.addWidget(self.cbEmbed)
        
        config_layout.addWidget(QLabel("Index:"))
        self.cbIndex = QComboBox()
        for key, label in INDEX_TYPES:
            self.cbIndex.addItem(label, key)
        config_layout.addWidget(self.cbIndex)
        layout.addLayout(config_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.bIndex = QPushButton("Build Index")
        self.bIndex.clicked.connect(self.start_index)
        button_layout.addWidget(self.bIndex)
        
        self.bCancel = QPushButton("Cancel")
        self.bCancel.clicked.connect(self.cancel_index)
        self.bCancel.setEnabled(False)
        button_layout.addWidget(self.bCancel)
        layout.addLayout(button_layout)
        
        # Progress bar
        self.prog = QProgressBar()
        self.prog.setValue(0)
        layout.addWidget(self.prog)
        
        # Log output
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log, 1)
        
        parent_tabs.addTab(indexing_widget, "Indexing")
    
    def setup_chat_tab(self, parent_tabs):
        """Setup the enhanced chat tab with JSON reasoning display"""
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        
        # Index status and reload
        status_layout = QHBoxLayout()
        self.lblIndex = QLabel(self.index_status_text())
        status_layout.addWidget(self.lblIndex)
        
        self.bReload = QPushButton("Reload Index")
        self.bReload.clicked.connect(self.reload_index)
        status_layout.addWidget(self.bReload)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # LLM configuration
        llm_layout = QHBoxLayout()
        llm_layout.addWidget(QLabel("LLM Backend:"))
        self.cbLLM = QComboBox()
        
        # Populate with available backends
        backends = get_available_backends()
        
        # Simple backend display names (CPU-only)
        backend_names = {
            "none": "No LLM (Citations Only)",
            "openai": "OpenAI / Compatible API",
            "anthropic": "Anthropic Claude",
            "gemini": "Google Gemini",
            "ollama": "Ollama (Local Server)",
            "hf_local": "HuggingFace Local",
            "llama_cpp": "LlamaCpp (GGUF)"
        }
        
        for backend in backends:
            display_name = backend_names.get(backend, backend)
            display_name += " (CPU)"
            self.cbLLM.addItem(display_name, backend)
        
        self.cbLLM.currentIndexChanged.connect(self.on_backend_change)
        llm_layout.addWidget(self.cbLLM)
        
        llm_layout.addWidget(QLabel("Model:"))
        self.eModelName = QLineEdit()
        self.eModelName.setPlaceholderText("Model name or path (e.g., gpt-4o-mini, Qwen, /path/to/model.gguf)")
        llm_layout.addWidget(self.eModelName, 1)
        
        self.bSetLLM = QPushButton("Apply")
        self.bSetLLM.clicked.connect(self.apply_llm)
        llm_layout.addWidget(self.bSetLLM)
        
        self.bConfigureLLM = QPushButton("Configure")
        self.bConfigureLLM.clicked.connect(self.configure_current_backend)
        llm_layout.addWidget(self.bConfigureLLM)
        
        layout.addLayout(llm_layout)
        
        # Chat input
        self.inp = QTextEdit()
        self.inp.setPlaceholderText("Type your question...")
        self.inp.setMaximumHeight(100)
        layout.addWidget(self.inp)
        
        # Ask button and streaming toggle
        ask_layout = QHBoxLayout()
        
        self.bAsk = QPushButton("Search and Answer")
        self.bAsk.clicked.connect(self.ask)
        ask_layout.addWidget(self.bAsk)
        
        # Streaming mode toggle
        self.streaming_mode = QCheckBox("Live Thinking")
        self.streaming_mode.setToolTip("Enable real-time streaming of reasoning process")
        self.streaming_mode.setChecked(True)  # Default to streaming mode
        ask_layout.addWidget(self.streaming_mode)
        
        layout.addLayout(ask_layout)
        
        # Output with JSON reasoning display
        output_layout = QHBoxLayout()
        
        # Left: Formatted answer
        self.out = QTextBrowser()
        self.out.setOpenExternalLinks(False)
        self.out.setOpenLinks(False)
        self.out.anchorClicked.connect(QDesktopServices.openUrl)
        output_layout.addWidget(self.out, 2)
        
        # Right: JSON reasoning
        json_group = QGroupBox("Reasoning Details")
        json_layout = QVBoxLayout(json_group)
        
        self.json_out = QTextEdit()
        self.json_out.setReadOnly(True)
        self.json_out.setFont(QFont("Consolas", 9))
        self.json_highlighter = JSONHighlighter(self.json_out.document())
        json_layout.addWidget(self.json_out)
        
        output_layout.addWidget(json_group, 1)
        layout.addLayout(output_layout, 1)
        
        parent_tabs.addTab(chat_widget, "Chat")
    
    def setup_index_management_tab(self, parent_tabs):
        """Setup the index management tab"""
        management_widget = QWidget()
        layout = QVBoxLayout(management_widget)
        
        # Title
        title = QLabel("Index Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Index list
        list_group = QGroupBox("Available Indexes")
        list_layout = QVBoxLayout(list_group)
        
        # Index tree widget
        self.index_tree = QTreeWidget()
        self.index_tree.setHeaderLabels(["Name", "Documents", "Vectors", "Size (MB)", "Created", "Model"])
        self.index_tree.setAlternatingRowColors(True)
        self.index_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        list_layout.addWidget(self.index_tree)
        
        # Index management buttons
        button_layout = QHBoxLayout()
        
        self.bRefreshIndexes = QPushButton("Refresh List")
        self.bRefreshIndexes.clicked.connect(self.refresh_index_list)
        button_layout.addWidget(self.bRefreshIndexes)
        
        self.bDeleteIndex = QPushButton("Delete Selected")
        self.bDeleteIndex.clicked.connect(self.delete_selected_indexes)
        button_layout.addWidget(self.bDeleteIndex)
        
        self.bDeleteAllIndexes = QPushButton("Delete All")
        self.bDeleteAllIndexes.clicked.connect(self.delete_all_indexes)
        button_layout.addWidget(self.bDeleteAllIndexes)
        
        self.bRebuildIndex = QPushButton("Rebuild Selected")
        self.bRebuildIndex.clicked.connect(self.rebuild_selected_index)
        button_layout.addWidget(self.bRebuildIndex)
        
        self.bRenameIndex = QPushButton("Rename Selected")
        self.bRenameIndex.clicked.connect(self.rename_selected_index)
        button_layout.addWidget(self.bRenameIndex)
        
        button_layout.addStretch()
        list_layout.addLayout(button_layout)
        
        layout.addWidget(list_group)
        
        # Index details
        details_group = QGroupBox("Index Details")
        details_layout = QVBoxLayout(details_group)
        
        self.index_details = QTextEdit()
        self.index_details.setReadOnly(True)
        self.index_details.setMaximumHeight(200)
        details_layout.addWidget(self.index_details)
        
        # Connect selection change
        self.index_tree.itemSelectionChanged.connect(self.on_index_selection_changed)
        
        layout.addWidget(details_group)
        
        # Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.index_summary = QLabel("Click 'Refresh List' to load index information")
        summary_layout.addWidget(self.index_summary)
        
        layout.addWidget(summary_group)
        
        # Load initial data
        self.refresh_index_list()
        
        parent_tabs.addTab(management_widget, "Index Management")
    
    def setup_diagnostics_tab(self):
        """Setup diagnostics tab"""
        self.diagnostics = DiagnosticsWidget(self)
        self.tabs.addTab(self.diagnostics, "Diagnostics")
    
    def setup_initial_state(self):
        """Setup initial application state"""
        # LLM backend will be set by _load_llm_config() during initialization
        # No need to set default here as it would trigger unwanted signals
        pass
    
    def update_gpu_status(self):
        """Update device status in status bar (CPU-only)"""
        self.gpu_status_label.setText("Device: CPU")
        self.gpu_status_label.setStyleSheet("color: #3498db; font-weight: bold;")
    
    def pick_folder(self):
        """Pick folder for indexing"""
        folder = QFileDialog.getExistingDirectory(self, "Select a folder to index")
        if folder:
            self.eFolder.setText(folder)
            log_operation("Folder Selected", f"Selected folder: {folder}")
    
    def start_index(self):
        """Start indexing process"""
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Please wait", "Indexing in progress...")
            return
        
        folder = self.eFolder.text().strip()
        if not folder:
            QMessageBox.warning(self, "Attention", "Please choose a folder.")
            return
        
        # Create index config
        cfg = IndexConfig(
            embed_model=self.cbEmbed.currentData(),
            index_type=self.cbIndex.currentData()
        )
        
        # Start indexing thread
        self.worker = EnterpriseIndexThread(Path(folder), cfg, config_manager.get_index_path())
        self.worker.status.connect(self.log.append)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.done.connect(self.index_done)
        
        self.bIndex.setEnabled(False)
        self.bCancel.setEnabled(True)
        self.log.append(f"\n— Starting indexing → {folder}")
        self.prog.setRange(0, 0)
        self.worker.start()
        
        log_operation("Indexing Started", f"Folder: {folder}, Model: {cfg.embed_model}")
    
    def on_progress_update(self, p: int):
        """Update progress bar"""
        if self.prog.minimum() == 0 and self.prog.maximum() == 0:
            self.prog.setRange(0, 100)
        self.prog.setValue(p)
    
    def cancel_index(self):
        """Cancel indexing"""
        if hasattr(self, 'worker') and self.worker:
            self.worker.cancel()
            log_operation("Indexing Cancelled", "User cancelled indexing")
    
    def index_done(self, files: int, vecs: int):
        """Handle indexing completion"""
        self.bIndex.setEnabled(True)
        self.bCancel.setEnabled(False)
        self.prog.setRange(0, 100)
        self.prog.setValue(100)
        self.log.append(f"\n✅ Completed. Files indexed: {files} • Vectors: {vecs}")
        
        # Update index status and try to reload
        self.lblIndex.setText(self.index_status_text())
        try:
            self.retriever = Retriever(config_manager.get_index_path())
            self.lblIndex.setText(
                self.index_status_text() + 
                f"  • vectors={self.retriever.idx.ntotal}  • embed={self.retriever.embed_model}"
            )
            self.log.append(f"✅ Index loaded successfully: {self.retriever.idx.ntotal} vectors")
        except Exception as e:
            self.log.append(f"⚠️ Index created but could not load: {e}")
            self.retriever = None
        
        log_operation("Indexing Completed", f"Files: {files}, Vectors: {vecs}")
    
    def index_status_text(self) -> str:
        """Get index status text"""
        idx_path = config_manager.get_index_path() / "index.faiss"
        return f"Index: {idx_path}" if idx_path.exists() else "Index: — not found —"
    
    def reload_index(self):
        """Reload the index"""
        idx_path = config_manager.get_index_path() / "index.faiss"
        if not idx_path.exists():
            QMessageBox.information(self, "No Index", "No index found. Please build an index first using the Indexing tab.")
            return
        
        try:
            self.retriever = Retriever(config_manager.get_index_path())
            self.lblIndex.setText(
                self.index_status_text() + 
                f"  • vectors={self.retriever.idx.ntotal}  • embed={self.retriever.embed_model}"
            )
            QMessageBox.information(self, "OK", f"Index reloaded successfully!\nVectors: {self.retriever.idx.ntotal}")
            log_operation("Index Reloaded", f"Vectors: {self.retriever.idx.ntotal}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load the index.\n{e}")
            log_error("Index Reload Failed", e)
    
    def on_backend_change(self, idx: int):
        """Handle LLM backend change"""
        kind = self.cbLLM.currentData()
        
        # Enable/disable model name field based on backend
        if kind in ["openai", "anthropic", "gemini"]:
            self.eModelName.setEnabled(False)
        else:
            self.eModelName.setEnabled(True)
        
        # Don't automatically apply - let users click the "Apply" button
        # This prevents unwanted warnings during startup or when browsing backends
    
    def _configure_openai(self):
        """Configure OpenAI/OpenRouter API"""
        from app_qt import OpenAIDialog
        dlg = OpenAIDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            key, url, model, remember = dlg.values()
            if not key:
                QMessageBox.warning(self, "Missing API key", "Please enter a valid API key.")
                self.cbLLM.setCurrentIndex(0)
                return
            
            # Set environment variables
            os.environ["OPENAI_API_KEY"] = key
            os.environ["OPENAI_MODEL"] = model
            if url:
                os.environ["OPENAI_BASE_URL"] = url
            else:
                os.environ.pop("OPENAI_BASE_URL", None)
            
            # Apply backend
            try:
                self.llm = create_llm("openai", model=model)
                QMessageBox.information(self, "LLM", f"Applied: {self.llm.name}")
                log_operation("LLM Backend Changed", f"OpenAI: {model}")
            except Exception as e:
                QMessageBox.warning(self, "LLM error", str(e))
                self.cbLLM.setCurrentIndex(0)
        else:
            self.cbLLM.setCurrentIndex(0)
    
    def _configure_anthropic(self):
        """Configure Anthropic Claude API"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Anthropic Claude")
        dialog.setModal(True)
        dialog.resize(400, 200)
        
        layout = QFormLayout(dialog)
        
        # API Key
        api_key_edit = QLineEdit()
        api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_edit.setText(os.getenv("ANTHROPIC_API_KEY", ""))
        layout.addRow("API Key:", api_key_edit)
        
        # Model selection
        model_combo = QComboBox()
        model_combo.addItems([
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022"
        ])
        model_combo.setCurrentText(os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"))
        layout.addRow("Model:", model_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            api_key = api_key_edit.text().strip()
            model = model_combo.currentText()
            
            if not api_key:
                QMessageBox.warning(self, "Missing API key", "Please enter a valid Anthropic API key.")
                self.cbLLM.setCurrentIndex(0)
                return
            
            # Set environment variables
            os.environ["ANTHROPIC_API_KEY"] = api_key
            os.environ["ANTHROPIC_MODEL"] = model
            
            # Apply backend
            try:
                self.llm = create_llm("anthropic", model=model)
                QMessageBox.information(self, "LLM", f"Applied: {self.llm.name}")
                log_operation("LLM Backend Changed", f"Anthropic: {model}")
            except Exception as e:
                QMessageBox.warning(self, "LLM error", str(e))
                self.cbLLM.setCurrentIndex(0)
        else:
            self.cbLLM.setCurrentIndex(0)
    
    def _configure_gemini(self):
        """Configure Google Gemini API"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Google Gemini")
        dialog.setModal(True)
        dialog.resize(400, 200)
        
        layout = QFormLayout(dialog)
        
        # API Key
        api_key_edit = QLineEdit()
        api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_edit.setText(os.getenv("GEMINI_API_KEY", ""))
        layout.addRow("API Key:", api_key_edit)
        
        # Model selection
        model_combo = QComboBox()
        model_combo.addItems([
            "gemini-2.5-flash",
            "gemini-2.5-pro", 
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro"
        ])
        model_combo.setCurrentText(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        layout.addRow("Model:", model_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            api_key = api_key_edit.text().strip()
            model = model_combo.currentText()
            
            if not api_key:
                QMessageBox.warning(self, "Missing API key", "Please enter a valid Gemini API key.")
                self.cbLLM.setCurrentIndex(0)
                return
            
            # Set environment variables
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["GEMINI_MODEL"] = model
            
            # Apply backend
            try:
                self.llm = create_llm("gemini", model=model)
                QMessageBox.information(self, "LLM", f"Applied: {self.llm.name}")
                log_operation("LLM Backend Changed", f"Gemini: {model}")
            except Exception as e:
                QMessageBox.warning(self, "LLM error", str(e))
                self.cbLLM.setCurrentIndex(0)
        else:
            self.cbLLM.setCurrentIndex(0)
    
    def _configure_ollama(self):
        """Configure Ollama local server"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Ollama")
        dialog.setModal(True)
        dialog.resize(400, 250)
        
        layout = QFormLayout(dialog)
        
        # Base URL
        url_edit = QLineEdit()
        url_edit.setText(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        layout.addRow("Base URL:", url_edit)
        
        # Model selection
        model_combo = QComboBox()
        popular_models = [
            "llama2",
            "mistral", 
            "codellama",
            "phi3",
            "qwen2.5:7b",
            "qwen2.5:14b",
            "qwen2.5:32b"
        ]
        model_combo.addItems(popular_models)
        layout.addRow("Model:", model_combo)
        
        # Custom model input
        custom_model = QLineEdit()
        custom_model.setPlaceholderText("Or enter custom model name")
        layout.addRow("Custom:", custom_model)
        
        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(lambda: self._test_ollama_connection(url_edit.text()))
        layout.addRow("", test_btn)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            base_url = url_edit.text().strip()
            
            if custom_model.text().strip():
                model = custom_model.text().strip()
            else:
                model = model_combo.currentText()
            
            if not base_url or not model:
                QMessageBox.warning(self, "Missing configuration", "Please enter both base URL and model name.")
                self.cbLLM.setCurrentIndex(0)
                return
            
            # Set environment variables
            os.environ["OLLAMA_BASE_URL"] = base_url
            os.environ["OLLAMA_MODEL"] = model
            
            # Apply backend
            try:
                self.llm = create_llm("ollama", model=model, base_url=base_url)
                self.eModelName.setText(model)
                self._save_llm_config("ollama", model)
                QMessageBox.information(self, "Configuration Saved", f"Ollama model configured: {model}")
                log_operation("LLM Backend Changed", f"Ollama: {model}")
            except Exception as e:
                QMessageBox.warning(self, "LLM error", str(e))
                self.cbLLM.setCurrentIndex(0)
        else:
            self.cbLLM.setCurrentIndex(0)
    
    
    def _test_ollama_connection(self, base_url: str):
        """Test Ollama server connection"""
        try:
            import requests
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                QMessageBox.information(self, "Connection Test", "✅ Ollama server is running and accessible!")
            else:
                QMessageBox.warning(self, "Connection Test", f"❌ Ollama server returned status {response.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Connection Test", f"❌ Cannot connect to Ollama server:\n{e}")
    
    def _configure_huggingface(self):
        """Configure HuggingFace local model"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure HuggingFace Model")
        dialog.setModal(True)
        dialog.resize(400, 200)
        
        layout = QFormLayout(dialog)
        
        # Model selection
        model_combo = QComboBox()
        popular_models = [
            # Qwen Models
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "Qwen/Qwen2.5-32B-Instruct",
            "Qwen/Qwen1.5-7B-Chat",
            "Qwen/Qwen1.5-14B-Chat",
            # Other Popular Models
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-large", 
            "facebook/blenderbot-400M-distill",
            "distilbert-base-uncased",
            "bert-base-uncased"
        ]
        model_combo.addItems(popular_models)
        layout.addRow("Model:", model_combo)
        
        # Custom model input
        custom_model = QLineEdit()
        custom_model.setPlaceholderText("Or enter custom model name (e.g., microsoft/DialoGPT-large)")
        layout.addRow("Custom:", custom_model)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        download_button = QPushButton("Download Model Now")
        download_button.clicked.connect(lambda: self._download_huggingface_model(dialog, model_combo, custom_model))
        button_layout.addWidget(download_button)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        button_layout.addWidget(buttons)
        
        layout.addRow(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if custom_model.text().strip():
                model_name = custom_model.text().strip()
            else:
                model_name = model_combo.currentText()
            
            if model_name:
                self.eModelName.setText(model_name)
                self._save_llm_config("hf_local", model_name)
                QMessageBox.information(self, "Configuration Saved", f"HuggingFace model configured: {model_name}")
    
    def _download_huggingface_model(self, dialog, model_combo, custom_model):
        """Download HuggingFace model immediately"""
        if custom_model.text().strip():
            model_name = custom_model.text().strip()
        else:
            model_name = model_combo.currentText()
        
        if not model_name:
            QMessageBox.warning(dialog, "No Model", "Please select or enter a model name.")
            return
        
        # Show progress dialog
        progress_dialog = QDialog(dialog)
        progress_dialog.setWindowTitle("Downloading Model")
        progress_dialog.setModal(True)
        progress_dialog.resize(400, 150)
        
        layout = QVBoxLayout(progress_dialog)
        layout.addWidget(QLabel(f"Downloading model: {model_name}"))
        layout.addWidget(QLabel("This may take several minutes..."))
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(progress_bar)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(progress_dialog.reject)
        layout.addWidget(cancel_button)
        
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # Create LLM with lazy_load=False to trigger immediate download
            from llm import create_llm
            llm = create_llm("hf_local", model_id=model_name, lazy_load=False)
            
            progress_dialog.accept()
            QMessageBox.information(
                dialog, "Download Complete", 
                f"Model '{model_name}' downloaded successfully!\n"
                "You can now use it without waiting for downloads."
            )
            
        except Exception as e:
            progress_dialog.accept()
            QMessageBox.warning(
                dialog, "Download Failed", 
                f"Failed to download model '{model_name}':\n{e}\n\n"
                "The model will still be downloaded automatically when you ask your first question."
            )
    
    def _configure_llama_cpp(self):
        """Configure LlamaCpp local model"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure LlamaCpp Model")
        dialog.setModal(True)
        dialog.resize(400, 200)
        
        layout = QFormLayout(dialog)
        
        # Model file selection
        file_layout = QHBoxLayout()
        model_path = QLineEdit()
        model_path.setPlaceholderText("Select GGUF model file...")
        file_layout.addWidget(model_path)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(lambda: self._browse_llama_model_file(dialog, model_path))
        file_layout.addWidget(browse_button)
        layout.addRow("Model File:", file_layout)
        
        # Model name input
        model_name = QLineEdit()
        model_name.setPlaceholderText("Or enter model name (e.g., mistral-7b-instruct-v0.1.Q4_K_M)")
        layout.addRow("Model Name:", model_name)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if model_path.text().strip():
                model = model_path.text().strip()
            elif model_name.text().strip():
                model = model_name.text().strip()
            else:
                QMessageBox.warning(self, "Missing configuration", "Please select a model file or enter a model name.")
                return
            
            if model:
                self.eModelName.setText(model)
                self._save_llm_config("llama_cpp", model)
                QMessageBox.information(self, "Configuration Saved", f"LlamaCpp model configured: {model}")
    
    def _browse_llama_model_file(self, parent, path_edit):
        """Browse for LlamaCpp model file"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Select GGUF Model File",
            "",
            "GGUF Files (*.gguf);;All Files (*)"
        )
        if file_path:
            path_edit.setText(file_path)
    
    
    def configure_current_backend(self):
        """Configure the currently selected LLM backend"""
        kind = self.cbLLM.currentData()
        
        if kind == "openai":
            self._configure_openai()
        elif kind == "anthropic":
            self._configure_anthropic()
        elif kind == "gemini":
            self._configure_gemini()
        elif kind == "ollama":
            self._configure_ollama()
        elif kind == "hf_local":
            self._configure_huggingface()
        elif kind == "llama_cpp":
            self._configure_llama_cpp()
        else:
            QMessageBox.information(
                self, 
                "Configuration", 
                f"No configuration needed for {kind} backend.\n"
                f"Just set the model name/path and click Apply."
            )

    def apply_llm(self, silent: bool = False):
        """Apply LLM configuration
        
        Args:
            silent: If True, don't show warnings for missing API keys (useful during startup)
        """
        kind = self.cbLLM.currentData()
        name = self.eModelName.text().strip() or ""
        
        try:
            if kind == "llama_cpp":
                if name:
                    # Use custom model path
                    model_path = name
                else:
                    # Use default Mistral model
                    models_dir = config_manager.get_model_path().parent
                    model_path = models_dir / "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
                    if not model_path.exists():
                        if not silent:
                            QMessageBox.warning(
                                self, "Model Not Found", 
                                f"Mistral model not found at: {model_path}\n\n"
                                "Please run setup_mistral.py to download the model, or\n"
                                "specify a custom model path in the Model field."
                            )
                        # Fall back to "none"
                        self.llm = create_llm("none")
                        log_operation("LLM Backend Applied", "Fallback to 'none' - Mistral model not found")
                        return
                
                self.llm = create_llm("llama_cpp", model_path=str(model_path))
            elif kind == "openai":
                if not os.getenv("OPENAI_API_KEY"):
                    if not silent:
                        QMessageBox.information(
                            self, "API Key Required", 
                            "OpenAI API key not found. Please click 'Configure' to set your API key."
                        )
                    # Fall back to "none" instead of showing error
                    self.llm = create_llm("none")
                    log_operation("LLM Backend Applied", "Fallback to 'none' - OpenAI API key not found")
                    return
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.llm = create_llm("openai", model=model)
            elif kind == "anthropic":
                if not os.getenv("ANTHROPIC_API_KEY"):
                    if not silent:
                        QMessageBox.information(
                            self, "API Key Required", 
                            "Anthropic API key not found. Please click 'Configure' to set your API key."
                        )
                    # Fall back to "none" instead of showing error
                    self.llm = create_llm("none")
                    log_operation("LLM Backend Applied", "Fallback to 'none' - Anthropic API key not found")
                    return
                model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
                self.llm = create_llm("anthropic", model=model)
            elif kind == "gemini":
                if not os.getenv("GEMINI_API_KEY"):
                    if not silent:
                        QMessageBox.information(
                            self, "API Key Required", 
                            "Gemini API key not found. Please click 'Configure' to set your API key."
                        )
                    # Fall back to "none" instead of showing error
                    self.llm = create_llm("none")
                    log_operation("LLM Backend Applied", "Fallback to 'none' - Gemini API key not found")
                    return
                model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                self.llm = create_llm("gemini", model=model)
                # Show helpful message about Gemini safety filters
                if not silent:
                    QMessageBox.information(
                        self, "Gemini Backend Applied", 
                        "Gemini backend applied successfully!\n\n"
                        "Note: Gemini has strict content safety policies. If you encounter safety filter blocks, "
                        "try rephrasing your question or switch to a different LLM backend (OpenAI, Anthropic, or Ollama)."
                    )
            elif kind == "ollama":
                model = os.getenv("OLLAMA_MODEL", "llama2")
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                self.llm = create_llm("ollama", model=model, base_url=base_url)
            elif kind == "hf_local":
                model_id = name or "microsoft/DialoGPT-medium"
                self.llm = create_llm("hf_local", model_id=model_id, lazy_load=True)
            elif kind == "none":
                self.llm = create_llm("none")
            else:
                if not silent:
                    QMessageBox.warning(self, "LLM Error", "Selected backend not available")
                self.llm = create_llm("none")
                return
            
            # Save LLM configuration to config file
            self._save_llm_config(kind, name)
            
            # Show appropriate message based on backend
            if kind == "hf_local":
                QMessageBox.information(
                    self, "LLM Applied", 
                    f"HuggingFace model configured: {model_id}\n\n"
                    "The model will be downloaded automatically when you ask your first question.\n"
                    "This may take several minutes depending on the model size."
                )
            else:
                QMessageBox.information(self, "LLM", f"Applied: {self.llm.name}")
            
            log_operation("LLM Backend Applied", f"{kind}: {self.llm.name}")
            
        except Exception as e:
            QMessageBox.warning(self, "LLM error", str(e))
            self.llm = create_llm("none")
            log_error("LLM Application Failed", e)
    
    def _save_llm_config(self, backend: str, model_name: str = ""):
        """Save LLM configuration to config file"""
        try:
            # Update config with new LLM settings
            config_manager.config.llm.backend = backend
            
            if backend == "llama_cpp" and model_name:
                config_manager.config.llm.model_path = model_name
            elif backend in ["openai", "anthropic", "gemini", "ollama"]:
                # For API backends, we don't need to save model path in config
                # The model is determined by environment variables
                pass
            elif backend == "hf_local" and model_name:
                config_manager.config.llm.model_path = model_name
            
            # Save configuration
            config_manager.save_config()
            log_operation("LLM Config Saved", f"Backend: {backend}, Model: {model_name}")
            
        except Exception as e:
            log_error("LLM Config Save Failed", e)
    
    def _load_llm_config(self):
        """Load saved LLM configuration from config file (UI only, no connections)"""
        try:
            # Get saved backend from config
            saved_backend = config_manager.config.llm.backend

            # Block signals to prevent on_backend_change from firing during initialization
            self.cbLLM.blockSignals(True)

            # Set the combo box to the saved backend
            for i in range(self.cbLLM.count()):
                if self.cbLLM.itemData(i) == saved_backend:
                    self.cbLLM.setCurrentIndex(i)
                    break

            # Re-enable signals
            self.cbLLM.blockSignals(False)

            # Set model name if available
            if saved_backend == "llama_cpp" and config_manager.config.llm.model_path:
                model_path = config_manager.config.llm.model_path
                # Extract just the filename for display
                import os
                model_name = os.path.basename(model_path)
                self.eModelName.setText(model_name)
            elif saved_backend == "hf_local" and config_manager.config.llm.model_path:
                self.eModelName.setText(config_manager.config.llm.model_path)

            # Set LLM to "none" during startup to avoid connection attempts
            # The actual LLM will be loaded when user clicks Apply
            self.llm = create_llm("none")

            log_operation("LLM Config Loaded", f"Backend: {saved_backend}")

        except Exception as e:
            log_error("LLM Config Load Failed", e)
            # Re-enable signals if there was an error
            self.cbLLM.blockSignals(False)
            # Fallback to "none" (no connections)
            self.llm = create_llm("none")
    
    def ask(self):
        """Ask a question with enhanced reasoning"""
        q = self.inp.toPlainText().strip()
        if not q:
            QMessageBox.warning(self, "Empty field", "Please type a question.")
            return
        
        if self.llm is None:
            QMessageBox.warning(self, "No LLM", "No LLM backend selected. Please select and apply an LLM backend first.")
            return
        
        if self.retriever is None:
            idx_path = config_manager.get_index_path() / "index.faiss"
            if not idx_path.exists():
                QMessageBox.warning(self, "No Index", "No index found. Please build an index first using the Indexing tab.")
                return
            try:
                self.retriever = Retriever(config_manager.get_index_path())
                self.lblIndex.setText(
                    self.index_status_text() + 
                    f"  • vectors={self.retriever.idx.ntotal}  • embed={self.retriever.embed_model}"
                )
            except Exception as e:
                QMessageBox.warning(self, "Index Error", f"Could not load the index.\n{e}")
                return
        
        if hasattr(self, 'asker') and self.asker and self.asker.isRunning():
            return
        
        self.bAsk.setEnabled(False)
        
        # Check if streaming mode is enabled
        if self.streaming_mode.isChecked():
            self.out.setHtml("<i>Starting live thinking process...</i>")
            self.json_out.setText("Streaming reasoning...")
            
            self.asker = StreamingAskThread(q, self.retriever, self.llm)
            self.asker.reasoning_update.connect(self.on_streaming_update)
            self.asker.error.connect(self.on_answer_error)
            self.asker.finished.connect(self.on_streaming_finished)
            self.asker.start()
        else:
            self.out.setHtml("<i>Searching documents...</i>")
            self.json_out.setText("Processing reasoning...")
            
            self.asker = AskThread(q, self.retriever, self.llm)
            self.asker.ready.connect(self.on_answer_ready)
            self.asker.error.connect(self.on_answer_error)
            self.asker.start()
        
        log_operation("Question Asked", f"Query: {q[:50]}...")
    
    def on_answer_ready(self, result: ReasoningResult):
        """Handle answer ready with enhanced reasoning display"""
        try:
            # Format answer with source citations like the original project
            formatted_answer = self._format_answer_with_citations(result.answer, result.source_citations)
            
            # Display formatted answer
            self.out.setHtml(f"<b>Answer:</b><br><div style='white-space:pre-wrap'>{formatted_answer}</div>")
            # Auto-scroll to bottom
            self.out.verticalScrollBar().setValue(self.out.verticalScrollBar().maximum())
            
            # Convert reasoning result to JSON
            import json
            from dataclasses import asdict
            json_str = json.dumps(asdict(result), indent=2, ensure_ascii=False)
            self.json_out.setText(json_str)
            # Auto-scroll to bottom
            self.json_out.verticalScrollBar().setValue(self.json_out.verticalScrollBar().maximum())
            
            # Log the reasoning result
            log_info(f"Reasoning completed with confidence: {result.confidence_score:.2f}")
            
        except Exception as e:
            log_error("Answer Display Failed", e)
            self.out.setHtml(f"<b>Error:</b> {e}")
            self.json_out.setText(f"Error: {e}")
        
        self.bAsk.setEnabled(True)
        self.inp.clear()
        self.inp.setFocus()
        log_operation("Answer Generated", "Answer provided to user")
    
    def _format_answer_with_citations(self, answer: str, source_citations: List[Any]) -> str:
        """Format the final answer with beautiful source citations like the original project"""
        if not source_citations:
            return answer
        
        # Remove duplicate sources based on file path
        unique_sources = {}
        for citation in source_citations:
            # Handle both dict and SourceCitation object
            if hasattr(citation, 'file'):
                file_path = citation.file
                page = citation.page
                relevance = getattr(citation, 'relevance', 0.0)
            else:
                file_path = citation.get("file", "Unknown")
                page = citation.get("page", "?")
                relevance = citation.get("relevance", 0.0)
            
            # Use file path as key to avoid duplicates
            if file_path not in unique_sources or relevance > unique_sources[file_path]['relevance']:
                unique_sources[file_path] = {
                    'file_path': file_path,
                    'page': page,
                    'relevance': relevance
                }
        
        # Create clean source citations section
        sources_html = []
        for i, (file_path, source_info) in enumerate(unique_sources.items(), 1):
            # Extract just the filename
            import os
            file_name = os.path.basename(file_path) if file_path != "Unknown" else "Unknown"
            
            # Create clickable "Open" link
            if file_path != "Unknown":
                try:
                    from pathlib import Path
                    from PyQt6.QtCore import QUrl
                    path = Path(file_path).resolve()
                    url = QUrl.fromLocalFile(str(path))
                    open_link = f"<a href='{url.toString()}' title='{path}' style='color: #007acc; text-decoration: none;'>Open</a>"
                except:
                    open_link = "<span style='color: #666;'>Open</span>"
            else:
                open_link = "<span style='color: #666;'>Open</span>"
            
            # Clean format for customer support: [1] filename.pdf • page 12 • Open
            source_text = f"[{i}] <span style='font-weight: bold; color: #2c3e50;'>{file_name}</span> • page {source_info['page']} • {open_link}"
            sources_html.append(source_text)
        
        # Combine answer with beautifully formatted sources
        formatted_answer = f"{answer}\n\n<b style='color: #34495e; font-size: 14px;'>Sources:</b><br>" + "<br>".join(sources_html)
        
        return formatted_answer
    
    def on_streaming_update(self, result):
        """Handle streaming reasoning update with enhanced display"""
        try:
            # Always show current step in answer area for live thinking
            if result.current_step:
                step_display = f"<b>Current Step:</b> {result.current_step}<br><br>"
            else:
                step_display = "<b>Thinking...</b><br><br>"
            
            # Show partial answer if available
            if result.answer:
                answer_display = f"<b>Answer (Building...):</b><br><div style='white-space:pre-wrap; color: #2E8B57;'>{result.answer}</div>"
            else:
                answer_display = "<i style='color: #666;'>Generating answer...</i>"
            
            # Combine step and answer display
            full_display = step_display + answer_display
            self.out.setHtml(full_display)
            # Auto-scroll answer area to bottom
            self.out.verticalScrollBar().setValue(self.out.verticalScrollBar().maximum())
            
            # Update reasoning display with live updates
            if result.reasoning_chain:
                reasoning_text = "\n\n".join(result.reasoning_chain)
                self.json_out.setText(reasoning_text)
                # Auto-scroll to bottom
                self.json_out.verticalScrollBar().setValue(self.json_out.verticalScrollBar().maximum())
            else:
                # Show current step in reasoning area
                if result.current_step:
                    self.json_out.setText(f"Current Step: {result.current_step}\n\nReasoning in progress...")
                else:
                    self.json_out.setText("Starting reasoning process...")
                # Auto-scroll to bottom
                self.json_out.verticalScrollBar().setValue(self.json_out.verticalScrollBar().maximum())
            
            # Update status if complete
            if result.is_complete:
                # Convert to JSON for final display
                import json
                from dataclasses import asdict
                json_str = json.dumps(asdict(result), indent=2, ensure_ascii=False)
                self.json_out.setText(json_str)
                # Auto-scroll to bottom for final result
                self.json_out.verticalScrollBar().setValue(self.json_out.verticalScrollBar().maximum())
                
                # Show final answer
                if result.answer:
                    self.out.setHtml(f"<b>Final Answer:</b><br><div style='white-space:pre-wrap; color: #2E8B57; font-weight: bold;'>{result.answer}</div>")
                    # Auto-scroll to bottom for final answer
                    self.out.verticalScrollBar().setValue(self.out.verticalScrollBar().maximum())
                
                log_info(f"Streaming reasoning completed with confidence: {result.confidence_score:.2f}")
                
        except Exception as e:
            log_error("Streaming Update Failed", e)
            self.out.setHtml(f"<b>Error:</b> {e}")
            self.json_out.setText(f"Error: {e}")
    
    def on_streaming_finished(self):
        """Handle streaming completion"""
        self.bAsk.setEnabled(True)
        self.inp.clear()
        self.inp.setFocus()
        log_operation("Streaming Answer Generated", "Streaming answer provided to user")
    
    def on_answer_error(self, msg: str):
        """Handle answer error"""
        QMessageBox.warning(self, "Error while answering", msg)
        self.bAsk.setEnabled(True)
        self.inp.setFocus()
        self.json_out.setText(f"Error: {msg}")
        log_error("Answer Generation Failed", Exception(msg))
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.setText(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        log_info(f"Status: {message}")
    
    # Index Management Methods
    def refresh_index_list(self):
        """Refresh the list of available indexes"""
        try:
            self.index_tree.clear()
            indexes = self.index_manager.list_indexes()
            
            for index in indexes:
                item = QTreeWidgetItem([
                    index.name,
                    str(index.document_count),
                    str(index.vector_count),
                    str(index.size_mb),
                    index.created_at,
                    index.embedding_model
                ])
                item.setData(0, 0, index.name)  # Store index name for later use
                self.index_tree.addTopLevelItem(item)
            
            # Update summary
            summary = self.index_manager.get_index_summary()
            summary_text = f"Total: {summary['total_indexes']} indexes, {summary['total_documents']} documents, {summary['total_vectors']} vectors, {summary['total_size_mb']} MB"
            self.index_summary.setText(summary_text)
            
            log_operation("Index List Refreshed", f"Found {len(indexes)} indexes")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh index list: {e}")
            log_error("Index List Refresh Failed", e)
    
    def on_index_selection_changed(self):
        """Handle index selection change"""
        try:
            selected_items = self.index_tree.selectedItems()
            if not selected_items:
                self.index_details.clear()
                return
            
            index_name = selected_items[0].data(0, 0)
            status = self.index_manager.get_index_status(index_name)
            
            if status.get('exists', False):
                details = f"""Index: {index_name}
Status: {'Valid' if status.get('is_valid', False) else 'Invalid'}
Vector Count: {status.get('vector_count', 0)}
Dimension: {status.get('dimension', 0)}
Chunk Count: {status.get('chunk_count', 0)}
Document Count: {status.get('document_count', 0)}
Embedding Model: {status.get('embedding_model', 'Unknown')}
Created: {status.get('created_at', 'Unknown')}
Last Modified: {status.get('last_modified', 'Unknown')}
Size: {status.get('size_mb', 0)} MB"""
                
                if 'error' in status:
                    details += f"\nError: {status['error']}"
                
                self.index_details.setText(details)
            else:
                self.index_details.setText(f"Index {index_name} does not exist or is invalid.")
                
        except Exception as e:
            self.index_details.setText(f"Error loading index details: {e}")
            log_error("Index Details Load Failed", e)
    
    def delete_selected_indexes(self):
        """Delete selected indexes"""
        try:
            selected_items = self.index_tree.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "No Selection", "Please select indexes to delete.")
                return
            
            # Confirm deletion
            index_names = [item.data(0, 0) for item in selected_items]
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Are you sure you want to delete {len(index_names)} index(es)?\n\n"
                f"Indexes: {', '.join(index_names)}\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                deleted_count = 0
                for index_name in index_names:
                    if self.index_manager.delete_index(index_name):
                        deleted_count += 1
                
                if deleted_count > 0:
                    self.refresh_index_list()
                    QMessageBox.information(self, "Success", f"Successfully deleted {deleted_count} index(es).")
                    log_operation("Indexes Deleted", f"Deleted {deleted_count} indexes")
                else:
                    QMessageBox.warning(self, "Warning", "No indexes were deleted.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete indexes: {e}")
            log_error("Index Deletion Failed", e)
    
    def delete_all_indexes(self):
        """Delete all indexes"""
        try:
            indexes = self.index_manager.list_indexes()
            if not indexes:
                QMessageBox.information(self, "No Indexes", "No indexes found to delete.")
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Are you sure you want to delete ALL {len(indexes)} indexes?\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.index_manager.delete_all_indexes():
                    self.refresh_index_list()
                    QMessageBox.information(self, "Success", "Successfully deleted all indexes.")
                    log_operation("All Indexes Deleted", f"Deleted {len(indexes)} indexes")
                else:
                    QMessageBox.warning(self, "Warning", "Some indexes could not be deleted.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete all indexes: {e}")
            log_error("All Index Deletion Failed", e)
    
    def rebuild_selected_index(self):
        """Rebuild selected index"""
        try:
            selected_items = self.index_tree.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "No Selection", "Please select an index to rebuild.")
                return
            
            if len(selected_items) > 1:
                QMessageBox.information(self, "Multiple Selection", "Please select only one index to rebuild.")
                return
            
            index_name = selected_items[0].data(0, 0)
            
            # Get source documents for the index
            index_info = self.index_manager._get_index_info(index_name)
            if not index_info:
                QMessageBox.warning(self, "Error", f"Could not get information for index: {index_name}")
                return
            
            source_documents = index_info.documents
            if not source_documents:
                # For old-style indexes, we don't have source documents stored
                # Ask user to provide source documents
                from PyQt6.QtWidgets import QInputDialog
                text, ok = QInputDialog.getText(
                    self, "Source Documents", 
                    f"No source documents found for index '{index_name}'.\n\n"
                    f"Please provide the path to the source documents folder:",
                    text="C:/Users/aamam/Desktop/database"  # Default path from your indexing
                )
                if not ok or not text.strip():
                    return
                
                # Validate the path
                import os
                if not os.path.exists(text.strip()):
                    QMessageBox.warning(self, "Error", f"Path does not exist: {text.strip()}")
                    return
                
                # Get all document files from the directory
                source_documents = []
                for root, dirs, files in os.walk(text.strip()):
                    for file in files:
                        if file.lower().endswith(('.pdf', '.docx', '.txt', '.pptx', '.xlsx', '.csv')):
                            source_documents.append(os.path.join(root, file))
                
                if not source_documents:
                    QMessageBox.warning(self, "Error", f"No supported documents found in: {text.strip()}")
                    return
            
            # Confirm rebuild
            reply = QMessageBox.question(
                self, "Confirm Rebuild",
                f"Are you sure you want to rebuild index '{index_name}'?\n\n"
                f"This will delete the current index and recreate it from {len(source_documents)} source document(s).\n\n"
                f"Source documents:\n" + "\n".join(f"• {doc}" for doc in source_documents[:5]) +
                (f"\n... and {len(source_documents) - 5} more" if len(source_documents) > 5 else ""),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Show progress
                progress = QMessageBox(self)
                progress.setWindowTitle("Rebuilding Index")
                progress.setText(f"Rebuilding index '{index_name}'...\nThis may take a few minutes.")
                progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
                progress.show()
                QApplication.processEvents()
                
                # Rebuild index
                success = self.index_manager.rebuild_index(index_name, source_documents)
                progress.close()
                
                if success:
                    self.refresh_index_list()
                    QMessageBox.information(self, "Success", f"Successfully rebuilt index: {index_name}")
                    log_operation("Index Rebuilt", f"Rebuilt index: {index_name}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to rebuild index: {index_name}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rebuild index: {e}")
            log_error("Index Rebuild Failed", e)
    
    def rename_selected_index(self):
        """Rename selected index"""
        try:
            selected_items = self.index_tree.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "No Selection", "Please select an index to rename.")
                return
            
            if len(selected_items) > 1:
                QMessageBox.information(self, "Multiple Selection", "Please select only one index to rename.")
                return
            
            old_name = selected_items[0].data(0, 0)
            
            # Get new name from user
            from PyQt6.QtWidgets import QInputDialog
            new_name, ok = QInputDialog.getText(
                self, "Rename Index", 
                f"Enter new name for index '{old_name}':",
                text=old_name
            )
            
            if not ok or not new_name.strip():
                return
            
            new_name = new_name.strip()
            
            # Validate new name
            if new_name == old_name:
                QMessageBox.information(self, "No Change", "The new name is the same as the current name.")
                return
            
            # Check if name contains invalid characters
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', new_name):
                QMessageBox.warning(self, "Invalid Name", 
                    "Index name can only contain letters, numbers, underscores, and hyphens.")
                return
            
            # Check if name already exists
            if self.index_manager.index_exists(new_name):
                QMessageBox.warning(self, "Name Exists", f"An index with the name '{new_name}' already exists.")
                return
            
            # Confirm rename
            reply = QMessageBox.question(
                self, "Confirm Rename",
                f"Are you sure you want to rename index '{old_name}' to '{new_name}'?\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Show progress
                progress = QMessageBox(self)
                progress.setWindowTitle("Renaming Index")
                progress.setText(f"Renaming index '{old_name}' to '{new_name}'...")
                progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
                progress.show()
                QApplication.processEvents()
                
                # Rename index
                success = self.index_manager.rename_index(old_name, new_name)
                progress.close()
                
                if success:
                    self.refresh_index_list()
                    QMessageBox.information(self, "Success", f"Successfully renamed index from '{old_name}' to '{new_name}'")
                    log_operation("Index Renamed", f"Renamed index from '{old_name}' to '{new_name}'")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to rename index from '{old_name}' to '{new_name}'")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rename index: {e}")
            log_error("Index Rename Failed", e)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("AI-System-DocAI V5I")
    app.setApplicationVersion("5I.2025")
    app.setOrganizationName("AI-System-Solutions")
    
    # Create and show main window
    window = EnterpriseApp()
    window.show()
    
    # Log startup
    log_operation("Application Started", "Enterprise UI initialized")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
