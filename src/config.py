"""
Configuration Management for AI-System-DocAI V5I (CPU-only, Internal LAN)
Handles persistent configuration, paths, and system configuration
"""
from __future__ import annotations
import os
import toml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Literal, List
import platform

# Force CPU-only mode globally
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# System Information
SYSTEM_INFO = {
    "os": platform.system(),
    "os_version": platform.version(),
    "architecture": platform.architecture()[0],
    "processor": platform.processor(),
    "python_version": platform.python_version(),
}

# Default Configuration
DEFAULT_CONFIG = {
    "app": {
        "name": "AI-System-DocAI",
        "version": "5I.2025",
        "publisher": "AI-System-Solutions",
        "debug": False,
        "log_level": "INFO",
    },
    "paths": {
        "index_dir": "faiss_index",
        "logs_dir": "logs",
        "cache_dir": "cache",
        "config_dir": None,  # Will be set based on OS
    },
    "llm": {
        "backend": "openai",  # openai, anthropic, gemini, ollama, hf_local, none
        "model_path": "",
        "model_type": "gpt-4o-mini",
        "context_length": 4096,
        "temperature": 0.7,
        "max_tokens": 600,
        "threads": None,  # Auto-detect for CPU
    },
    "embeddings": {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "device": "cpu",  # Always CPU
        "batch_size": 8,
        "max_seq_length": 512,
    },
    "indexing": {
        "chunk_size": 800,
        "chunk_overlap": 120,
        "index_type": "hnsw",
        "persist_every": 2000,
    },
    "retrieval": {
        "top_k": 12,
        "min_similarity": 0.25,
        "use_bm25": True,
        "dense_weight": 0.6,
        "sparse_weight": 0.4,
        "context_window": 3,
        "rerank": False,
        "chunk_size": 800,
        "chunk_overlap": 120,
    },
    "reasoning": {
        "max_tokens": 600,
        "temperature": 0.7,
        "use_streaming": True,
        "show_steps": True,
        "confidence_threshold": 0.5,
    },
    "security": {
        "internal_lan_mode": True,
        "allowed_ips": [],  # Empty = all LAN IPs allowed
        "require_auth": False,
        "audit_logging": True,
        "rate_limit_per_ip": 100,  # queries per hour
        "encrypt_index": False,
    },
    "enterprise": {
        "multi_user": False,
        "audit_logging": True,
        "backup_enabled": True,
        "auto_update": False,
    }
}

@dataclass
class AppConfig:
    name: str
    version: str
    publisher: str
    debug: bool
    log_level: str

@dataclass
class PathsConfig:
    index_dir: str
    logs_dir: str
    cache_dir: str
    config_dir: str

@dataclass
class LLMConfig:
    backend: Literal["openai", "anthropic", "gemini", "ollama", "hf_local", "llama_cpp", "none"]
    model_path: str
    model_type: str
    context_length: int
    temperature: float
    max_tokens: int
    threads: Optional[int] = None

@dataclass
class EmbeddingsConfig:
    model: str
    device: str  # Always "cpu"
    batch_size: int
    max_seq_length: int

@dataclass
class IndexingConfig:
    chunk_size: int
    chunk_overlap: int
    index_type: str
    persist_every: int

@dataclass
class RetrievalConfig:
    top_k: int
    min_similarity: float
    use_bm25: bool
    dense_weight: float
    sparse_weight: float
    context_window: int
    rerank: bool
    chunk_size: int
    chunk_overlap: int

@dataclass
class ReasoningConfig:
    max_tokens: int
    temperature: float
    use_streaming: bool
    show_steps: bool
    confidence_threshold: float

@dataclass
class SecurityConfig:
    internal_lan_mode: bool
    allowed_ips: List[str]
    require_auth: bool
    audit_logging: bool
    rate_limit_per_ip: int
    encrypt_index: bool

@dataclass
class EnterpriseConfig:
    multi_user: bool
    audit_logging: bool
    backup_enabled: bool
    auto_update: bool

@dataclass
class Config:
    app: AppConfig
    paths: PathsConfig
    llm: LLMConfig
    embeddings: EmbeddingsConfig
    indexing: IndexingConfig
    retrieval: RetrievalConfig
    reasoning: ReasoningConfig
    security: SecurityConfig
    enterprise: EnterpriseConfig

