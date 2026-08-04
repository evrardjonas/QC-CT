#!/usr/bin/env python3
"""
Test d'intégration CT-QC - Simulation de traitement
"""

import os
import sys
import tempfile
from pathlib import Path

# Ajout du src au path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("🔧 TEST D'INTÉGRATION CT-QC")
print("=" * 50)


def test_workflow_simplifie():
    """Test le workflow simplifié"""
    print("\n🔄 TEST WORKFLOW SIMPLIFIÉ")
    print("-" * 30)
    
    try:
        from src.core.orchestrator import CTQCOrchestrator
        from src.core.selector import TemplateSelector
        from src.core.sidecar import SidecarLoader
        from src.utils.config import load_config
        
        # Chargement configuration
        config = load_config()
        print("✅ Configuration chargée")
        
        # Test sélecteur simplifié
        selector = TemplateSelector(config['templates']['directory'])
        template_id = selector.select_from_file("fichier_inexistant.xlsx")
        
        if template_id == "ctqc_base":
            print("✅ Sélecteur simplifié fonctionne")
        else:
            print(f"❌ Sélecteur retourne {template_id} au lieu de ctqc_base")
            return False
        
        # Test sidecar
        loader = SidecarLoader(config['templates']['directory'])
        sidecar = loader.load("ctqc_base")
        
        if sidecar["id"] == "ctqc_base":
            print("✅ Sidecar unique chargé")
        else:
            print("❌ Sidecar incorrect")
            return False
        
        # Vérification structure
        required_fields = ["id", "version", "sheets"]
        for field in required_fields:
            if field in sidecar:
                print(f"✅ Champ {field} présent")
            else:
                print(f"❌ Champ {field} manquant")
                return False
        
        print("🎯 WORKFLOW SIMPLIFIÉ VALIDÉ")
        return True
        
    except Exception as e:
        print(f"❌ Erreur workflow: {e}")
        return False


def test_commande_line_interface():
    """Test que les commandes CLI sont toujours disponibles"""
    print("\n💻 TEST INTERFACE COMMANDES")
    print("-" * 30)
    
    try:
        # Test import des modules CLI
        from bin import ctqc_ingest, ctqc_export, ctqc_analytics
        print("✅ Modules CLI importables")
        
        # Vérification des fonctions main
        if hasattr(ctqc_ingest, 'main'):
            print("✅ ctqc-ingest: main() disponible")
        else:
            print("❌ ctqc-ingest: main() manquant")
            
        if hasattr(ctqc_export, 'main'):
            print("✅ ctqc-export: main() disponible")
        else:
            print("❌ ctqc-export: main() manquant")
            
        if hasattr(ctqc_analytics, 'main'):
            print("✅ ctqc-analytics: main() disponible")
        else:
            print("❌ ctqc-analytics: main() manquant")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur interface commandes: {e}")
        return False


def test_configuration_avancee():
    """Test avancé de la configuration"""
    print("\n⚙️ TEST CONFIGURATION AVANCÉE")
    print("-" * 30)
    
    try:
        from src.utils.config import load_config, get_config_value
        
        config = load_config()
        
        # Tests de valeurs spécifiques
        tests = [
            ("Template par défaut", "processing.default_template", "ctqc_base"),
            ("Détection auto", "templates.auto_detection", False),
            ("Export Parquet", "exports.parquet_enabled", True),
            ("Chemin HDF5", "storage.hdf5_path", "data/operational/CTdb.hdf"),
        ]
        
        success_count = 0
        for test_name, key_path, expected_value in tests:
            actual_value = get_config_value(config, key_path)
            if actual_value == expected_value:
                print(f"✅ {test_name}: {actual_value}")
                success_count += 1
            else:
                print(f"❌ {test_name}: {actual_value} (attendu: {expected_value})")
        
        print(f"📊 Configuration: {success_count}/{len(tests)} tests réussis")
        return success_count == len(tests)
        
    except Exception as e:
        print(f"❌ Erreur configuration avancée: {e}")
        return False


def main():
    """Fonction principale de test d'intégration"""
    tests = [
        test_workflow_simplifie,
        test_commande_line_interface, 
        test_configuration_avancee
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} a échoué: {e}")
            results.append(False)
    
    # Résumé
    print("\n" + "=" * 50)
    success_count = sum(results)
    total_tests = len(results)
    
    print(f"TESTS D'INTÉGRATION: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 INTÉGRATION VALIDÉE AVEC SUCCÈS !")
        print("✅ Le système simplifié est opérationnel")
        return True
    else:
        print("⚠️  Problèmes détectés lors de l'intégration")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)