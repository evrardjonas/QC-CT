"""
Système de conversion d'unités CT-QC
"""

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class UnitConverter:
    """
    Convertit les unités des données extraites
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.conversion_factors = self._load_conversion_factors()
    
    def _load_conversion_factors(self) -> Dict[str, Dict]:
        """Charge les facteurs de conversion"""
        return {
            'mGy_to_cGy': {'factor': 0.1, 'description': 'milliGray to centiGray'},
            'cGy_to_mGy': {'factor': 10, 'description': 'centiGray to milliGray'},
            'mGy_to_Gy': {'factor': 0.001, 'description': 'milliGray to Gray'},
            'Gy_to_mGy': {'factor': 1000, 'description': 'Gray to milliGray'},
            'cm_to_mm': {'factor': 10, 'description': 'centimeter to millimeter'},
            'mm_to_cm': {'factor': 0.1, 'description': 'millimeter to centimeter'},
            'mAs_to_As': {'factor': 0.001, 'description': 'milliAmpere-second to Ampere-second'},
            'As_to_mAs': {'factor': 1000, 'description': 'Ampere-second to milliAmpere-second'}
        }
    
    def convert(self, value: Any, target_unit: str) -> Any:
        """
        Convertit une valeur vers l'unité cible
        """
        if value is None:
            return None
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            logger.warning(f"Cannot convert non-numeric value: {value}")
            return value
        
        # Conversions prédéfinies
        if target_unit in self.conversion_factors:
            conversion = self.conversion_factors[target_unit]
            return numeric_value * conversion['factor']
        
        # Conversions spécifiques CT
        if target_unit == 'hu_to_linear':
            # Conversion HU vers coefficient d'atténuation linéaire (simplifié)
            return (numeric_value / 1000) * 0.2 + 0.2
        
        logger.warning(f"Unknown conversion target: {target_unit}")
        return value
    
    def convert_dose_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convertit les unités de dose"""
        conversions = {
            ('mGy', 'cGy'): 0.1,
            ('cGy', 'mGy'): 10,
            ('mGy', 'Gy'): 0.001,
            ('Gy', 'mGy'): 1000,
            ('mGy.cm', 'Gy.cm'): 0.001,
            ('Gy.cm', 'mGy.cm'): 1000
        }
        
        key = (from_unit, to_unit)
        if key in conversions:
            return value * conversions[key]
        
        logger.warning(f"Unsupported dose conversion: {from_unit} to {to_unit}")
        return value
    
    def get_available_conversions(self) -> Dict[str, str]:
        """Retourne les conversions disponibles"""
        return {k: v['description'] for k, v in self.conversion_factors.items()}