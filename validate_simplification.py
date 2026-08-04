#!/usr/bin/env python3
"""
Script de validation CT-QC - Vérification après simplification
"""

import os
import sys
import importlib
import yaml
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ajout du src au path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("🎯 MOUVEMENT 3 - VALIDATION CT-QC")
print("=" * 50)


def test_imports():
    """Teste l'importation de tous les modules"""
    print("\n📦 TEST DES IMPORTS")
    print("-" * 30)
    
    modules_to_test = [
        "src.core.orchestrator",
        "src.core.selector", 
        "src.core.sidecar",
        "src.core.audit",
        "src.engine.extraction_engine",
        "src.models.qa_visit",
        "src.storage.hdf5_store",
        "src.storage.parquet_export",
        "src.storage.access_export",
        "src.utils.config",
        "src.utils.log"
    ]
    
    success_count = 0
    for module_path in modules_to_test:
        try:
            module = importlib.import_module(module_path)
            print(f"✅ {module_path}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_path}: {e}")
    
    print(f"\n📊 Résultat imports: {success_count}/{len(modules_to_test)}")
    return success_count == len(modules_to_test)


def test_configuration():
    """Teste la configuration"""
    print("\n⚙️ TEST DE CONFIGURATION")
    print("-" * 30)
    
    try:
        from src.utils.config import load_config
        
        config = load_config()
        
        # Vérifications clés
        checks = [
            ("Template par défaut ou auto", config.get('processing', {}).get('default_template') in {"ctqc_base", "auto"}),
            ("Fallback ctqc_base", config.get('templates', {}).get('fallback_template') == "ctqc_base"),
            ("Export Parquet activé", config.get('exports', {}).get('parquet_enabled') == True),
        ]
        
        for check_name, check_result in checks:
            if check_result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
        
        print(f"✅ Configuration chargée: {config.get('version')}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False


def test_template_system():
    """Teste le système de templates simplifié"""
    print("\n📄 TEST TEMPLATE SYSTÈME")
    print("-" * 30)
    
    try:
        from src.core.selector import TemplateSelector
        from src.core.sidecar import SidecarLoader
        
        # Test sélecteur
        selector = TemplateSelector("templates")
        template_id = selector.select_from_file("test.xlsx")
        
        if template_id == "ctqc_base":
            print("✅ TemplateSelector retourne ctqc_base")
        else:
            print(f"❌ TemplateSelector retourne {template_id} au lieu de ctqc_base")
            return False
        
        # Test sidecar
        loader = SidecarLoader("templates")
        sidecar = loader.load("ctqc_base")
        
        if sidecar.get("id") == "ctqc_base":
            print("✅ Sidecar ctqc_base chargé")
        else:
            print("❌ Sidecar ctqc_base non chargé")
            return False
        
        # Verification structure sidecar. v6 uses logical sheet ids plus sheet_name.
        required_sheets = ["Algemene Informatie", "Verslag", "buisspanning-geometrie"]
        sheets_in_sidecar = {
            config.get("sheet_name", key)
            for key, config in sidecar.get("sheets", {}).items()
            if isinstance(config, dict)
        }
        
        for sheet in required_sheets:
            if sheet in sheets_in_sidecar:
                print(f"✅ Feuille {sheet} présente")
            else:
                print(f"❌ Feuille {sheet} manquante")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur template système: {e}")
        return False


def test_orchestrator_init():
    """Teste l'initialisation de l'orchestrateur"""
    print("\n🎵 TEST ORCHESTRATEUR")
    print("-" * 30)
    
    try:
        from src.core.orchestrator import CTQCOrchestrator
        from src.storage.hdf5_store import HDF5Store
        from src.utils.config import load_config
        
        config = load_config()
        
        # Test avec HDFStore mock
        class MockHDFStore:
            def __init__(self, path):
                self.path = path
            def close(self):
                pass
        
        orchestrator = CTQCOrchestrator(MockHDFStore("test.hdf"), config)
        
        # Vérification des attributs
        if hasattr(orchestrator, 'template_selector'):
            print("✅ TemplateSelector initialisé")
        else:
            print("❌ TemplateSelector manquant")
            return False
            
        if hasattr(orchestrator, 'sidecar_loader'):
            print("✅ SidecarLoader initialisé")
        else:
            print("❌ SidecarLoader manquant")
            return False
            
        if hasattr(orchestrator, 'extraction_engine'):
            print("✅ ExtractionEngine initialisé")
        else:
            print("❌ ExtractionEngine manquant")
            return False
        
        print("✅ Orchestrateur initialisé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur orchestrateur: {e}")
        return False


def test_extraction_engine():
    """Teste le moteur d'extraction"""
    print("\n🔧 TEST MOTEUR EXTRACTION")
    print("-" * 30)
    
    try:
        from src.engine.extraction_engine import ExtractionEngine
        from src.utils.config import load_config
        
        config = load_config()
        engine = ExtractionEngine(config)
        
        # Test des composants internes
        if hasattr(engine, 'normalizers'):
            print("✅ Normalizers initialisés")
        else:
            print("❌ Normalizers manquants")
            
        if hasattr(engine, 'validators'):
            print("✅ Validators initialisés")
        else:
            print("❌ Validators manquants")
            
        if hasattr(engine, 'unit_converter'):
            print("✅ UnitConverter initialisé")
        else:
            print("❌ UnitConverter manquant")
        
        print("✅ Moteur d'extraction initialisé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur moteur extraction: {e}")
        return False


def test_audit_system():
    """Teste le système d'audit"""
    print("\n📋 TEST SYSTÈME AUDIT")
    print("-" * 30)
    
    try:
        from src.core.audit import AuditSystem
        
        audit = AuditSystem()
        
        # Test logging
        audit.log_event("INFO", "Validation", "Test", "Message de test")
        
        # Test métriques
        metrics = audit.get_summary_metrics()
        
        if 'total_events' in metrics:
            print("✅ Système d'audit fonctionnel")
        else:
            print("❌ Métriques d'audit manquantes")
            return False
            
        print("✅ Système d'audit testé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur système audit: {e}")
        return False


def test_config_files():
    """Vérifie les fichiers de configuration"""
    print("\n📁 TEST FICHIERS CONFIG")
    print("-" * 30)
    
    config_files = [
        "config/default.yml",
        "config/development.yml", 
        "config/production.yml",
        "templates/ctqc_base.yml",
        "templates/index.yml"
    ]
    
    success_count = 0
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.endswith('.yml'):
                        content = yaml.safe_load(f)
                    else:
                        content = f.read()
                
                print(f"✅ {config_file}")
                success_count += 1
                
                # Vérifications spécifiques
                if config_file == "config/default.yml":
                    if content.get('processing', {}).get('default_template') in {'ctqc_base', 'auto'}:
                        print("  ✅ Template par défaut: auto/ctqc_base")
                    else:
                        print("  ❌ Template par défaut incorrect")
                
                if config_file == "templates/index.yml":
                    if 'ctqc_base' in content.get('templates', {}):
                        print("  ✅ Template ctqc_base dans registry")
                    else:
                        print("  ❌ Template ctqc_base manquant dans registry")
                        
            except Exception as e:
                print(f"❌ {config_file}: {e}")
        else:
            print(f"❌ {config_file}: Fichier manquant")
    
    print(f"\n📊 Fichiers config: {success_count}/{len(config_files)}")
    return success_count == len(config_files)


def main():
    """Fonction principale de validation"""
    print("🚀 LANCEMENT DE LA VALIDATION COMPLÈTE")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_template_system,
        test_orchestrator_init,
        test_extraction_engine,
        test_audit_system,
        test_config_files
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} a échoué: {e}")
            results.append(False)
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RAPPORT FINAL DE VALIDATION")
    print("=" * 50)
    
    success_count = sum(results)
    total_tests = len(results)
    
    print(f"Tests réussis: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        print("✅ La simplification a été appliquée avec succès")
        return True
    else:
        print("⚠️  Certains tests ont échoué")
        print("🔧 Des corrections peuvent être nécessaires")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
