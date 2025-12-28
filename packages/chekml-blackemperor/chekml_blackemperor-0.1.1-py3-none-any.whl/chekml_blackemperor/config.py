import os
import json
from typing import Optional
from dataclasses import dataclass, asdict, field

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    google_drive_enabled: bool = False
    google_drive_credentials: Optional[str] = None
    google_drive_folder: str = "chekml_models"
    plugins_dir: str = "plugins"
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        config = cls()
        
        # Server settings
        config.host = os.getenv("CHEKML_HOST", config.host)
        config.port = int(os.getenv("CHEKML_PORT", config.port))
        
        # Google Drive settings
        config.google_drive_enabled = os.getenv("CHEKML_GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
        config.google_drive_credentials = os.getenv("CHEKML_GOOGLE_CREDENTIALS", config.google_drive_credentials)
        config.google_drive_folder = os.getenv("CHEKML_GOOGLE_FOLDER", config.google_drive_folder)
        
        # Plugin settings
        config.plugins_dir = os.getenv("CHEKML_PLUGINS_DIR", config.plugins_dir)
        config.log_level = os.getenv("CHEKML_LOG_LEVEL", config.log_level)
        
        return config
    
    @classmethod
    def from_file(cls, config_path: str):
        """Load configuration from JSON file"""
        config = cls()
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        # Override with environment variables
        env_config = cls.from_env()
        for key, value in asdict(env_config).items():
            if value is not None:
                setattr(config, key, value)
        
        return config

@dataclass
class WorkerConfig:
    """Worker configuration"""
    server_url: Optional[str] = None
    model_id: Optional[str] = None
    model_file: str = "model.py"
    batch_size: int = 64
    learning_rate: float = 0.01
    max_batches: int = 100
    num_workers: int = 2
    verbose: bool = False
    verbose_interval: int = 10
    dataset_name: Optional[str] = None
    dataset_source: str = "local"  # or 'drive'
    google_drive_enabled: bool = False
    google_drive_credentials: Optional[str] = None
    google_drive_folder: str = "chekml_models"
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        config = cls()
        
        # Server URL from environment variable (support CHEKML_EMPEROR or legacy CHEKML_EMPERROR)
        config.server_url = os.getenv("CHEKML_SERVER_URL") or os.getenv("CHEKML_EMPEROR") or os.getenv("CHEKML_EMPERROR")
        if config.server_url:
            # If provided as short id (no scheme), build ngrok-free wss url
            if not (config.server_url.startswith("ws://") or config.server_url.startswith("wss://") or config.server_url.startswith("http://") or config.server_url.startswith("https://")):
                config.server_url = f"wss://{config.server_url}.ngrok-free.app/ws"
            else:
                # convert http(s) to ws(s) and ensure path /ws
                if config.server_url.startswith("http://") or config.server_url.startswith("https://"):
                    proto = "wss" if config.server_url.startswith("https://") else "ws"
                    host = config.server_url.split("://", 1)[1].rstrip('/')
                    config.server_url = f"{proto}://{host}/ws"
        
        # Model settings
        config.model_id = os.getenv("CHEKML_MODEL_ID", config.model_id)
        config.model_file = os.getenv("CHEKML_MODEL_FILE", config.model_file)
        
        # Training settings
        config.batch_size = int(os.getenv("CHEKML_BATCH_SIZE", config.batch_size))
        config.learning_rate = float(os.getenv("CHEKML_LEARNING_RATE", config.learning_rate))
        config.max_batches = int(os.getenv("CHEKML_MAX_BATCHES", config.max_batches))
        config.num_workers = int(os.getenv("CHEKML_NUM_WORKERS", config.num_workers))
        config.verbose = os.getenv("CHEKML_VERBOSE", str(config.verbose)).lower() == 'true'
        config.verbose_interval = int(os.getenv("CHEKML_VERBOSE_INTERVAL", config.verbose_interval))
        config.dataset_name = os.getenv("CHEKML_DATASET_NAME", config.dataset_name)
        config.dataset_source = os.getenv("CHEKML_DATASET_SOURCE", config.dataset_source)
        
        # Google Drive settings
        config.google_drive_enabled = os.getenv("CHEKML_GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
        config.google_drive_credentials = os.getenv("CHEKML_GOOGLE_CREDENTIALS", config.google_drive_credentials)
        config.google_drive_folder = os.getenv("CHEKML_GOOGLE_FOLDER", config.google_drive_folder)
        
        return config
    
    @classmethod
    def from_file(cls, config_path: str):
        """Load configuration from JSON file"""
        config = cls()
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        # Override with environment variables
        env_config = cls.from_env()
        for key, value in asdict(env_config).items():
            if value is not None:
                setattr(config, key, value)
        
        return config

def Config(config_path: Optional[str] = None):
    """Factory function to get appropriate config"""
    if config_path:
        return ServerConfig.from_file(config_path)
    return ServerConfig.from_env()
