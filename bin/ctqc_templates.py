#!/usr/bin/env python3
"""
Gestion des templates CT-QC - Création et validation
"""

import argparse
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.template_manager import TemplateManager
from utils.config import load_config


def main():
    """Utilitaire de gestion des templates"""
    parser = argparse.ArgumentParser(
        prog="ctqc-templates",
        description="Gestion des templates Excel et sidecars CT-QC"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes")
    
    # Liste des templates
    list_parser = subparsers.add_parser("list", help="Lister les templates disponibles")
    
    # Validation
    validate_parser = subparsers.add_parser("validate", help="Valider les templates")
    validate_parser.add_argument("--template", help="Template spécifique (sinon tous)")
    
    # Création
    create_parser = subparsers.add_parser("create", help="Créer un nouveau template")
    create_parser.add_argument("template_id", help="ID du nouveau template")
    create_parser.add_argument("--description", help="Description du template")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = load_config()
    templates_dir = config['templates']['directory']
    template_manager = TemplateManager(templates_dir)
    
    if args.command == "list":
        templates = template_manager.get_available_templates()
        print("=== TEMPLATES DISPONIBLES ===")
        for template in templates:
            status = "✅" if template['excel_exists'] and template['sidecar_exists'] else "⚠️"
            print(f"{status} {template['id']}: {template['description']}")
            if template['excel_exists']:
                print(f"   📊 Excel: {template['excel_path'].name}")
            else:
                print(f"   ❌ Excel: MANQUANT")
            if template['sidecar_exists']:
                print(f"   📝 Sidecar: {template['sidecar_path'].name}")
            else:
                print(f"   ❌ Sidecar: MANQUANT")
            print()
    
    elif args.command == "validate":
        if args.template:
            # Validation d'un template spécifique
            result = template_manager.validate_template(args.template)
            print(f"Validation de {args.template}:")
            if result['valid']:
                print("✅ VALIDE")
            else:
                print("❌ INVALIDE")
                for issue in result['issues']:
                    print(f"   - {issue}")
        else:
            # Validation de tous les templates
            templates = template_manager.get_available_templates()
            valid_count = 0
            total_count = len(templates)
            
            for template in templates:
                result = template_manager.validate_template(template['id'])
                status = "✅" if result['valid'] else "❌"
                print(f"{status} {template['id']}: {result['info']['description']}")
                if not result['valid']:
                    for issue in result['issues']:
                        print(f"      - {issue}")
                else:
                    valid_count += 1
            
            print(f"\nRésumé: {valid_count}/{total_count} templates valides")
    
    elif args.command == "create":
        description = args.description or f"Template {args.template_id}"
        template_manager.create_template_structure(args.template_id, description)
        print(f"✅ Template {args.template_id} créé avec succès")
        print(f"   📊 Excel: templates/masters/{args.template_id}.xlsx")
        print(f"   📝 Sidecar: templates/{args.template_id}.yml")
        print("\n📋 Prochaines étapes:")
        print("1. Éditez le fichier Excel pour créer la structure")
        print("2. Adaptez le sidecar YAML pour les règles d'extraction")
        print("3. Ajoutez le template à templates/index.yml")


if __name__ == "__main__":
    main()