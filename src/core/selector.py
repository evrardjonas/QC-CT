"""
Template Selector Simplifié - Un seul template CT-QC
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TemplateSelector:
    """
    Sélecteur simplifié - Template unique toujours utilisé
    """
    
    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir
        logger.info("TemplateSelector initialisé - template unique: ctqc_base")
    
    def select_from_file(self, excel_path: str, forced: Optional[str] = None) -> str:
        """
        Retourne toujours le template ctqc_base
        """
        # Template unique - pas de détection nécessaire
        template_id = "ctqc_base"
        
        if forced and forced != "auto":
            logger.warning(f"Option --template {forced} ignorée, utilisation de ctqc_base")
        
        logger.debug(f"Template sélectionné: {template_id}")
        return template_id
    
    def get_available_templates(self) -> dict:
        """Retourne le template unique disponible"""
        return {
            "ctqc_base": {
                "description": "Template unique pour visites CT-QC complètes",
                "required": True
            }
        }
    
    def validate_template_compatibility(self, excel_path: str, template_id: str) -> bool:
        """
        Validation simplifiée - toujours vrai pour ctqc_base
        """
        return template_id == "ctqc_base"