"""
Fonctions helper CT-QC
"""

import os
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd


def generate_id() -> str:
    """Génère un ID unique"""
    return uuid.uuid4().hex[:16]


def calculate_hash(content: str) -> str:
    """Calcule le hash d'un contenu"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convertit en float de manière sécurisée"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convertit en int de manière sécurisée"""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def format_timestamp(timestamp: datetime = None) -> str:
    """Formate un timestamp"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.isoformat()


def ensure_directory(path: str):
    """S'assure qu'un dossier existe"""
    os.makedirs(path, exist_ok=True)


def dataframe_to_records(df: pd.DataFrame) -> List[Dict]:
    """Convertit un DataFrame en liste de dictionnaires"""
    return df.to_dict('records')


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Découpe une liste en chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def human_readable_size(size_bytes: int) -> str:
    """Convertit une taille en bytes en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def timer_func(func):
    """Décorateur pour mesurer le temps d'exécution"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    
    return wrapper