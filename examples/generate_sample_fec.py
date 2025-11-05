#!/usr/bin/env python3
"""
Script pour générer un fichier FEC d'exemple.

Usage:
    python generate_sample_fec.py [output_file]

Exemple:
    python generate_sample_fec.py sample_fec.txt
"""
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.accounting_entry import AccountingEntry


def generate_sample_entries():
    """Génère des écritures comptables d'exemple."""
    entries = []

    # Date de base
    base_date = date(2024, 1, 1)

    # Écriture 1: Vente
    entries.append(AccountingEntry(
        journal_code="VE",
        journal_lib="Journal des ventes",
        ecriture_num="VE001",
        ecriture_date=base_date,
        compte_num="411000",
        compte_lib="Clients",
        comp_aux_num="CLI001",
        comp_aux_lib="Client ABC",
        piece_ref="FAC001",
        piece_date=base_date,
        ecriture_lib="Vente marchandises",
        debit=Decimal("1200.00"),
        credit=Decimal("0"),
        valid_date=base_date
    ))

    entries.append(AccountingEntry(
        journal_code="VE",
        journal_lib="Journal des ventes",
        ecriture_num="VE001",
        ecriture_date=base_date,
        compte_num="707000",
        compte_lib="Ventes de marchandises",
        piece_ref="FAC001",
        piece_date=base_date,
        ecriture_lib="Vente marchandises",
        debit=Decimal("0"),
        credit=Decimal("1000.00"),
        valid_date=base_date
    ))

    entries.append(AccountingEntry(
        journal_code="VE",
        journal_lib="Journal des ventes",
        ecriture_num="VE001",
        ecriture_date=base_date,
        compte_num="445710",
        compte_lib="TVA collectée",
        piece_ref="FAC001",
        piece_date=base_date,
        ecriture_lib="TVA sur vente",
        debit=Decimal("0"),
        credit=Decimal("200.00"),
        valid_date=base_date
    ))

    # Écriture 2: Achat
    entries.append(AccountingEntry(
        journal_code="AC",
        journal_lib="Journal des achats",
        ecriture_num="AC001",
        ecriture_date=base_date + timedelta(days=5),
        compte_num="607000",
        compte_lib="Achats de marchandises",
        piece_ref="FACH001",
        piece_date=base_date + timedelta(days=5),
        ecriture_lib="Achat fournitures",
        debit=Decimal("500.00"),
        credit=Decimal("0"),
        valid_date=base_date + timedelta(days=5)
    ))

    entries.append(AccountingEntry(
        journal_code="AC",
        journal_lib="Journal des achats",
        ecriture_num="AC001",
        ecriture_date=base_date + timedelta(days=5),
        compte_num="445660",
        compte_lib="TVA déductible",
        piece_ref="FACH001",
        piece_date=base_date + timedelta(days=5),
        ecriture_lib="TVA sur achat",
        debit=Decimal("100.00"),
        credit=Decimal("0"),
        valid_date=base_date + timedelta(days=5)
    ))

    entries.append(AccountingEntry(
        journal_code="AC",
        journal_lib="Journal des achats",
        ecriture_num="AC001",
        ecriture_date=base_date + timedelta(days=5),
        compte_num="401000",
        compte_lib="Fournisseurs",
        comp_aux_num="FOUR001",
        comp_aux_lib="Fournisseur XYZ",
        piece_ref="FACH001",
        piece_date=base_date + timedelta(days=5),
        ecriture_lib="Achat fournitures",
        debit=Decimal("0"),
        credit=Decimal("600.00"),
        valid_date=base_date + timedelta(days=5)
    ))

    # Écriture 3: Règlement banque
    entries.append(AccountingEntry(
        journal_code="BQ",
        journal_lib="Journal de banque",
        ecriture_num="BQ001",
        ecriture_date=base_date + timedelta(days=10),
        compte_num="512000",
        compte_lib="Banque",
        piece_ref="VIR001",
        piece_date=base_date + timedelta(days=10),
        ecriture_lib="Encaissement client",
        debit=Decimal("1200.00"),
        credit=Decimal("0"),
        valid_date=base_date + timedelta(days=10)
    ))

    entries.append(AccountingEntry(
        journal_code="BQ",
        journal_lib="Journal de banque",
        ecriture_num="BQ001",
        ecriture_date=base_date + timedelta(days=10),
        compte_num="411000",
        compte_lib="Clients",
        comp_aux_num="CLI001",
        comp_aux_lib="Client ABC",
        piece_ref="VIR001",
        piece_date=base_date + timedelta(days=10),
        ecriture_lib="Encaissement client",
        debit=Decimal("0"),
        credit=Decimal("1200.00"),
        ecriture_let="A",
        date_let=base_date + timedelta(days=10),
        valid_date=base_date + timedelta(days=10)
    ))

    return entries


def write_fec_file(entries, output_file):
    """Écrit les écritures dans un fichier FEC."""
    headers = [
        'JournalCode', 'JournalLib', 'EcritureNum', 'EcritureDate',
        'CompteNum', 'CompteLib', 'CompAuxNum', 'CompAuxLib',
        'PieceRef', 'PieceDate', 'EcritureLib', 'Debit', 'Credit',
        'EcritureLet', 'DateLet', 'ValidDate', 'Montantdevise', 'Idevise'
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        # Écrire les en-têtes
        f.write('\t'.join(headers) + '\n')

        # Écrire les données
        for entry in entries:
            data = entry.to_grist_dict()
            row = [
                data.get('JournalCode', ''),
                data.get('JournalLib', ''),
                data.get('EcritureNum', ''),
                data.get('EcritureDate', '').replace('-', ''),
                data.get('CompteNum', ''),
                data.get('CompteLib', ''),
                data.get('CompAuxNum', ''),
                data.get('CompAuxLib', ''),
                data.get('PieceRef', ''),
                data.get('PieceDate', '').replace('-', ''),
                data.get('EcritureLib', ''),
                str(data.get('Debit', 0)).replace('.', ','),
                str(data.get('Credit', 0)).replace('.', ','),
                data.get('EcritureLet', ''),
                data.get('DateLet', '').replace('-', '') if data.get('DateLet') else '',
                data.get('ValidDate', '').replace('-', ''),
                str(data.get('Montantdevise', 0)).replace('.', ','),
                data.get('Idevise', ''),
            ]
            f.write('\t'.join(row) + '\n')


def main():
    """Fonction principale."""
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'sample_fec.txt'

    print(f"Génération d'un fichier FEC d'exemple...")
    print(f"Fichier de sortie: {output_file}")

    entries = generate_sample_entries()
    write_fec_file(entries, output_file)

    print(f"\n✓ {len(entries)} écritures générées dans {output_file}")
    print("\nVous pouvez maintenant analyser ce fichier avec:")
    print(f"  python analyze_fec.py {output_file}")


if __name__ == "__main__":
    main()
