"""
Système de normalisation CT-QC
"""

import re
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class Normalizers:
    """
    Applique les normalisations aux données extraites
    """
    
    def __init__(self, config: Dict):
        self.config = config
    
    def apply(self, value: Any, normalize_config: Dict) -> Any:
        """
        Applique une normalisation à une valeur
        """
        if value is None:
            return normalize_config.get('default')
        
        # Application séquentielle des normalisations
        result = value
        
        if 'map' in normalize_config:
            result = self._apply_map(result, normalize_config['map'])
        
        if 'regex' in normalize_config:
            result = self._apply_regex(result, normalize_config['regex'])
        
        if 'trim' in normalize_config and normalize_config['trim']:
            result = self._apply_trim(result)
        
        if 'case' in normalize_config:
            result = self._apply_case(result, normalize_config['case'])
        
        return result
    
    def _apply_map(self, value: Any, mapping: Dict) -> Any:
        """Applique un mapping de valeurs"""
        str_value = str(value).strip()
        
        # Recherche par patterns regex
        for pattern, replacement in mapping.items():
            if pattern.startswith('^') or '.*' in pattern:
                # Pattern regex
                try:
                    if re.match(pattern, str_value, re.IGNORECASE):
                        return replacement
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")
            else:
                # Valeur exacte
                if str_value.lower() == pattern.lower():
                    return replacement
        
        # Valeur par défaut
        return mapping.get('default', value)
    
    def _apply_regex(self, value: Any, regex_config: Dict) -> Any:
        """Applique une transformation regex"""
        str_value = str(value)
        pattern = regex_config.get('pattern')
        
        if not pattern:
            return value
        
        try:
            if re.match(pattern, str_value):
                replacement = regex_config.get('replacement', '')
                if replacement:
                    return re.sub(pattern, replacement, str_value)
                return str_value
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
        
        return value
    
    def _apply_trim(self, value: Any) -> Any:
        """Supprime les espaces superflus"""
        if isinstance(value, str):
            return value.strip()
        return value
    
    def _apply_case(self, value: Any, case_type: str) -> Any:
        """Applique une transformation de casse"""
        if not isinstance(value, str):
            return value
        
        if case_type == 'upper':
            return value.upper()
        elif case_type == 'lower':
            return value.lower()
        elif case_type == 'title':
            return value.title()
        elif case_type == 'capitalize':
            return value.capitalize()
        else:
            return value
    
    def normalize_vendor_name(self, vendor: str) -> str:
        """Normalise les noms de fabricants"""
        vendor_map = {
            'siemens': 'Siemens',
            'ge': 'GE Healthcare',
            'general electric': 'GE Healthcare',
            'philips': 'Philips',
            'canon': 'Canon',
            'toshiba': 'Toshiba',
            'hitachi': 'Hitachi'
        }
        return vendor_map.get(vendor.lower().strip(), vendor)
    
    def normalize_boolean(self, value: Any) -> bool:
        """Normalise les valeurs booléennes"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        
        str_value = str(value).lower().strip()
        true_values = ['true', '1', 'yes', 'y', 'oui', 'vrai']
        false_values = ['false', '0', 'no', 'n', 'non', 'faux']
        
        if str_value in true_values:
            return True
        elif str_value in false_values:
            return False
        
        return bool(value)