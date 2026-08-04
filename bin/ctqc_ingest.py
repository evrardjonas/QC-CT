#!/usr/bin/env python3
"""
Point d'entrée principal - Ingestion des fichiers Excel CT-QC
"""

import argparse
import os
import sys
from pathlib import Path

# Ajout du src au path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.orchestrator import CTQCOrchestrator
from storage.hdf5_store import HDF5Store
from utils.config import load_config
from utils.log import setup_logging


def main():
    """Point d'entrée CLI pour l'ingestion"""
    parser = argparse.ArgumentParser(
        prog="ctqc-ingest",
        description="Ingestion des fichiers Excel CT-QC vers HDF5/Parquet/TXT"
    )
    
    # Arguments principaux
    parser.add_argument("input_path", help="Chemin vers fichier Excel ou dossier")
    parser.add_argument("--config", "-c", default="config/default.yml", 
                       help="Fichier de configuration")
    
    # Options de traitement
    parser.add_argument("--template", default="auto", 
                       help="Template ID ou 'auto' pour détection")
    parser.add_argument("--strict", action="store_true", 
                       help="Mode validation stricte")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Validation sans écriture")
    
    # Options d'export
    parser.add_argument("--to-parquet", help="Export Parquet analytics")
    parser.add_argument("--to-access", help="Export TXT pour Access")
    parser.add_argument("--no-export", action="store_true", 
                       help="Désactive tous les exports")
    
    # Options de performance
    parser.add_argument("--workers", "-w", type=int, default=0,
                       help="Nombre de workers parallèles")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Taille des lots pour traitement parallèle")
    
    args = parser.parse_args()
    
    # Chargement configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config['logging'])
    
    # Initialisation storage
    hdf_store = HDF5Store(config['storage']['hdf5_path'])
    
    # Configuration processing
    processing_config = {
        'template': args.template,
        'strict': args.strict,
        'dry_run': args.dry_run,
        'workers': args.workers,
        'batch_size': args.batch_size,
        'exports': {
            'parquet': args.to_parquet if not args.no_export else None,
            'access': args.to_access if not args.no_export else None
        }
    }
    
    # Orchestrateur
    orchestrator = CTQCOrchestrator(hdf_store, config)
    
    try:
        # Traitement
        if os.path.isfile(args.input_path):
            # Fichier unique
            success = orchestrator.process_file(args.input_path, processing_config)
            result_msg = "SUCCESS" if success else "FAILED"
            print(f"Processing {args.input_path}: {result_msg}")
            
        elif os.path.isdir(args.input_path):
            # Dossier complet
            results = orchestrator.process_directory(args.input_path, processing_config)
            success_count = sum(1 for r in results if r['success'])
            total_count = len(results)
            print(f"Batch processing: {success_count}/{total_count} successful")
            
        else:
            print(f"ERROR: Path not found: {args.input_path}")
            sys.exit(1)
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
    finally:
        hdf_store.close()


if __name__ == "__main__":
    main()