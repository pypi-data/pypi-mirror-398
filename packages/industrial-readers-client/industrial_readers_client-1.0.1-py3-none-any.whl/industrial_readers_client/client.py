import requests
from typing import Optional, Dict, Any, Union
from pathlib import Path
import json

class IndustrialReadersClient:
    """High-performance client for Industrial Readers Server"""
    
    def __init__(self, base_url: str = "http://localhost:9847", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def health(self) -> Dict[str, Any]:
        """Check server health"""
        response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def detect(self, file_path: Union[str, Path]) -> str:
        """Detect file format"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(f"{self.base_url}/detect", files=files, timeout=self.timeout)
        response.raise_for_status()
        return response.json()['format']
    
    def read(self, file_path: Union[str, Path], **params) -> Dict[str, Any]:
        """Read file with auto-detection"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(f"{self.base_url}/read", files=files, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def read_format(self, file_path: Union[str, Path], format_type: str, **params) -> Dict[str, Any]:
        """Read file with specific format"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(f"{self.base_url}/read/{format_type}", files=files, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    # Convenience methods
    def read_excel(self, file_path: Union[str, Path], max_rows: Optional[int] = None, max_cells: Optional[int] = None) -> Dict[str, Any]:
        params = {}
        if max_rows: params['max_rows'] = max_rows
        if max_cells: params['max_cells'] = max_cells
        return self.read_format(file_path, 'xlsx', **params)
    
    def read_word(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        return self.read_format(file_path, 'docx')
    
    def read_pdf(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        return self.read_format(file_path, 'pdf')
    
    def read_image(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        return self.read_format(file_path, 'image')