import os
import gdown
import torch
from typing import List, Optional
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import logging

logger = logging.getLogger(__name__)

def get_available_gpus() -> List[str]:
    """Get list of available GPUs"""
    if not torch.cuda.is_available():
        return []
    
    gpus = []
    for i in range(torch.cuda.device_count()):
        gpus.append(f"cuda:{i}")
    
    return gpus

def ensure_model_file(model_id: str = None, model_file: str = "model.py"):
    """Ensure model.py is available, download from Google Drive if needed"""
    if not os.path.exists(model_file) and model_id:
        logger.info(f"Downloading {model_file} from Google Drive...")
        url = f"https://drive.google.com/uc?id={model_id}"
        gdown.download(url, model_file, quiet=False, fuzzy=True)

class GoogleDriveClient:
    def __init__(self, credentials_file: str = None, folder_name: str = "chekml_models"):
        self.credentials_file = credentials_file
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
        
        if credentials_file and os.path.exists(credentials_file):
            self._authenticate()
            self._get_folder_id()
    
    def _authenticate(self):
        """Authenticate with Google Drive"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file
            )
            self.service = build('drive', 'v3', credentials=creds)
            logger.info(f"Authenticated to Google Drive using {self.credentials_file}")
        except Exception as e:
            logger.exception(f"Failed to authenticate with Google Drive: {e}")
            self.service = None
    
    def _get_folder_id(self):
        """Get folder ID for model storage"""
        if not self.service:
            return
        
        try:
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            logger.debug(f"Searching Drive for folder with query: {query}")
            response = self.service.files().list(q=query, spaces='drive').execute()
            
            if response.get('files'):
                self.folder_id = response['files'][0]['id']
            else:
                # Create folder if it doesn't exist
                file_metadata = {
                    'name': self.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=file_metadata, fields='id').execute()
                self.folder_id = folder.get('id')
                
        except Exception as e:
            logger.exception(f"Failed to get folder ID: {e}")
    
    def list_models(self):
        """List all models in Google Drive folder"""
        if not self.service or not self.folder_id:
            return []
        
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            logger.debug(f"Listing files in Drive folder id={self.folder_id}")
            results = self.service.files().list(q=query, fields="files(name)").execute()
            files = results.get('files', [])
            
            # Filter for model files (ending with .py or .pt)
            model_files = []
            for file in files:
                if file['name'].endswith('.py') or file['name'].endswith('.pt'):
                    model_name = os.path.splitext(file['name'])[0]
                    model_files.append(model_name)
            
            return model_files
        except Exception as e:
            logger.exception(f"Failed to list models: {e}")
            return []

    def list_datasets(self):
        """List files in the dataset folder (any extension)."""
        if not self.service or not self.folder_id:
            return []
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields="files(name)").execute()
            files = results.get('files', [])
            # return raw filenames
            return [f['name'] for f in files]
        except Exception as e:
            logger.exception(f"Failed to list datasets: {e}")
            return []

    def download_dataset(self, filename: str):
        """Download arbitrary file from the folder by exact filename."""
        if not self.service or not self.folder_id:
            return None
        try:
            query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            if not files:
                return None
            file_id = files[0]['id']
            request = self.service.files().get_media(fileId=file_id)
            file_handle = io.BytesIO()
            downloader = MediaIoBaseDownload(file_handle, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            logger.info(f"Downloaded dataset {filename} from Drive (file id={file_id})")
            return file_handle.getvalue()
        except Exception as e:
            logger.exception(f"Failed to download dataset {filename}: {e}")
            return None
    
    def download_model(self, model_name: str):
        """Download model from Google Drive"""
        if not self.service or not self.folder_id:
            return None
        
        try:
            # Look for .py file first, then .pt
            for ext in ['.py', '.pt']:
                query = f"name='{model_name}{ext}' and '{self.folder_id}' in parents and trashed=false"
                logger.debug(f"Searching for model on Drive with query: {query}")
                results = self.service.files().list(q=query, fields="files(id, name)").execute()
                files = results.get('files', [])
                
                if files:
                    file_id = files[0]['id']
                    
                    # Download file
                    try:
                        request = self.service.files().get_media(fileId=file_id)
                        file_handle = io.BytesIO()
                        downloader = MediaIoBaseDownload(file_handle, request)
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()
                        logger.info(f"Downloaded {model_name}{ext} from Drive (file id={file_id})")
                        return file_handle.getvalue()
                    except Exception as e:
                        logger.exception(f"Failed while downloading file id={file_id}: {e}")
                        continue
            
            return None
        except Exception as e:
            logger.exception(f"Failed to download model {model_name}: {e}")
            return None
    
    def save_model(self, model_name: str, model_data: bytes, extension: str = '.pt'):
        """Save model to Google Drive"""
        if not self.service or not self.folder_id:
            return False
        
        try:
            # Check if file exists
            query = f"name='{model_name}{extension}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields="files(id)").execute()
            files = results.get('files', [])
            
            file_metadata = {
                'name': f'{model_name}{extension}',
                'parents': [self.folder_id]
            }
            
            media = MediaIoBaseUpload(io.BytesIO(model_data), mimetype='application/octet-stream')
            
            if files:
                # Update existing file
                file_id = files[0]['id']
                self.service.files().update(fileId=file_id, body=file_metadata, media_body=media).execute()
            else:
                # Create new file
                self.service.files().create(body=file_metadata, media_body=media).execute()
            
            logger.info(f"Saved model {model_name}{extension} to Drive")
            return True
        except Exception as e:
            logger.exception(f"Failed to save model {model_name}: {e}")
            return False
