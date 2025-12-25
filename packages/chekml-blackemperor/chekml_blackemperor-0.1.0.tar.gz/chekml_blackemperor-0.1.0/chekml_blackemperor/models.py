import os
import tempfile
import importlib.util
import inspect
import torch.nn as nn
import glob
from typing import Dict, Optional, Type, Any, List
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        self.local_models = {}
        self.drive_models = {}
        self._load_local_models()
    
    def _load_local_models(self):
        """Load models from model.py and from the `local_models/` directory."""
        # Base directory (package directory) to find model files reliably
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Load single-file model.py if present next to package
        paths = []
        model_py = os.path.join(base_dir, "model.py")
        if os.path.exists(model_py):
            paths.append(("model", model_py))

        # Load all files under local_models/ inside package
        lm_dir = os.path.join(base_dir, 'local_models')
        if os.path.isdir(lm_dir):
            for py in glob.glob(os.path.join(lm_dir, "*.py")):
                name = os.path.splitext(os.path.basename(py))[0]
                paths.append((f"local_{name}", py))

        for mod_name, path in paths:
            try:
                spec = importlib.util.spec_from_file_location(mod_name, path)
                model_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(model_module)

                # Find all nn.Module subclasses
                for name, obj in inspect.getmembers(model_module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, nn.Module) and 
                        obj != nn.Module):
                        self.local_models[name.lower()] = obj
                        logger.info(f"Registered local model: {name} from {path}")
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
    
    def register_drive_model(self, model_name: str, drive_client):
        """Register a model from Google Drive"""
        self.drive_models[model_name] = drive_client
    
    def list_local_models(self):
        """List all available local models"""
        return list(self.local_models.keys())
    
    def list_drive_models(self):
        """List all available drive models"""
        return list(self.drive_models.keys())
    
    def get_model(self, model_name: str):
        """Get model class by name"""
        model_name = model_name.lower()
        
        # Try local first
        if model_name in self.local_models:
            return self.local_models[model_name]
        
        # Try drive models
        if model_name in self.drive_models:
            # This would need to download and load the model
            # Implementation depends on how models are stored in drive
            pass
        
        return None

class ModelLoader:
    def __init__(self):
        self.registry = ModelRegistry()
    
    def load_local_model(self, model_name: str) -> Optional[Type[nn.Module]]:
        """Load model from local model.py"""
        return self.registry.get_model(model_name)
    
    async def load_drive_model(self, model_name: str, drive_client) -> Optional[Type[nn.Module]]:
        """Load model from Google Drive"""
        try:
            # Download model file
            model_content = drive_client.download_model(model_name)
            
            if not model_content:
                logger.error(f"Model {model_name} not found in Google Drive")
                return None
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as temp_file:
                if isinstance(model_content, bytes):
                    temp_file.write(model_content)
                else:
                    temp_file.write(model_content.encode())
                temp_path = temp_file.name
            
            try:
                # Load the module
                spec = importlib.util.spec_from_file_location(f"drive_model_{model_name}", temp_path)
                model_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(model_module)
                
                # Find nn.Module subclass
                for name, obj in inspect.getmembers(model_module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, nn.Module) and 
                        obj != nn.Module):
                        
                        logger.info(f"Loaded model {model_name} from Google Drive")
                        return obj
                
                logger.error(f"No nn.Module found in {model_name}.py from Google Drive")
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        except Exception as e:
            logger.error(f"Failed to load model from drive: {e}")
        
        return None