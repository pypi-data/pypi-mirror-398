"""
Configuration Management for SanTOK
Handles environment variables and configuration
"""

import os
from typing import Optional
from pathlib import Path


class Config:
    """Configuration class for SanTOK"""
    
    # Default values
    DEFAULT_PORT = 8000
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_DATA_DIR = "data"
    DEFAULT_MODELS_DIR = "models"
    DEFAULT_OUTPUT_DIR = "outputs"
    
    @staticmethod
    def get_port(default: Optional[int] = None) -> int:
        """
        Get server port from environment variable or default
        
        Args:
            default: Default port if not set in environment
            
        Returns:
            Port number (1-65535)
        """
        if default is None:
            default = Config.DEFAULT_PORT
        
        port_str = os.getenv('PORT') or os.getenv('SANTOK_PORT')
        if port_str:
            try:
                port = int(port_str)
                if 1 <= port <= 65535:
                    return port
            except ValueError:
                pass
        
        return default
    
    @staticmethod
    def get_host(default: Optional[str] = None) -> str:
        """
        Get server host from environment variable or default
        
        Args:
            default: Default host if not set in environment
            
        Returns:
            Host string
        """
        if default is None:
            default = Config.DEFAULT_HOST
        
        return os.getenv('HOST') or os.getenv('SANTOK_HOST') or default
    
    @staticmethod
    def get_log_level(default: Optional[str] = None) -> str:
        """
        Get log level from environment variable or default
        
        Args:
            default: Default log level if not set in environment
            
        Returns:
            Log level string
        """
        if default is None:
            default = Config.DEFAULT_LOG_LEVEL
        
        return os.getenv('LOG_LEVEL') or os.getenv('SANTOK_LOG_LEVEL') or default
    
    @staticmethod
    def get_data_dir(default: Optional[str] = None) -> Path:
        """
        Get data directory from environment variable or default
        
        Args:
            default: Default data directory if not set in environment
            
        Returns:
            Path to data directory
        """
        if default is None:
            default = Config.DEFAULT_DATA_DIR
        
        dir_str = os.getenv('DATA_DIR') or os.getenv('SANTOK_DATA_DIR') or default
        return Path(dir_str).expanduser().resolve()
    
    @staticmethod
    def get_models_dir(default: Optional[str] = None) -> Path:
        """
        Get models directory from environment variable or default
        
        Args:
            default: Default models directory if not set in environment
            
        Returns:
            Path to models directory
        """
        if default is None:
            default = Config.DEFAULT_MODELS_DIR
        
        dir_str = os.getenv('MODELS_DIR') or os.getenv('SANTOK_MODELS_DIR') or default
        return Path(dir_str).expanduser().resolve()
    
    @staticmethod
    def get_output_dir(default: Optional[str] = None) -> Path:
        """
        Get output directory from environment variable or default
        
        Args:
            default: Default output directory if not set in environment
            
        Returns:
            Path to output directory
        """
        if default is None:
            default = Config.DEFAULT_OUTPUT_DIR
        
        dir_str = os.getenv('OUTPUT_DIR') or os.getenv('SANTOK_OUTPUT_DIR') or default
        return Path(dir_str).expanduser().resolve()
    
    @staticmethod
    def get_log_file() -> Optional[str]:
        """
        Get log file path from environment variable
        
        Returns:
            Log file path or None
        """
        return os.getenv('LOG_FILE') or os.getenv('SANTOK_LOG_FILE')


def get_config() -> Config:
    """
    Get configuration instance
    
    Returns:
        Config instance
    """
    return Config()

