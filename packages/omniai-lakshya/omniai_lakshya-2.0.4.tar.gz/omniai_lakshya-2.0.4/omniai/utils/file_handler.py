"""
███████╗███╗   ███╗███╗   ██╗ ██╗ █████╗ 
██╔════╝████╗ ████║████╗  ██║███║██╔══██╗
█████╗  ██╔████╔██║██╔██╗ ██║╚██║╚█████╔╝
██╔══╝  ██║╚██╔╝██║██║╚██╗██║ ██║██╔══██╗
███████╗██║ ╚═╝ ██║██║ ╚████║ ██║╚█████╔╝
╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═╝ ╚════╝ 

O M N I   A I
Christmas Edition 2025
Created by: Lakshya Gupta
Date: 25 December 2025

FREE for everyone to use forever.
But this is MY work - please don't remove my name.
"""

# Your existing code continues here...
import os
import pandas as pd

class FileHandler:
    """Handles file operations for OmniAI"""
    
    @staticmethod
    def detect_file_type(file_path):
        """Detect file type from extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        file_types = {
            '.csv': 'CSV',
            '.xlsx': 'Excel',
            '.xls': 'Excel',
            '.parquet': 'Parquet',
            '.json': 'JSON',
            '.h5': 'HDF5',
            '.feather': 'Feather'
        }
        
        return file_types.get(ext, 'Unknown')
    
    @staticmethod
    def get_file_size(file_path):
        """Get file size in human-readable format"""
        size_bytes = os.path.getsize(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} PB"