class ConfigManager:
    """Configuration manager for CPU-only, Internal LAN deployment"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._ensure_directories()
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration path based on OS"""
        if SYSTEM_INFO["os"] == "Windows":
            base_path = Path(os.environ.get("LOCALAPPDATA", ""))
        else:
            base_path = Path.home() / ".config"
        
        config_dir = base_path / "AI-System-DocAI"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.toml"
    
    def _load_config(self) -> Config:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                config_data = toml.load(self.config_path)
                return self._merge_config(config_data)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        
        return self._create_default_config()
    
    def _merge_config(self, config_data: Dict[str, Any]) -> Config:
        """Merge loaded config with defaults"""
        merged = DEFAULT_CONFIG.copy()
        
        # Deep merge
        for section, values in config_data.items():
            if section in merged and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
        
        return self._create_config_from_dict(merged)
    
    def _create_default_config(self) -> Config:
        """Create default configuration"""
        return self._create_config_from_dict(DEFAULT_CONFIG)
    
    def _create_config_from_dict(self, config_dict: Dict[str, Any]) -> Config:
        """Create Config object from dictionary"""
        # Set OS-specific paths
        if config_dict["paths"]["config_dir"] is None:
            config_dict["paths"]["config_dir"] = str(self.config_path.parent)
        
        return Config(
            app=AppConfig(**config_dict["app"]),
            paths=PathsConfig(**config_dict["paths"]),
            llm=LLMConfig(**config_dict["llm"]),
            embeddings=EmbeddingsConfig(**config_dict["embeddings"]),
            indexing=IndexingConfig(**config_dict["indexing"]),
            retrieval=RetrievalConfig(**config_dict["retrieval"]),
            reasoning=ReasoningConfig(**config_dict["reasoning"]),
            security=SecurityConfig(**config_dict["security"]),
            enterprise=EnterpriseConfig(**config_dict["enterprise"])
        )
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.get_index_path(),
            self.get_logs_path(),
            self.get_cache_path(),
            self.config_path.parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_dict = asdict(self.config)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_dict, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_index_path(self) -> Path:
        """Get index directory path"""
        return Path(self.config.paths.index_dir).resolve()
    
    def get_logs_path(self) -> Path:
        """Get logs directory path"""
        return Path(self.config.paths.logs_dir).resolve()
    
    def get_cache_path(self) -> Path:
        """Get cache directory path"""
        return Path(self.config.paths.cache_dir).resolve()
    
    def get_config_path(self) -> Path:
        """Get configuration file path"""
        return self.config_path
    
    def get_system_info(self) -> Dict[str, str]:
        """Get system information"""
        return SYSTEM_INFO.copy()
    
    def get_llm_device(self) -> str:
        """Get LLM device string (always CPU)"""
        return "CPU"
    
    def get_optimal_batch_size(self, model_type: str = "embeddings") -> int:
        """Get optimal batch size for CPU operation"""
        if model_type == "embeddings":
            return self.config.embeddings.batch_size
        elif model_type == "llm":
            return 128
        return 8

# Global configuration manager
config_manager = ConfigManager()

# Embedding models
EMBED_MODELS = {
    "sentence-transformers/all-MiniLM-L6-v2": {
        "display": "MiniLM-L6-v2 (384d, fast)",
        "dimension": 384,
        "size": "80MB"
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "display": "MPNet-Base-v2 (768d, accurate)",
        "dimension": 768,
        "size": "420MB"
    },
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
        "display": "Multilingual MiniLM-L12 (384d)",
        "dimension": 384,
        "size": "120MB"
    }
}

# Index types
INDEX_TYPES = [
    ("flat", "FAISS Flat (precise, RAM)"),
    ("hnsw", "FAISS HNSW (ANN, scales well)"),
    ("ivf", "FAISS IVF Flat (ANN, large datasets)"),
]

# Check if llama-cpp is available
try:
    import llama_cpp
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

# Build LLM backends based on availability
LLM_BACKENDS = [
    ("none", "No LLM (citations only)"),
    ("openai", "OpenAI / compatible"),
    ("anthropic", "Anthropic Claude"),
    ("gemini", "Google Gemini"),
    ("ollama", "Ollama (local server)"),
    ("hf_local", "Local HuggingFace"),
]

if LLAMA_CPP_AVAILABLE:
    LLM_BACKENDS.insert(1, ("llama_cpp", "Local LlamaCpp (GGUF)"))

# Legacy DEFAULTS for backward compatibility
DEFAULTS = {
    "embed_model": config_manager.config.embeddings.model,
    "index_type": config_manager.config.indexing.index_type,
    "bm25": config_manager.config.retrieval.use_bm25,
    "k": config_manager.config.retrieval.top_k,
    "min_sim": config_manager.config.retrieval.min_similarity,
}

# IndexConfig for backward compatibility
@dataclass
class IndexConfig:
    embed_model: str
    index_type: str

