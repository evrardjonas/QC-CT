"""
Chargeur de sidecars CT-QC
"""

import os
import yaml
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SidecarLoader:
    """
    Charge et valide les fichiers sidecar YAML
    """
    
    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir
        self.loaded_sidecars: Dict[str, Dict] = {}
    
    def load(self, template_id: str, strict: bool = False) -> Dict[str, Any]:
        """
        Charge un sidecar pour un template donné
        """
        # Cache
        if template_id in self.loaded_sidecars:
            return self.loaded_sidecars[template_id]
        
        sidecar_path = self._resolve_sidecar_path(template_id)
        
        if not sidecar_path:
            if strict:
                raise FileNotFoundError(f"Sidecar not found for template: {template_id}")
            logger.warning(f"Sidecar not found, using default: {template_id}")
            return self._create_default_sidecar(template_id)
        
        try:
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                sidecar = yaml.safe_load(f)
        except Exception as e:
            if strict:
                raise
            logger.error(f"Failed to load sidecar {sidecar_path}: {e}")
            return self._create_default_sidecar(template_id)
        
        # Gestion de l'héritage
        sidecar = self._normalize_loaded_sidecar(template_id, sidecar or {})

        if 'extends' in sidecar:
            base_template = sidecar['extends']
            base_sidecar = self.load(base_template, strict)
            sidecar = self._deep_merge(base_sidecar, sidecar)
        
        # Validation
        if strict:
            self._validate_sidecar(sidecar)
        
        self.loaded_sidecars[template_id] = sidecar
        logger.info(f"Sidecar loaded: {template_id} (version: {sidecar.get('version', 'unknown')})")
        return sidecar

    def _resolve_sidecar_path(self, template_id: str) -> Optional[str]:
        """Resolve .yaml before .yml so v6 mappings can supersede legacy sidecars."""
        for extension in (".yaml", ".yml"):
            sidecar_path = os.path.join(self.templates_dir, f"{template_id}{extension}")
            if os.path.exists(sidecar_path):
                return sidecar_path
        return None

    def _normalize_loaded_sidecar(self, template_id: str, sidecar: Dict[str, Any]) -> Dict[str, Any]:
        """Add compatibility metadata without changing the mapping body."""
        sidecar.setdefault("id", template_id)
        if "version" not in sidecar:
            workbook = sidecar.get("workbook") or {}
            sidecar["version"] = str(workbook.get("version", "0.0.0"))
        sidecar["_template_id"] = template_id
        return sidecar
    
    def _create_default_sidecar(self, template_id: str) -> Dict[str, Any]:
        """Crée un sidecar par défaut"""
        return {
            "id": template_id,
            "version": "1.0.0",
            "description": f"Default sidecar for {template_id}",
            "strict": False,
            "sheets": {}
        }
    
    def _deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        """Fusion récursive de dictionnaires"""
        result = base.copy()
        
        for key, value in overlay.items():
            if (key in base and isinstance(base[key], dict) 
                and isinstance(value, dict)):
                result[key] = self._deep_merge(base[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_sidecar(self, sidecar: Dict) -> None:
        """Valide la structure du sidecar"""
        required_fields = ['id', 'version']
        for field in required_fields:
            if field not in sidecar:
                raise ValueError(f"Sidecar missing required field: {field}")
        
        # Validation des sheets
        for sheet_name, sheet_config in sidecar.get('sheets', {}).items():
            self._validate_sheet_config(sheet_name, sheet_config)
    
    def _validate_sheet_config(self, sheet_name: str, sheet_config: Dict) -> None:
        """Valide la configuration d'une feuille"""
        if not isinstance(sheet_config, dict):
            raise ValueError(f"Sheet {sheet_name} must be a dictionary")

        if 'sections' in sheet_config:
            if not isinstance(sheet_config['sections'], dict):
                raise ValueError(f"Sheet {sheet_name} sections must be a dictionary")
            return

        if 'sheet_name' in sheet_config and 'fields' not in sheet_config and 'tables' not in sheet_config:
            return

        # Validation des fields
        if 'fields' in sheet_config:
            for field_name, field_config in sheet_config['fields'].items():
                if not isinstance(field_config, dict):
                    raise ValueError(f"Field {field_name} must be a dictionary")
                # 'name' est optionnel : par défaut, on utilise le nom du champ
                field_config.setdefault('name', field_name)

        # Validation des tables
        if 'tables' in sheet_config:
            for table_name, table_config in sheet_config['tables'].items():
                if not isinstance(table_config, dict):
                    raise ValueError(f"Table {table_name} must be a dictionary")
                if 'table' not in table_config:
                    raise ValueError(f"Table {table_name} missing 'table' reference")


    
    def get_sidecar_info(self, template_id: str) -> Dict[str, Any]:
        """Retourne les informations d'un sidecar"""
        sidecar = self.load(template_id)
        return {
            'id': sidecar.get('id'),
            'version': sidecar.get('version'),
            'description': sidecar.get('description'),
            'sheets_count': len(sidecar.get('sheets', {})),
            'extends': sidecar.get('extends')
        }
    
    def clear_cache(self):
        """Vide le cache des sidecars"""
        self.loaded_sidecars.clear()
