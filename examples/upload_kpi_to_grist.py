#!/usr/bin/env python3
"""
Script pour calculer et uploader les KPI vers Grist.

Usage:
    python upload_kpi_to_grist.py <fichier_fec>

Exemple:
    python upload_kpi_to_grist.py sample.txt
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.readers.fec_reader import FECReader
from src.kpi.calculator import KPICalculator
from src.kpi.financial_kpi import FinancialKPI
from src.kpi.operational_kpi import OperationalKPI
from src.grist.client import GristClient


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python upload_kpi_to_grist.py <fichier_fec>")
        sys.exit(1)

    file_path = sys.argv[1]

    print("=" * 80)
    print("CALCUL ET UPLOAD DES KPI VERS GRIST")
    print("=" * 80)
    print(f"\n📁 Fichier: {file_path}")

    # Lire le fichier FEC
    print("\n1️⃣  Lecture du fichier FEC...")
    encodings = ['utf-8', 'latin1', 'cp1252']
    entries = None

    for encoding in encodings:
        try:
            reader = FECReader(file_path, encoding=encoding)
            entries = reader.read()
            print(f"   ✓ {len(entries)} écritures lues (encodage: {encoding})")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            sys.exit(1)

    if not entries:
        print("   ❌ Impossible de lire le fichier")
        sys.exit(1)

    # Calculer les statistiques de base
    stats = reader.get_statistics()
    print(f"\n   📊 Période: {stats['date_range']['min']} au {stats['date_range']['max']}")
    print(f"   💰 CA: {stats['total_debit']:,.2f} €")
    print(f"   ⚖️  Équilibré: {'✓' if stats['is_balanced'] else '✗'}")

    # Calculer les KPI
    print("\n2️⃣  Calcul des KPI...")
    calc = KPICalculator(entries)
    fin_kpi = FinancialKPI(calc)
    op_kpi = OperationalKPI(calc)

    kpi_data = calc.calculate_all_kpi()
    kpi_data['kpi_financiers'] = fin_kpi.calculate_all_financial_kpi()
    kpi_data['kpi_operationnels'] = op_kpi.calculate_all_operational_kpi()

    print("   ✓ KPI calculés")

    # Afficher un résumé des KPI
    print("\n   📈 Résumé des KPI principaux:")
    fin = kpi_data['financiers']
    print(f"      - Chiffre d'affaires:  {fin['chiffre_affaires']:,.2f} €")
    print(f"      - Résultat net:        {fin['resultat_net']:,.2f} €")
    print(f"      - Trésorerie:          {fin['tresorerie']:,.2f} €")
    print(f"      - Marge nette:         {kpi_data['ratios']['marge_nette_pct']:.2f} %")

    if 'kpi_financiers' in kpi_data:
        fin_kpi_data = kpi_data['kpi_financiers']
        print(f"      - ROE:                 {fin_kpi_data['rentabilite']['roe_pct']:.2f} %")
        print(f"      - Ratio liquidité:     {fin_kpi_data['liquidite']['ratio_general']:.2f}")

    # Upload vers Grist
    print("\n3️⃣  Upload vers Grist...")

    try:
        client = GristClient()
        print(f"   ✓ Connexion à: {client.server_url}")
        print(f"   ✓ Document ID: {client.doc_id}")

        result = client.upload_kpi(kpi_data, kpi_table_name='KPI')
        print("   ✓ KPI uploadés avec succès!")

        # Récupérer l'historique des KPI
        print("\n4️⃣  Récupération de l'historique des KPI...")
        history = client.get_kpi_history(kpi_table_name='KPI', limit=5)
        print(f"   ✓ {len(history)} entrées KPI dans l'historique")

        if history:
            print("\n   📊 Dernières entrées KPI:")
            for i, record in enumerate(history[:3], 1):
                fields = record.get('fields', {})
                print(f"\n   {i}. Période: {fields.get('PeriodeDebut', '')} au {fields.get('PeriodeFin', '')}")
                print(f"      CA: {fields.get('ChiffreAffaires', 0):,.2f} €")
                print(f"      Résultat: {fields.get('ResultatNet', 0):,.2f} €")

    except ValueError as e:
        print(f"\n   ❌ Erreur de configuration: {e}")
        print("\n   💡 Assurez-vous d'avoir configuré le fichier .env avec:")
        print("      - GRIST_API_KEY")
        print("      - GRIST_DOC_ID")
        sys.exit(1)
    except Exception as e:
        print(f"\n   ❌ Erreur lors de l'upload: {e}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("✅ TERMINÉ!")
    print("=" * 80)
    print("\n💡 Vous pouvez maintenant consulter vos KPI dans Grist:")
    print(f"   {client.server_url}/doc/{client.doc_id}/p/1")
    print("\n💡 Pour générer un rapport détaillé:")
    print(f"   python generate_kpi_report.py {file_path}")


if __name__ == "__main__":
    main()
