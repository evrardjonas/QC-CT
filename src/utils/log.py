"""
Système de logging CT-QC
"""

import logging
import logging.config
import os
from datetime import datetime
from typing import Dict, Any
import functools


def setup_logging(config: Dict[str, Any]):
    """Configure le système de logging"""
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': config.get('console_level', 'INFO'),
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': config.get('file_level', 'DEBUG'),
                'formatter': 'detailed',
                'filename': os.path.join(config.get('log_dir', 'logs'), 'ctqc.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': 'DEBUG',
                'handlers': ['console', 'file']
            },
            'engine': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'core': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        }
    }
    
    # Création du dossier de logs
    os.makedirs(config.get('log_dir', 'logs'), exist_ok=True)
    
    logging.config.dictConfig(log_config)


def log_execution(func):
    """Décorateur pour logger l'exécution des fonctions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Executing {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__} successfully")
            return result
        except Exception as e:
            logger.error(f"Failed {func.__name__}: {e}")
            raise
    
    return wrapper


class PerformanceLogger:
    """Logger de performance"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = datetime.now()
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        self.logger.info(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.info(f"Completed {self.operation_name} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed {self.operation_name} after {duration:.2f}s: {exc_val}")
    
    def checkpoint(self, checkpoint_name: str):
        """Marque un point de contrôle"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.debug(f"Checkpoint {checkpoint_name} at {duration:.2f}s")