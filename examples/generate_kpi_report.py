#!/usr/bin/env python3
"""
Script pour générer un rapport KPI complet à partir d'un fichier FEC.

Usage:
    python generate_kpi_report.py <fichier_fec> [--format json|text]

Exemple:
    python generate_kpi_report.py ../data/FEC_2024.txt
    python generate_kpi_report.py sample.txt --format json
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.readers.fec_reader import FECReader
from src.kpi.calculator import KPICalculator
from src.kpi.financial_kpi import FinancialKPI
from src.kpi.operational_kpi import OperationalKPI


def format_currency(value: float) -> str:
    """Formate une valeur en devise."""
    return f"{value:,.2f} €".replace(',', ' ')


def format_percentage(value: float) -> str:
    """Formate une valeur en pourcentage."""
    return f"{value:.2f} %"


def format_days(value: float) -> str:
    """Formate un nombre de jours."""
    return f"{value:.0f} jours"


def generate_text_report(kpi_data: dict) -> str:
    """
    Génère un rapport KPI au format texte.

    Args:
        kpi_data: Données KPI

    Returns:
        Rapport formaté
    """
    lines = []
    lines.append("=" * 80)
    lines.append("RAPPORT KPI - ANALYSE FINANCIÈRE ET OPÉRATIONNELLE")
    lines.append("=" * 80)
    lines.append(f"\nDate de génération: {kpi_data['date_calcul']}")
    lines.append(f"Période analysée: {kpi_data['periode']['debut']} au {kpi_data['periode']['fin']}")

    # KPI Financiers de base
    lines.append("\n" + "=" * 80)
    lines.append("1. INDICATEURS FINANCIERS DE BASE")
    lines.append("=" * 80)

    fin = kpi_data['financiers']
    lines.append(f"\n💰 Chiffre d'affaires:        {format_currency(fin['chiffre_affaires'])}")
    lines.append(f"📊 Charges totales:           {format_currency(fin['charges'])}")
    lines.append(f"✨ Résultat net:              {format_currency(fin['resultat_net'])}")
    lines.append(f"📈 Marge brute:               {format_currency(fin['marge_brute'])}")

    lines.append(f"\n💵 Trésorerie:                {format_currency(fin['tresorerie'])}")
    lines.append(f"👥 Créances clients:          {format_currency(fin['creances_clients'])}")
    lines.append(f"🏭 Dettes fournisseurs:       {format_currency(fin['dettes_fournisseurs'])}")

    lines.append(f"\n🔄 Fonds de roulement (FR):   {format_currency(fin['fonds_roulement'])}")
    lines.append(f"📦 Besoin en FR (BFR):        {format_currency(fin['bfr'])}")

    # Ratios
    lines.append("\n" + "=" * 80)
    lines.append("2. RATIOS FINANCIERS")
    lines.append("=" * 80)

    ratios = kpi_data['ratios']
    lines.append(f"\n📊 Taux de marge brute:       {format_percentage(ratios['marge_brute_pct'])}")
    lines.append(f"📊 Taux de marge nette:       {format_percentage(ratios['marge_nette_pct'])}")

    # KPI Financiers détaillés
    if 'kpi_financiers' in kpi_data:
        fin_kpi = kpi_data['kpi_financiers']

        lines.append("\n" + "-" * 80)
        lines.append("2.1 Liquidité")
        lines.append("-" * 80)
        liq = fin_kpi['liquidite']
        lines.append(f"\nRatio de liquidité générale:  {liq['ratio_general']:.2f}")
        lines.append(f"Ratio de liquidité immédiate: {liq['ratio_immediat']:.2f}")
        lines.append(f"Ratio de trésorerie:          {liq['ratio_tresorerie']:.2f}")
        lines.append(f"\n💡 {liq['interpretation']}")

        lines.append("\n" + "-" * 80)
        lines.append("2.2 Solvabilité")
        lines.append("-" * 80)
        solv = fin_kpi['solvabilite']
        lines.append(f"\nAutonomie financière:         {format_percentage(solv['autonomie_financiere_pct'])}")
        lines.append(f"Ratio d'endettement:          {solv['ratio_endettement']:.2f}")
        lines.append(f"\n💡 {solv['interpretation']}")

        lines.append("\n" + "-" * 80)
        lines.append("2.3 Rentabilité")
        lines.append("-" * 80)
        rent = fin_kpi['rentabilite']
        lines.append(f"\nROE (Return on Equity):       {format_percentage(rent['roe_pct'])}")
        lines.append(f"ROA (Return on Assets):       {format_percentage(rent['roa_pct'])}")
        lines.append(f"Taux de marge commerciale:    {format_percentage(rent['taux_marge_commerciale_pct'])}")
        lines.append(f"Taux de marge nette:          {format_percentage(rent['taux_marge_nette_pct'])}")
        lines.append(f"Seuil de rentabilité:         {format_currency(rent['seuil_rentabilite'])}")
        lines.append(f"\n💡 {rent['interpretation']}")

        lines.append("\n" + "-" * 80)
        lines.append("2.4 Délais et Rotation")
        lines.append("-" * 80)
        delais = fin_kpi['delais']
        lines.append(f"\nDélai de paiement clients:    {format_days(delais['delai_paiement_clients_jours'])}")
        lines.append(f"Délai de paiement fournisseurs: {format_days(delais['delai_paiement_fournisseurs_jours'])}")
        lines.append(f"Rotation des stocks:          {format_days(delais['rotation_stocks_jours'])}")
        lines.append(f"\n💡 {delais['interpretation']}")

    # KPI Opérationnels
    if 'kpi_operationnels' in kpi_data:
        op_kpi = kpi_data['kpi_operationnels']

        lines.append("\n" + "=" * 80)
        lines.append("3. INDICATEURS OPÉRATIONNELS")
        lines.append("=" * 80)

        vue = op_kpi['vue_ensemble']
        lines.append(f"\n📝 Nombre d'écritures:        {vue['nombre_ecritures']:,}")
        lines.append(f"📁 Comptes utilisés:          {vue['comptes_utilises']}")
        lines.append(f"📅 Jours d'activité:          {vue['jours_activite']}")

        # Productivité
        prod = op_kpi['productivite']
        lines.append(f"\n⚡ Productivité:")
        lines.append(f"  - Écritures par jour:       {prod['ecritures_par_jour']:.1f}")
        lines.append(f"  - Montant moyen:            {format_currency(prod['montant_moyen_ecriture'])}")
        lines.append(f"  - Taux d'équilibrage:       {format_percentage(prod['taux_equilibrage_pct'])}")

        # Qualité des données
        qualite = op_kpi['qualite_donnees']
        lines.append(f"\n📊 Qualité des données:")
        lines.append(f"  - Score de qualité:         {qualite['score_qualite']}/100")
        lines.append(f"  - Libellés renseignés:      {format_percentage(qualite['taux_libelles_renseignes_pct'])}")
        lines.append(f"  - Pièces renseignées:       {format_percentage(qualite['taux_pieces_renseignees_pct'])}")
        lines.append(f"  - Utilisation auxiliaires:  {format_percentage(qualite['taux_utilisation_auxiliaire_pct'])}")
        lines.append(f"  - Taux de lettrage:         {format_percentage(qualite['taux_lettrage_pct'])}")

        # Top journaux
        lines.append("\n" + "-" * 80)
        lines.append("3.1 Répartition par journal")
        lines.append("-" * 80)
        for journal in op_kpi['repartition_journaux'][:5]:
            lines.append(f"\n{journal['code']} - {journal['libelle']}")
            lines.append(f"  Écritures: {journal['nombre']:,} ({journal['pourcentage']:.1f}%)")
            lines.append(f"  Débit: {format_currency(journal['debit'])}")
            lines.append(f"  Crédit: {format_currency(journal['credit'])}")

        # Top comptes
        lines.append("\n" + "-" * 80)
        lines.append("3.2 Top 5 des comptes les plus utilisés")
        lines.append("-" * 80)
        for compte in op_kpi['top_comptes'][:5]:
            lines.append(f"\n{compte['compte']} - {compte['libelle']}")
            lines.append(f"  Nombre d'écritures: {compte['nombre_ecritures']}")
            lines.append(f"  Débit: {format_currency(compte['debit'])}, Crédit: {format_currency(compte['credit'])}")

    # Top clients
    lines.append("\n" + "=" * 80)
    lines.append("4. TOP CLIENTS")
    lines.append("=" * 80)
    for i, client in enumerate(kpi_data['top_clients'][:10], 1):
        lines.append(f"\n{i}. {client['libelle'] or client['compte']}")
        lines.append(f"   Total: {format_currency(client['total'])}")

    # Évolution mensuelle
    lines.append("\n" + "=" * 80)
    lines.append("5. ÉVOLUTION MENSUELLE")
    lines.append("=" * 80)
    lines.append(f"\n{'Mois':<10} {'CA':>15} {'Charges':>15} {'Résultat':>15}")
    lines.append("-" * 80)
    for month in kpi_data['evolution_mensuelle']:
        lines.append(
            f"{month['mois']:<10} "
            f"{format_currency(month['ca']):>15} "
            f"{format_currency(month['charges']):>15} "
            f"{format_currency(month['resultat']):>15}"
        )

    # Aging clients
    lines.append("\n" + "=" * 80)
    lines.append("6. BALANCE ÂGÉE CLIENTS")
    lines.append("=" * 80)
    aging = kpi_data['aging_clients']
    for bucket, entries in aging.items():
        total = sum(e['montant'] for e in entries)
        lines.append(f"\n{bucket} jours: {format_currency(total)} ({len(entries)} créances)")

    lines.append("\n" + "=" * 80)
    lines.append("FIN DU RAPPORT")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python generate_kpi_report.py <fichier_fec> [--format json|text]")
        sys.exit(1)

    file_path = sys.argv[1]
    output_format = 'text'

    if len(sys.argv) > 2 and sys.argv[2] == '--format':
        if len(sys.argv) > 3:
            output_format = sys.argv[3]

    print(f"📁 Lecture du fichier: {file_path}")

    # Lire le fichier FEC
    encodings = ['utf-8', 'latin1', 'cp1252']
    reader = None
    entries = None

    for encoding in encodings:
        try:
            reader = FECReader(file_path, encoding=encoding)
            entries = reader.read()
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)

    if not entries:
        print("❌ Impossible de lire le fichier")
        sys.exit(1)

    print(f"✓ {len(entries)} écritures lues")
    print("\n📊 Calcul des KPI en cours...")

    # Calculer les KPI
    calc = KPICalculator(entries)
    fin_kpi = FinancialKPI(calc)
    op_kpi = OperationalKPI(calc)

    # Collecter tous les KPI
    kpi_data = calc.calculate_all_kpi()
    kpi_data['kpi_financiers'] = fin_kpi.calculate_all_financial_kpi()
    kpi_data['kpi_operationnels'] = op_kpi.calculate_all_operational_kpi()

    print("✓ KPI calculés\n")

    # Générer le rapport selon le format
    if output_format == 'json':
        output = json.dumps(kpi_data, indent=2, ensure_ascii=False)
        print(output)

        # Sauvegarder dans un fichier
        output_file = f"kpi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n✓ Rapport sauvegardé dans {output_file}")

    else:  # format text
        report = generate_text_report(kpi_data)
        print(report)

        # Sauvegarder dans un fichier
        output_file = f"kpi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✓ Rapport sauvegardé dans {output_file}")


if __name__ == "__main__":
    main()
