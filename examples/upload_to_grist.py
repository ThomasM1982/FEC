#!/usr/bin/env python3
"""
Script d'exemple pour uploader des écritures comptables vers Grist.

Usage:
    python upload_to_grist.py <fichier_fec>

Exemple:
    python upload_to_grist.py ../data/FEC_2024.txt
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.readers.fec_reader import FECReader
from src.validators.fec_validator import FECValidator
from src.grist.client import GristClient


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python upload_to_grist.py <fichier_fec>")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"📁 Lecture du fichier: {file_path}")
    print("-" * 60)

    # Lire le fichier FEC
    try:
        reader = FECReader(file_path, encoding='utf-8')
    except FileNotFoundError:
        # Essayer avec latin1 si utf-8 échoue
        try:
            reader = FECReader(file_path, encoding='latin1')
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du fichier: {e}")
            sys.exit(1)

    try:
        entries = reader.read()
        print(f"✓ {len(entries)} écritures lues")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        sys.exit(1)

    # Afficher les statistiques
    print("\n📊 Statistiques du fichier:")
    print("-" * 60)
    stats = reader.get_statistics()
    print(f"Nombre d'écritures: {stats['total_entries']}")
    print(f"Total débit: {stats['total_debit']:,.2f} €")
    print(f"Total crédit: {stats['total_credit']:,.2f} €")
    print(f"Équilibré: {'✓ Oui' if stats['is_balanced'] else '✗ Non'}")
    print(f"Période: {stats['date_range']['min']} à {stats['date_range']['max']}")

    print("\nJournaux:")
    for journal in stats['journals']:
        print(f"  - {journal['code']}: {journal['libelle']} ({journal['count']} écritures)")

    # Valider le fichier
    print("\n🔍 Validation du fichier:")
    print("-" * 60)
    validator = FECValidator(entries)
    validation_report = validator.get_report()
    print(validation_report)

    results = validator.validate_all()
    if not results['is_valid']:
        print("\n❌ Le fichier contient des erreurs. Voulez-vous continuer l'upload ? (o/n)")
        response = input().lower()
        if response != 'o':
            print("Upload annulé.")
            sys.exit(0)

    # Upload vers Grist
    print("\n☁️  Upload vers Grist:")
    print("-" * 60)

    try:
        client = GristClient()
        print(f"Connexion à: {client.server_url}")
        print(f"Document ID: {client.doc_id}")
        print(f"Table: {client.table_name}")

        result = client.upload_entries(entries, batch_size=500)

        print("\n✓ Upload terminé!")
        print(f"Total: {result['total']} écritures")
        print(f"Uploadées: {result['uploaded']} écritures")

        if result['errors']:
            print(f"\n⚠️  {len(result['errors'])} erreurs:")
            for error in result['errors']:
                print(f"  - Lot {error['batch']}: {error['error']}")
        else:
            print("\n✅ Toutes les écritures ont été uploadées avec succès!")

    except ValueError as e:
        print(f"\n❌ Erreur de configuration: {e}")
        print("\nAssurez-vous d'avoir configuré le fichier .env avec:")
        print("  - GRIST_API_KEY")
        print("  - GRIST_DOC_ID")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de l'upload: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
