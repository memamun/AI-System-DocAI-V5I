"""
Embeddings Manager for AI-System-DocAI V5I (CPU-only)
Handles sentence-transformers embeddings with forced CPU operation
"""
from __future__ import annotations
import os
import numpy as np
from pathlib import Path
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
import logging

from config import config_manager

logger = logging.getLogger(__name__)

# Force CPU-only operation globally
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

def download_model(model_name: str = None) -> bool:
    """
    Download and cache embedding model for offline use

    Args:
        model_name: Name of the model to download (uses config default if None)

    Returns:
        True if successful, False otherwise
    """
    if model_name is None:
        model_name = config_manager.config.embeddings.model

    print(f"Downloading embedding model: {model_name}")
    print("This may take several minutes depending on your internet connection...")

    try:
        success = ensure_model_available(model_name)
        if success:
            print(f"✅ Model {model_name} downloaded successfully!")
            print(f"📁 Cached in: {config_manager.get_cache_path() / 'transformers'}")
            return True
        else:
            print(f"❌ Failed to download model {model_name}")
            return False
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

def get_cache_dir() -> Path:
    """Get the cache directory for transformers models"""
    cache_dir = config_manager.get_cache_path() / "transformers"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def ensure_model_available(model_name: str) -> bool:
    """
    Ensure the embedding model is available locally (pre-download if needed)

    Args:
        model_name: Name of the sentence-transformers model

    Returns:
        True if model is available, False otherwise
    """
    cache_dir = get_cache_dir()

    # Set environment variables for sentence-transformers
    os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
    os.environ["HF_HOME"] = str(cache_dir)
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"
    os.environ["HF_HUB_ETAG_TIMEOUT"] = "30"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir)

    # Check if model files already exist (try both cache structures)
    model_cache_path1 = cache_dir / "models" / model_name.replace("/", "--")
    model_cache_path2 = cache_dir / model_name.replace("/", "--")

    if model_cache_path1.exists() or model_cache_path2.exists():
        logger.info(f"Model {model_name} already cached")
        return True

    logger.info(f"Pre-downloading embedding model: {model_name}")
    try:
        # Try to load the model (this will trigger download if needed)
        model = SentenceTransformer(
            model_name,
            device="cpu",
            cache_folder=str(cache_dir),
            trust_remote_code=False
        )
        logger.info(f"Model {model_name} downloaded and cached successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to pre-download model {model_name}: {e}")
        return False

def load_embedding_model(model_name: str) -> SentenceTransformer:
    """
    Load a sentence-transformers model with CPU-only operation
    
    Args:
        model_name: Name or path of the sentence-transformers model
    
    Returns:
        Loaded SentenceTransformer model (CPU-only)
    """
    cache_dir = get_cache_dir()
    
    # Set environment variables for transformers cache and better timeout handling
    os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
    os.environ["HF_HOME"] = str(cache_dir)
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir)
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"  # 60 second timeout
    os.environ["HF_HUB_ETAG_TIMEOUT"] = "30"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"  # Disable telemetry
    # Try to force offline mode if model exists locally
    os.environ["HF_HUB_OFFLINE"] = "1"

    # Try to find the local model path first
    local_model_path = cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
    if local_model_path.exists():
        # Find the actual model directory
        model_dirs = list(local_model_path.glob("*"))
        if model_dirs:
            actual_model_path = model_dirs[0]
            logger.info(f"Found local model at: {actual_model_path}")
            try:
                model = SentenceTransformer(
                    str(actual_model_path),
                    device="cpu",
                    trust_remote_code=False
                )
                logger.info(f"Successfully loaded {model_name} from local cache")
                logger.info(f"Model dimension: {model.get_sentence_embedding_dimension()}")
                return model
            except Exception as e:
                logger.warning(f"Failed to load from local path, trying online method: {e}")

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Loading embedding model: {model_name} (CPU-only) - Attempt {attempt + 1}/{max_retries}")

            # Force CPU device with additional parameters for reliability
            model = SentenceTransformer(
                model_name,
                device="cpu",
                cache_folder=str(cache_dir),
                trust_remote_code=False  # Security: don't trust remote code
            )

            logger.info(f"Successfully loaded {model_name} on CPU")
            logger.info(f"Model dimension: {model.get_sentence_embedding_dimension()}")

            return model

        except Exception as e:
            logger.warning(f"Failed to load embedding model {model_name} (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                import time
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"All attempts failed to load embedding model {model_name}")
                raise

class EmbeddingManager:
    """Manages embeddings generation with CPU-only operation"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding manager
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name or config_manager.config.embeddings.model
        self.model = None
        self.dimension = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            self.model = load_embedding_model(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding manager initialized with {self.model_name} (dim={self.dimension})")
        except Exception as e:
            logger.error(f"Failed to initialize embedding manager: {e}")
            raise
    
    def embed_texts(
        self,
        texts: Union[str, List[str]],
        batch_size: Optional[int] = None,
        show_progress: bool = False,
        normalize: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts to embed
            batch_size: Batch size for processing (defaults to config)
            show_progress: Whether to show progress bar
            normalize: Whether to normalize embeddings
        
        Returns:
            Numpy array of embeddings (shape: [num_texts, dimension])
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        # Convert single text to list
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        # Get batch size from config if not provided
        if batch_size is None:
            batch_size = config_manager.config.embeddings.batch_size
        
        try:
            logger.debug(f"Embedding {len(texts)} texts with batch_size={batch_size}")
            
            # Generate embeddings (CPU-only)
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                device="cpu",
                normalize_embeddings=normalize,
                convert_to_numpy=True
            )
            
            logger.debug(f"Generated embeddings with shape: {embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def embed_query(self, query: str, normalize: bool = False) -> np.ndarray:
        """
        Generate embedding for a single query
        
        Args:
            query: Query text to embed
            normalize: Whether to normalize the embedding
        
        Returns:
            Numpy array of the query embedding (shape: [dimension])
        """
        embeddings = self.embed_texts([query], batch_size=1, normalize=normalize)
        return embeddings[0]
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if self.model is None:
            return {"error": "Model not loaded"}
        
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": "cpu",
            "max_seq_length": self.model.max_seq_length,
            "cache_dir": str(get_cache_dir())
        }
    
    def reload_model(self, model_name: Optional[str] = None):
        """
        Reload the embedding model (useful for switching models)
        
        Args:
            model_name: New model name (if changing models)
        """
        if model_name:
            self.model_name = model_name
        
        logger.info(f"Reloading embedding model: {self.model_name}")
        self._load_model()

# Global embedding manager instance (lazy initialization)
_global_embedding_manager: Optional[EmbeddingManager] = None

def get_embedding_manager() -> EmbeddingManager:
    """Get or create the global embedding manager instance"""
    global _global_embedding_manager
    
    if _global_embedding_manager is None:
        _global_embedding_manager = EmbeddingManager()
    
    return _global_embedding_manager

def embed_texts(texts: Union[str, List[str]], **kwargs) -> np.ndarray:
    """Convenience function to embed texts using the global manager"""
    manager = get_embedding_manager()
    return manager.embed_texts(texts, **kwargs)

def embed_query(query: str, **kwargs) -> np.ndarray:
    """Convenience function to embed a query using the global manager"""
    manager = get_embedding_manager()
    return manager.embed_query(query, **kwargs)

