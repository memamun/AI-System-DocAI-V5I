"""
Streaming UI Components for AI-System-DocAI V5I
Provides real-time display of LLM reasoning process with typing animations
"""
from __future__ import annotations
import time
from typing import Optional, Generator
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QProgressBar, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from streaming_reasoning import StreamingReasoningEngine, StreamingReasoningResult
from llm import BaseLLM
from retrieval import Retriever
from config import config_manager

class StreamingDisplayWidget(QWidget):
    """Widget for displaying streaming reasoning process"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_text = ""
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.update_typing_animation)
        self.typing_speed = 30  # milliseconds per character
        
    def setup_ui(self):
        """Setup the streaming display UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: #2E8B57;")
        header_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        header_layout.addWidget(self.progress_bar)
        
        layout.addLayout(header_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left panel - Answer
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_panel_layout = QVBoxLayout(left_panel)
        
        answer_label = QLabel("Answer")
        answer_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_panel_layout.addWidget(answer_label)
        
        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True)
        self.answer_display.setMaximumHeight(150)
        self.answer_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        left_panel_layout.addWidget(self.answer_display)
        
        content_layout.addWidget(left_panel, 1)
        
        # Right panel - Reasoning
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_panel_layout = QVBoxLayout(right_panel)
        
        reasoning_label = QLabel("Thinking Process")
        reasoning_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_panel_layout.addWidget(reasoning_label)
        
        self.reasoning_display = QTextEdit()
        self.reasoning_display.setReadOnly(True)
        self.reasoning_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        right_panel_layout.addWidget(self.reasoning_display)
        
        content_layout.addWidget(right_panel, 2)
        
        layout.addLayout(content_layout)
        
        # Bottom panel - Current Step
        bottom_panel = QFrame()
        bottom_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        bottom_panel.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 5px;
            }
        """)
        bottom_layout = QVBoxLayout(bottom_panel)
        
        self.current_step_label = QLabel("Current Step: Ready")
        self.current_step_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        bottom_layout.addWidget(self.current_step_label)
        
        layout.addWidget(bottom_panel)
    
    def start_streaming(self):
        """Start the streaming display"""
        self.status_label.setText("Thinking...")
        self.status_label.setStyleSheet("font-weight: bold; color: #ff9800;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.answer_display.clear()
        self.reasoning_display.clear()
        self.current_text = ""
    
    def update_reasoning_result(self, result: StreamingReasoningResult):
        """Update the display with new reasoning result"""
        # Update answer with typing animation
        if result.answer and result.answer != self.current_text:
            self.animate_text(self.answer_display, result.answer)
            self.current_text = result.answer
        
        # Update reasoning chain
        if result.reasoning_chain:
            reasoning_text = "\n\n".join(result.reasoning_chain)
            self.reasoning_display.setPlainText(reasoning_text)
            self.reasoning_display.moveCursor(QTextCursor.MoveOperation.End)
        
        # Update current step
        if result.current_step:
            self.current_step_label.setText(f"Current Step: {result.current_step}")
        
        # Update status when complete
        if result.is_complete:
            self.status_label.setText("Complete")
            self.status_label.setStyleSheet("font-weight: bold; color: #4caf50;")
            self.progress_bar.setVisible(False)
            self.current_step_label.setText("Current Step: Complete")
    
    def animate_text(self, text_widget: QTextEdit, target_text: str):
        """Animate text typing effect"""
        current_text = text_widget.toPlainText()
        if len(target_text) > len(current_text):
            new_text = target_text[:len(current_text) + 1]
            text_widget.setPlainText(new_text)
            text_widget.moveCursor(QTextCursor.MoveOperation.End)
    
    def update_typing_animation(self):
        """Update typing animation"""
        # This can be enhanced for more sophisticated typing effects
        pass
    
    def clear_display(self):
        """Clear the display"""
        self.answer_display.clear()
        self.reasoning_display.clear()
        self.current_text = ""
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: #2E8B57;")
        self.progress_bar.setVisible(False)
        self.current_step_label.setText("Current Step: Ready")

class StreamingAskThread(QThread):
    """Thread for streaming question answering"""
    reasoning_update = pyqtSignal(StreamingReasoningResult)
    error = pyqtSignal(str)
    
    def __init__(self, query: str, retriever: Retriever, llm_backend: BaseLLM):
        super().__init__()
        self.query = query
        self.retriever = retriever
        self.llm_backend = llm_backend
    
    def run(self):
        try:
            # Retrieve relevant snippets
            hits = self.retriever.search(self.query, k=config_manager.config.retrieval.top_k)
            context = self.retriever.gather(hits)
            
            # Convert context to DocumentSnippet format
            from retrieval import DocumentSnippet
            snippets = []
            for i, item in enumerate(context):
                snippet = DocumentSnippet(
                    text=item.get("text", ""),
                    file=item.get("file", f"Document {i+1}"),
                    page=item.get("page"),
                    section=item.get("section"),
                    start_char=item.get("start_char"),
                    end_char=item.get("end_char")
                )
                snippets.append(snippet)
            
            # Create streaming reasoning engine
            reasoning_engine = StreamingReasoningEngine(self.llm_backend)
            
            # Stream the reasoning process
            for result in reasoning_engine.process_query_stream(self.query, snippets):
                self.reasoning_update.emit(result)
                
                # Small delay to make streaming visible
                time.sleep(0.1)
                
        except Exception as e:
            self.error.emit(str(e))

class StreamingChatWidget(QWidget):
    """Complete streaming chat widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.retriever = None
        self.llm_backend = None
        self.current_thread = None
    
    def setup_ui(self):
        """Setup the streaming chat UI"""
        layout = QVBoxLayout(self)
        
        # Input area
        input_layout = QHBoxLayout()
        
        from PyQt6.QtWidgets import QLineEdit, QPushButton
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ask a question about your documents...")
        self.query_input.returnPressed.connect(self.ask_question)
        input_layout.addWidget(self.query_input)
        
        self.ask_button = QPushButton("Ask")
        self.ask_button.clicked.connect(self.ask_question)
        input_layout.addWidget(self.ask_button)
        
        layout.addLayout(input_layout)
        
        # Streaming display
        self.streaming_display = StreamingDisplayWidget()
        layout.addWidget(self.streaming_display)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_display)
        control_layout.addWidget(self.clear_button)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
    
    def set_retriever(self, retriever: Retriever):
        """Set the document retriever"""
        self.retriever = retriever
    
    def set_llm_backend(self, llm_backend: BaseLLM):
        """Set the LLM backend"""
        self.llm_backend = llm_backend
    
    def ask_question(self):
        """Ask a question with streaming response"""
        query = self.query_input.text().strip()
        if not query:
            return
        
        if not self.llm_backend:
            self.streaming_display.status_label.setText("Error: No LLM backend selected")
            self.streaming_display.status_label.setStyleSheet("font-weight: bold; color: #f44336;")
            return
        
        if not self.retriever:
            self.streaming_display.status_label.setText("Error: No document index available")
            self.streaming_display.status_label.setStyleSheet("font-weight: bold; color: #f44336;")
            return
        
        # Start streaming
        self.streaming_display.start_streaming()
        self.ask_button.setEnabled(False)
        self.query_input.clear()
        
        # Start streaming thread
        self.current_thread = StreamingAskThread(query, self.retriever, self.llm_backend)
        self.current_thread.reasoning_update.connect(self.on_reasoning_update)
        self.current_thread.error.connect(self.on_error)
        self.current_thread.finished.connect(self.on_thread_finished)
        self.current_thread.start()
    
    def on_reasoning_update(self, result: StreamingReasoningResult):
        """Handle reasoning update"""
        self.streaming_display.update_reasoning_result(result)
    
    def on_error(self, error_msg: str):
        """Handle error"""
        self.streaming_display.status_label.setText(f"Error: {error_msg}")
        self.streaming_display.status_label.setStyleSheet("font-weight: bold; color: #f44336;")
        self.streaming_display.progress_bar.setVisible(False)
    
    def on_thread_finished(self):
        """Handle thread completion"""
        self.ask_button.setEnabled(True)
        self.query_input.setFocus()
    
    def clear_display(self):
        """Clear the display"""
        self.streaming_display.clear_display()
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.terminate()
            self.current_thread.wait()

