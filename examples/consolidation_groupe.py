#!/usr/bin/env python3
"""
Script pour analyser et consolider plusieurs FEC de SCCV.

Usage:
    python consolidation_groupe.py <config_entities.json> <repertoire_fec>

Exemple:
    python consolidation_groupe.py entities_config.json ../data/fec_sccv/

Le fichier JSON doit contenir la configuration des entités:
{
    "entities": [
        {
            "code": "MERE",
            "name": "Société Mère Promotion",
            "type": "MERE",
            "siren": "123456789",
            "exercice_start": "2024-01-01",
            "exercice_end": "2024-12-31",
            "intercompany_prefix": "451"
        },
        {
            "code": "SCCV001",
            "name": "SCCV Projet Résidence A",
            "type": "SCCV",
            "parent_code": "MERE",
            "ownership_pct": 100.0,
            "exercice_start": "2024-01-01",
            "exercice_end": "2024-12-31",
            "intercompany_prefix": "451"
        }
    ]
}
"""
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.consolidation.entity import EntityManager, Entity
from src.consolidation.consolidation import ConsolidationEngine
from src.readers.fec_reader import FECReader
from src.grist.client import GristClient


def load_entities_from_config(config_file: str) -> EntityManager:
    """
    Charge les entités depuis un fichier de configuration JSON.

    Args:
        config_file: Chemin vers le fichier JSON

    Returns:
        EntityManager avec les entités chargées
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    manager = EntityManager()
    manager.load_from_dict_list(config['entities'])

    return manager


def find_fec_files(directory: str, entity_code: str) -> list:
    """
    Trouve les fichiers FEC pour une entité.

    Cherche des fichiers avec le pattern: <entity_code>*.txt ou <entity_code>*.csv

    Args:
        directory: Répertoire contenant les FEC
        entity_code: Code de l'entité

    Returns:
        Liste des fichiers trouvés
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        return []

    patterns = [
        f"{entity_code}*.txt",
        f"{entity_code}*.csv",
        f"{entity_code}*.xlsx",
        f"*{entity_code}*.txt",
        f"*{entity_code}*.csv"
    ]

    files = []
    for pattern in patterns:
        files.extend(dir_path.glob(pattern))

    return list(set(files))  # Dédupliquer


