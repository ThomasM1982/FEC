#!/usr/bin/env python3
"""
Script d'analyse de fichier FEC sans upload vers Grist.

Usage:
    python analyze_fec.py <fichier_fec>

Exemple:
    python analyze_fec.py ../data/FEC_2024.txt
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.readers.fec_reader import FECReader
from src.validators.fec_validator import FECValidator


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_fec.py <fichier_fec>")
        sys.exit(1)

    file_path = sys.argv[1]

    print("=" * 60)
    print("ANALYSE DE FICHIER FEC")
    print("=" * 60)
    print(f"\n📁 Fichier: {file_path}\n")

    # Lire le fichier FEC
    encodings = ['utf-8', 'latin1', 'cp1252']
    reader = None

    for encoding in encodings:
        try:
            reader = FECReader(file_path, encoding=encoding)
            entries = reader.read()
            print(f"✓ Fichier lu avec succès (encodage: {encoding})")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)

    if reader is None:
        print("❌ Impossible de lire le fichier avec les encodages supportés")
        sys.exit(1)

    # Statistiques générales
    print("\n" + "=" * 60)
    print("STATISTIQUES GÉNÉRALES")
    print("=" * 60)

    stats = reader.get_statistics()
    print(f"\n📊 Vue d'ensemble:")
    print(f"  Nombre total d'écritures: {stats['total_entries']:,}")
    print(f"  Total débit: {stats['total_debit']:,.2f} €")
    print(f"  Total crédit: {stats['total_credit']:,.2f} €")
    print(f"  Différence: {abs(stats['total_debit'] - stats['total_credit']):,.2f} €")
    print(f"  Équilibré: {'✓ Oui' if stats['is_balanced'] else '✗ Non'}")
    print(f"\n📅 Période:")
    print(f"  Du {stats['date_range']['min']} au {stats['date_range']['max']}")

    # Analyse par journal
    print(f"\n📚 Journaux ({len(stats['journals'])}):")
    for journal in sorted(stats['journals'], key=lambda x: x['count'], reverse=True):
        pct = (journal['count'] / stats['total_entries']) * 100
        print(f"\n  {journal['code']} - {journal['libelle']}")
        print(f"    Écritures: {journal['count']:,} ({pct:.1f}%)")
        print(f"    Débit: {journal['debit']:,.2f} €")
        print(f"    Crédit: {journal['credit']:,.2f} €")

    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)

    validator = FECValidator(entries)
    report = validator.get_report()
    print(report)

    # Analyse par compte
    print("\n" + "=" * 60)
    print("ANALYSE PAR CLASSE DE COMPTES")
    print("=" * 60)

    classes = {}
    for entry in entries:
        classe = entry.compte_num[0] if entry.compte_num else '?'
        if classe not in classes:
            classes[classe] = {'count': 0, 'debit': 0, 'credit': 0}
        classes[classe]['count'] += 1
        classes[classe]['debit'] += float(entry.debit)
        classes[classe]['credit'] += float(entry.credit)

    classe_names = {
        '1': 'Comptes de capitaux',
        '2': 'Comptes d\'immobilisations',
        '3': 'Comptes de stocks',
        '4': 'Comptes de tiers',
        '5': 'Comptes financiers',
        '6': 'Comptes de charges',
        '7': 'Comptes de produits',
        '8': 'Comptes spéciaux'
    }

    print()
    for classe in sorted(classes.keys()):
        data = classes[classe]
        classe_name = classe_names.get(classe, 'Autres')
        print(f"\nClasse {classe} - {classe_name}:")
        print(f"  Écritures: {data['count']:,}")
        print(f"  Débit: {data['debit']:,.2f} €")
        print(f"  Crédit: {data['credit']:,.2f} €")
        print(f"  Solde: {data['debit'] - data['credit']:,.2f} €")

    print("\n" + "=" * 60)
    print("Analyse terminée!")
    print("=" * 60)


if __name__ == "__main__":
    main()
