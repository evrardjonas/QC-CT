"""
Gestion de configuration CT-QC
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Charge la configuration depuis un fichier YAML
    """
    if config_path is None:
        # Recherche dans l'ordre de priorité
        possible_paths = [
            'config/production.yml',
            'config/development.yml', 
            'config/default.yml',
            'config.yml'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
        else:
            # Configuration par défaut
            return get_default_config()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Fusion avec la configuration par défaut
        default_config = get_default_config()
        merged_config = _deep_merge(default_config, config)
        
        return merged_config
        
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Retourne la configuration par défaut"""
    return {
        'version': '2025.1.0',
        'environment': 'development',
        
        'paths': {
            'data_root': 'data',
            'templates_dir': 'templates',
            'visits_dir': 'visits',
            'logs_dir': 'logs',
            'config_dir': 'config'
        },
        
        'processing': {
            'default_template': 'auto',
            'strict_validation': False,
            'dry_run': False,
            'workers': 0,
            'batch_size': 10
        },
        
        'templates': {
            'directory': 'templates',
            'auto_detection': True,
            'fallback_template': 'ctqc_base'
        },
        
        'exports': {
            'parquet_enabled': True,
            'access_enabled': True,
            'audit_enabled': True
        },
        
        'storage': {
            'hdf5_path': 'data/operational/CTdb.hdf',
            'visits_archive': 'visits/processed',
            'atomic_writes': True,
            'compression': 'zlib',
            'complevel': 9
        },
        
        'parquet': {
            'compression': 'ZSTD',
            'row_group_size': 100000,
            'partitioning': ['year', 'hospital', 'system']
        },
        
        'access': {
            'delimiter': ',',
            'encoding': 'utf-8',
            'quote_all': True
        },
        
        'logging': {
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'log_dir': 'logs'
        },
        
        'engine': {
            'extraction': {
                'max_sheets': 50,
                'max_rows_per_sheet': 10000,
                'timeout_seconds': 300
            },
            'validation': {
                'strict_mode': False,
                'log_warnings': True
            }
        }
    }


def _deep_merge(base: Dict, overlay: Dict) -> Dict:
    """Fusion récursive de dictionnaires"""
    result = base.copy()
    
    for key, value in overlay.items():
        if (key in base and isinstance(base[key], dict) 
            and isinstance(value, dict)):
            result[key] = _deep_merge(base[key], value)
        else:
            result[key] = value
    
    return result


def save_config(config: Dict[str, Any], config_path: str):
    """Sauvegarde la configuration dans un fichier YAML"""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Récupère une valeur de configuration par chemin
    Exemple: 'processing.default_template'
    """
    keys = key_path.split('.')
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current
