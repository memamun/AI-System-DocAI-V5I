"""
Enterprise Logging System for AI-System-DocAI V5I
Provides comprehensive logging with startup and runtime logs
"""
from __future__ import annotations
import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import platform
import psutil
from typing import Optional

from config import config_manager

class EnterpriseLogger:
    """Enterprise-grade logging system with multiple handlers and formats"""
    
    def __init__(self, app_name: str = "AI-System-DocAI"):
        self.app_name = app_name
        self.logs_dir = config_manager.get_logs_path()
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Log startup information
        self._log_startup_info()
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 1. Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # 2. Startup log file (all levels)
        startup_log_path = self.logs_dir / f"{self.app_name}_Startup.log"
        startup_handler = logging.FileHandler(startup_log_path, mode='a', encoding='utf-8')
        startup_handler.setLevel(logging.DEBUG)
        startup_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(startup_handler)
        
        # 3. Runtime log file (rotating, INFO and above)
        runtime_log_path = self.logs_dir / f"{self.app_name}_Runtime.log"
        runtime_handler = logging.handlers.RotatingFileHandler(
            runtime_log_path, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        runtime_handler.setLevel(logging.INFO)
        runtime_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(runtime_handler)
        
        # 4. Error log file (ERROR and above)
        error_log_path = self.logs_dir / f"{self.app_name}_Errors.log"
        error_handler = logging.FileHandler(error_log_path, mode='a', encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # 5. Audit log file (for enterprise features)
        if config_manager.config.enterprise.audit_logging:
            audit_log_path = self.logs_dir / f"{self.app_name}_Audit.log"
            audit_handler = logging.FileHandler(audit_log_path, mode='a', encoding='utf-8')
            audit_handler.setLevel(logging.INFO)
            audit_formatter = logging.Formatter(
                '%(asctime)s | AUDIT | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            audit_handler.setFormatter(audit_formatter)
            self.logger.addHandler(audit_handler)
    
    def _log_startup_info(self):
        """Log comprehensive startup information"""
        self.logger.info("=" * 80)
        self.logger.info(f"{self.app_name} V{config_manager.config.app.version} Starting Up")
        self.logger.info("=" * 80)
        
        # System Information
        self.logger.info("SYSTEM INFORMATION:")
        system_info = config_manager.get_system_info()
        for key, value in system_info.items():
            self.logger.info(f"  {key}: {value}")
        
        # Memory Information
        try:
            memory = psutil.virtual_memory()
            self.logger.info(f"  Total RAM: {memory.total / (1024**3):.1f} GB")
            self.logger.info(f"  Available RAM: {memory.available / (1024**3):.1f} GB")
            self.logger.info(f"  RAM Usage: {memory.percent:.1f}%")
        except Exception as e:
            self.logger.warning(f"Could not get memory info: {e}")
        
        # CPU Information
        try:
            self.logger.info(f"  CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
            self.logger.info(f"  CPU Usage: {psutil.cpu_percent(interval=1):.1f}%")
        except Exception as e:
            self.logger.warning(f"Could not get CPU info: {e}")
        
        # Configuration
        self.logger.info("CONFIGURATION:")
        self.logger.info(f"  Config Path: {config_manager.config_path}")
        self.logger.info(f"  Index Dir: {config_manager.get_index_path()}")
        self.logger.info(f"  Logs Dir: {self.logs_dir}")
        self.logger.info(f"  LLM Backend: {config_manager.config.llm.backend}")
        self.logger.info(f"  Embedding Model: {config_manager.config.embeddings.model}")
        self.logger.info(f"  Device: CPU (forced)")
        
        # Security Settings
        self.logger.info("SECURITY SETTINGS:")
        self.logger.info(f"  Internal LAN Mode: {config_manager.config.security.internal_lan_mode}")
        self.logger.info(f"  Audit Logging: {config_manager.config.security.audit_logging}")
        
        # Enterprise Settings
        if config_manager.config.enterprise.audit_logging:
            self.logger.info("ENTERPRISE FEATURES:")
            self.logger.info(f"  Multi-User: {config_manager.config.enterprise.multi_user}")
            self.logger.info(f"  Audit Logging: {config_manager.config.enterprise.audit_logging}")
            self.logger.info(f"  Backup Enabled: {config_manager.config.enterprise.backup_enabled}")
        
        self.logger.info("=" * 80)
    
    def log_operation(self, operation: str, details: str = "", user: str = "system"):
        """Log an operation for audit purposes"""
        if config_manager.config.enterprise.audit_logging:
            self.logger.info(f"OPERATION | {user} | {operation} | {details}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log an error with context"""
        self.logger.error(f"ERROR | {context} | {type(error).__name__}: {str(error)}", exc_info=True)
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics"""
        self.logger.info(f"PERFORMANCE | {operation} | {duration:.3f}s | {details}")
    
    def log_model_usage(self, model_name: str, tokens_generated: int, duration: float):
        """Log model usage statistics"""
        self.logger.info(f"MODEL_USAGE | {model_name} | {tokens_generated} tokens | {duration:.3f}s")
    
    def get_log_files(self) -> dict:
        """Get information about log files"""
        log_files = {}
        
        for log_file in self.logs_dir.glob(f"{self.app_name}_*.log"):
            try:
                stat = log_file.stat()
                log_files[log_file.name] = {
                    "path": str(log_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "lines": sum(1 for _ in open(log_file, 'r', encoding='utf-8'))
                }
            except Exception as e:
                log_files[log_file.name] = {"error": str(e)}
        
        return log_files
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in self.logs_dir.glob(f"{self.app_name}_*.log"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old log file: {log_file.name}")
            except Exception as e:
                self.logger.warning(f"Could not clean up {log_file.name}: {e}")

# Global logger instance
enterprise_logger = EnterpriseLogger()

# Convenience functions
def log_info(message: str):
    """Log info message"""
    enterprise_logger.logger.info(message)

def log_warning(message: str):
    """Log warning message"""
    enterprise_logger.logger.warning(message)

def log_error(message: str, error: Optional[Exception] = None):
    """Log error message"""
    if error:
        enterprise_logger.log_error(error, message)
    else:
        enterprise_logger.logger.error(message)

def log_debug(message: str):
    """Log debug message"""
    enterprise_logger.logger.debug(message)

def log_operation(operation: str, details: str = "", user: str = "system"):
    """Log operation for audit"""
    enterprise_logger.log_operation(operation, details, user)

def log_performance(operation: str, duration: float, details: str = ""):
    """Log performance metrics"""
    enterprise_logger.log_performance(operation, duration, details)