def main():
    """Fonction principale."""
    if len(sys.argv) < 3:
        print("Usage: python consolidation_groupe.py <config_entities.json> <repertoire_fec>")
        print("\nExemple:")
        print("  python consolidation_groupe.py entities.json ../data/fec_sccv/")
        sys.exit(1)

    config_file = sys.argv[1]
    fec_directory = sys.argv[2]

    print("=" * 80)
    print("CONSOLIDATION MULTI-ENTITÉS - ANALYSE GROUPE")
    print("=" * 80)

    # 1. Charger la configuration des entités
    print("\n1️⃣  Chargement de la configuration des entités...")
    try:
        entity_manager = load_entities_from_config(config_file)
        print(f"   ✓ {len(entity_manager.get_all_entities())} entités chargées")

        parent = entity_manager.get_parent_entity()
        if parent:
            print(f"   📊 Société mère: {parent.name}")

        sccv_list = entity_manager.get_sccv_entities()
        print(f"   🏢 SCCV: {len(sccv_list)}")
        for sccv in sccv_list[:5]:
            print(f"      - {sccv.code}: {sccv.name}")
        if len(sccv_list) > 5:
            print(f"      ... et {len(sccv_list) - 5} autres")

    except Exception as e:
        print(f"   ❌ Erreur lors du chargement de la configuration: {e}")
        sys.exit(1)

    # 2. Charger les FEC de chaque entité
    print("\n2️⃣  Chargement des fichiers FEC...")
    consolidation = ConsolidationEngine(entity_manager)

    loaded_entities = 0
    for entity in entity_manager.get_active_entities():
        # Chercher le fichier FEC
        fec_files = find_fec_files(fec_directory, entity.code)

        if not fec_files:
            print(f"   ⚠️  Aucun FEC trouvé pour {entity.code} ({entity.name})")
            continue

        fec_file = fec_files[0]  # Prendre le premier
        print(f"   📁 {entity.code}: {fec_file.name}")

        try:
            # Lire le FEC
            reader = FECReader(str(fec_file), encoding='utf-8')
            entries = reader.read()

            # Charger dans le moteur de consolidation
            consolidation.load_entity_data(entity.code, entries)
            loaded_entities += 1

            print(f"      ✓ {len(entries)} écritures chargées")

        except UnicodeDecodeError:
            try:
                reader = FECReader(str(fec_file), encoding='latin1')
                entries = reader.read()
                consolidation.load_entity_data(entity.code, entries)
                loaded_entities += 1
                print(f"      ✓ {len(entries)} écritures chargées (latin1)")
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
        except Exception as e:
            print(f"      ❌ Erreur: {e}")

    if loaded_entities == 0:
        print("\n❌ Aucune entité chargée. Vérifiez le répertoire des FEC.")
        sys.exit(1)

    print(f"\n   ✓ {loaded_entities} entités chargées avec succès")

    # 3. Analyser la couverture des périodes
    print("\n3️⃣  Analyse des périodes comptables...")
    coverage = consolidation.get_period_coverage()

    if coverage.get('has_offset'):
        print("   ⚠️  Attention: Exercices décalés détectés")
        print("\n   📅 Périodes par entité:")
        for period in coverage['periods_by_entity']:
            print(f"      {period['entity']}: {period['exercice_start']} → {period['exercice_end']}")

    if coverage.get('common_period'):
        cp = coverage['common_period']
        print(f"\n   ✅ Période commune identifiée:")
        print(f"      {cp['start']} → {cp['end']} ({cp['duration_days']} jours)")
    else:
        print("\n   ⚠️  Aucune période commune trouvée")

    # 4. Calculer la consolidation
    print("\n4️⃣  Calcul de la consolidation groupe...")
    use_common = coverage.get('common_period') is not None
    kpi = consolidation.get_consolidated_kpi(use_common_period=use_common)

    cons = kpi['consolidated']
    print(f"\n   💰 KPI Consolidés:")
    print(f"      CA groupe:        {cons['ca']:>20,.2f} €")
    print(f"      Charges:          {cons['charges']:>20,.2f} €")
    print(f"      Résultat net:     {cons['resultat']:>20,.2f} €")
    print(f"      Marge:            {cons['marge_pct']:>19.2f} %")
    print(f"      Trésorerie:       {cons['tresorerie']:>20,.2f} €")

    # 5. Analyser les flux inter-compagnies
    print("\n5️⃣  Analyse des flux inter-compagnies...")
    ic = kpi['intercompany']
    print(f"\n   🔄 Flux inter-compagnies:")
    print(f"      Total flux:       {ic['total_flows']}")
    print(f"      Rapprochés:       {ic['reconciled']} ({ic['reconciliation_rate']:.1f}%)")
    print(f"      Non rapprochés:   {ic['unreconciled']}")
    print(f"      Soldes nets:      {ic['total_ic_balances']:>20,.2f} €")

    if ic['balances']:
        print(f"\n   📊 Top 5 des soldes inter-compagnies:")
        for i, bal in enumerate(ic['balances'][:5], 1):
            print(f"\n      {i}. {bal['entity1']} ↔ {bal['entity2']}")
            print(f"         {bal['who_owes']}")

    # 6. Classement des SCCV
    print("\n6️⃣  Classement des SCCV par performance...")
    ranking = consolidation.get_sccv_performance_ranking()

    if ranking:
        print(f"\n   {'Rang':<6} {'SCCV':<30} {'CA':>15} {'Marge':>10} {'Perf':>12}")
        print("   " + "-" * 75)
        for i, sccv in enumerate(ranking, 1):
            print(
                f"   {i:<6} {sccv['name'][:30]:<30} "
                f"{sccv['ca']:>15,.0f} "
                f"{sccv['marge_pct']:>9.1f}% "
                f"{sccv['rentabilite']:>12}"
            )

    # 7. Upload vers Grist (optionnel)
    print("\n7️⃣  Upload vers Grist...")
    try:
        client = GristClient()

        # Upload des entités
        entities_data = entity_manager.to_dict_list()
        client.upload_entities(entities_data)
        print(f"   ✓ {len(entities_data)} entités uploadées")

        # Upload de la consolidation
        client.upload_consolidation(kpi)
        print("   ✓ Données de consolidation uploadées")

        # Upload des flux IC
        client.upload_intercompany_balances(ic['balances'])
        print(f"   ✓ {len(ic['balances'])} flux inter-compagnies uploadés")

        print(f"\n   🌐 Consultez vos données dans Grist:")
        print(f"      {client.server_url}/doc/{client.doc_id}")

    except ValueError as e:
        print(f"   ⚠️  Grist non configuré: {e}")
        print("   💡 Configurez le fichier .env pour activer l'upload Grist")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'upload: {e}")

    # 8. Génération du rapport
    print("\n8️⃣  Génération du rapport de consolidation...")
    report = consolidation.generate_consolidation_report()

    output_file = f"consolidation_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"   ✓ Rapport sauvegardé: {output_file}")

    print("\n" + "=" * 80)
    print("✅ CONSOLIDATION TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()
