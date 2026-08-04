"""
Système de validation CT-QC
"""

import re
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Validators:
    """
    Applique les validations aux données extraites
    """
    
    def __init__(self, config: Dict):
        self.config = config
    
    def validate(self, value: Any, validator_config: Dict, field_name: str = "unknown", 
                silent: bool = False) -> bool:
        """
        Valide une valeur selon la configuration
        """
        if value is None:
            return not validator_config.get('required', False)
        
        validator_type = next(iter(validator_config.keys()))
        validator_value = validator_config[validator_type]
        
        try:
            if validator_type == 'range':
                return self._validate_range(value, validator_value)
            elif validator_type == 'in':
                return self._validate_in(value, validator_value)
            elif validator_type == 'regex':
                return self._validate_regex(value, validator_value)
            elif validator_type == 'length':
                return self._validate_length(value, validator_value)
            elif validator_type == 'required':
                return self._validate_required(value)
            else:
                if not silent:
                    logger.warning(f"Unknown validator type: {validator_type}")
                return True
        except Exception as e:
            if not silent:
                logger.error(f"Validation failed for {field_name}: {e}")
            return False
    
    def _validate_range(self, value: Any, range_config: List) -> bool:
        """Valide une plage de valeurs"""
        try:
            numeric_value = float(value)
            min_val, max_val = range_config
            return min_val <= numeric_value <= max_val
        except (ValueError, TypeError):
            return False
    
    def _validate_in(self, value: Any, allowed_values: List) -> bool:
        """Valide l'appartenance à une liste"""
        return value in allowed_values
    
    def _validate_regex(self, value: Any, pattern: str) -> bool:
        """Valide un pattern regex"""
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
            return False
    
    def _validate_length(self, value: Any, length_config: Dict) -> bool:
        """Valide la longueur d'une chaîne"""
        str_value = str(value)
        min_len = length_config.get('min', 0)
        max_len = length_config.get('max', float('inf'))
        
        return min_len <= len(str_value) <= max_len
    
    def _validate_required(self, value: Any) -> bool:
        """Valide qu'une valeur est requise"""
        return value is not None and value != ''
    
    def validate_ctdi_value(self, value: float, measurement_type: str) -> bool:
        """Valide les valeurs CTDI spécifiques"""
        ranges = {
            'ctdi_vol': (0, 200),      # mGy
            'dlp': (0, 5000),          # mGy.cm
            'dose_central': (0, 1000), # mGy.cm
            'kv': (70, 150),           # kV
            'mas': (10, 1000)          # mAs
        }
        
        if measurement_type in ranges:
            min_val, max_val = ranges[measurement_type]
            return min_val <= value <= max_val
        
        return True
    
    def validate_hu_value(self, value: float, material: str) -> bool:
        """Valide les valeurs HU"""
        ranges = {
            'air': (-1000, -900),
            'water': (-10, 10),
            'pmp': (-250, -150),
            'ldpe': (-120, -80),
            'polystyrene': (-50, -20),
            'acrylic': (100, 140),
            'delrin': (300, 380),
            'teflon': (900, 1100)
        }
        
        if material in ranges:
            min_val, max_val = ranges[material]
            return min_val <= value <= max_val
        
        return True