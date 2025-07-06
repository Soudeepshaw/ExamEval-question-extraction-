import os
import mimetypes
from typing import Optional
from pathlib import Path

def get_file_mime_type(file_path: str) -> str:
    """Get MIME type of a file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def ensure_directory_exists(directory_path: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def clean_filename(filename: str) -> str:
    """Clean filename by removing special characters"""
    import re
    # Remove special characters except dots and hyphens
    cleaned = re.sub(r'[^\w\-_\.]', '_', filename)
    return cleaned

def validate_pdf_extension(filename: str) -> bool:
    """Validate if file has PDF extension"""
    return filename.lower().endswith('.pdf')
