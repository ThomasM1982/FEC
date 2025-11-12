"""Moteur de consolidation multi-entités."""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date
from collections import defaultdict

from ..models.accounting_entry import AccountingEntry
from ..kpi.calculator import KPICalculator
from .entity import Entity, EntityManager
from .intercompany import IntercompanyAnalyzer


class ConsolidationEngine:
    """
    Moteur de consolidation pour analyse multi-entités.

    Gère la consolidation des comptes, KPI et analyses pour un groupe
    de sociétés (SCCV + société mère).
    """

    def __init__(self, entity_manager: EntityManager):
        """
        Initialise le moteur de consolidation.

        Args:
            entity_manager: Gestionnaire d'entités
        """
        self.entity_manager = entity_manager
        self.entries_by_entity: Dict[str, List[AccountingEntry]] = {}
        self.kpi_by_entity: Dict[str, KPICalculator] = {}
        self.intercompany_analyzer = IntercompanyAnalyzer(entity_manager)

    def load_entity_data(self, entity_code: str, entries: List[AccountingEntry]) -> None:
        """
        Charge les données d'une entité.

        Args:
            entity_code: Code de l'entité
            entries: Liste des écritures
        """
        self.entries_by_entity[entity_code] = entries
        self.kpi_by_entity[entity_code] = KPICalculator(entries)
        self.intercompany_analyzer.load_entries(entity_code, entries)

    def filter_by_common_period(self) -> Dict[str, List[AccountingEntry]]:
        """
        Filtre les écritures sur la période commune à toutes les entités.

        Utile quand les exercices sont décalés.

        Returns:
            Dictionnaire {entity_code: entries_filtered}
        """
        # Trouver la période commune
        entity_codes = list(self.entries_by_entity.keys())
        common_period = self.entity_manager.get_common_period(entity_codes)

        if not common_period:
            return self.entries_by_entity

        # Filtrer les écritures
        filtered = {}
        start = common_period['start']
        end = common_period['end']

        for entity_code, entries in self.entries_by_entity.items():
            filtered[entity_code] = [
                e for e in entries
                if start <= e.ecriture_date <= end
            ]

        return filtered

    def get_consolidated_kpi(self, use_common_period: bool = False) -> Dict[str, Any]:
        """
        Calcule les KPI consolidés du groupe.

        Args:
            use_common_period: Utiliser la période commune aux entités

        Returns:
            KPI consolidés
        """
        entries_data = self.filter_by_common_period() if use_common_period else self.entries_by_entity

        # Agréger les KPI par entité
        total_ca = Decimal('0')
        total_charges = Decimal('0')
        total_tresorerie = Decimal('0')
        total_creances = Decimal('0')
        total_dettes = Decimal('0')

        kpi_by_entity = {}

        for entity_code, entries in entries_data.items():
            if not entries:
                continue

            entity = self.entity_manager.get_entity(entity_code)
            calc = KPICalculator(entries)

            ca = calc.get_chiffre_affaires()
            charges = calc.get_charges()
            tresorerie = calc.get_tresorerie()
            creances = calc.get_creances_clients()
            dettes = calc.get_dettes_fournisseurs()

            kpi_by_entity[entity_code] = {
                'name': entity.name if entity else entity_code,
                'ca': float(ca),
                'charges': float(charges),
                'resultat': float(ca - charges),
                'tresorerie': float(tresorerie),
                'creances': float(creances),
                'dettes': float(dettes)
            }

            # Agréger au niveau groupe
            total_ca += ca
            total_charges += charges
            total_tresorerie += tresorerie
            total_creances += creances
            total_dettes += dettes

        # Analyser les flux inter-compagnies
        self.intercompany_analyzer.analyze_all_flows()
        recon_stats = self.intercompany_analyzer.reconcile_flows()
        ic_balances = self.intercompany_analyzer.get_intercompany_balances()

        # Calculer le total des flux inter-compagnies (à éliminer)
        total_ic_flows = sum(bal['net_balance'] for bal in ic_balances)

        return {
            'consolidated': {
                'ca': float(total_ca),
                'charges': float(total_charges),
                'resultat': float(total_ca - total_charges),
                'tresorerie': float(total_tresorerie),
                'creances_externes': float(total_creances),  # Avant élimination IC
                'dettes_externes': float(total_dettes),
                'marge_pct': float((total_ca - total_charges) / total_ca * 100) if total_ca > 0 else 0
            },
            'by_entity': kpi_by_entity,
            'intercompany': {
                'total_flows': recon_stats['total_flows'],
                'reconciled': recon_stats['reconciled'],
                'unreconciled': recon_stats['unreconciled'],
                'reconciliation_rate': recon_stats['reconciliation_rate'],
                'total_ic_balances': total_ic_flows,
                'balances': ic_balances[:10]  # Top 10
            },
            'period': self._get_period_info(use_common_period)
        }

    def get_entity_comparison(self) -> List[Dict[str, Any]]:
        """
        Compare les performances des différentes entités.

        Returns:
            Liste des entités avec leurs performances
        """
        comparison = []

        for entity_code, calc in self.kpi_by_entity.items():
            entity = self.entity_manager.get_entity(entity_code)
            if not entity:
                continue

            ca = calc.get_chiffre_affaires()
            charges = calc.get_charges()
            resultat = ca - charges
            tresorerie = calc.get_tresorerie()

            comparison.append({
                'code': entity_code,
                'name': entity.name,
                'type': entity.entity_type,
                'ca': float(ca),
                'charges': float(charges),
                'resultat': float(resultat),
                'marge_pct': float((resultat / ca * 100) if ca > 0 else 0),
                'tresorerie': float(tresorerie),
                'ownership_pct': entity.ownership_pct
            })

        return sorted(comparison, key=lambda x: x['ca'], reverse=True)

    def get_sccv_performance_ranking(self) -> List[Dict[str, Any]]:
        """
        Classe les SCCV par performance.

        Returns:
            Classement des SCCV
        """
        sccv_entities = self.entity_manager.get_sccv_entities()
        ranking = []

        for entity in sccv_entities:
            if entity.code not in self.kpi_by_entity:
                continue

            calc = self.kpi_by_entity[entity.code]
            ca = calc.get_chiffre_affaires()
            resultat = calc.get_resultat_net()

            if ca > 0:
                ranking.append({
                    'code': entity.code,
                    'name': entity.name,
                    'ca': float(ca),
                    'resultat': float(resultat),
                    'marge_pct': float((resultat / ca * 100)),
                    'rentabilite': 'Excellente' if (resultat / ca) > 0.15
                                   else 'Bonne' if (resultat / ca) > 0.10
                                   else 'Moyenne' if (resultat / ca) > 0.05
                                   else 'Faible'
                })

        return sorted(ranking, key=lambda x: x['marge_pct'], reverse=True)

    def get_period_coverage(self) -> Dict[str, Any]:
        """
        Analyse la couverture des périodes comptables.

        Returns:
            Informations sur les périodes
        """
        entities = self.entity_manager.get_active_entities()

        if not entities:
            return {}

        periods = []
        for entity in entities:
            if entity.code in self.entries_by_entity:
                entries = self.entries_by_entity[entity.code]
                if entries:
                    actual_start = min(e.ecriture_date for e in entries)
                    actual_end = max(e.ecriture_date for e in entries)

                    periods.append({
                        'entity': entity.code,
                        'name': entity.name,
                        'exercice_start': entity.exercice_start.strftime('%Y-%m-%d'),
                        'exercice_end': entity.exercice_end.strftime('%Y-%m-%d'),
                        'actual_start': actual_start.strftime('%Y-%m-%d'),
                        'actual_end': actual_end.strftime('%Y-%m-%d'),
                        'duration_days': (entity.exercice_end - entity.exercice_start).days,
                        'coverage_pct': self._calculate_coverage(entity, entries)
                    })

        # Trouver la période commune
        common = self.entity_manager.get_common_period([e.code for e in entities])

        return {
            'periods_by_entity': periods,
            'common_period': {
                'start': common['start'].strftime('%Y-%m-%d'),
                'end': common['end'].strftime('%Y-%m-%d'),
                'duration_days': (common['end'] - common['start']).days
            } if common else None,
            'has_offset': len(set(e.exercice_start for e in entities)) > 1
        }

    def _calculate_coverage(self, entity: Entity, entries: List[AccountingEntry]) -> float:
        """Calcule le pourcentage de couverture de l'exercice."""
        if not entries:
            return 0.0

        exercice_days = (entity.exercice_end - entity.exercice_start).days
        dates = set(e.ecriture_date for e in entries)
        dates_in_exercice = [
            d for d in dates
            if entity.exercice_start <= d <= entity.exercice_end
        ]

        return (len(dates_in_exercice) / exercice_days * 100) if exercice_days > 0 else 0

    def _get_period_info(self, use_common: bool) -> Dict[str, Any]:
        """Récupère les informations de période."""
        if use_common:
            entity_codes = list(self.entries_by_entity.keys())
            common = self.entity_manager.get_common_period(entity_codes)
            if common:
                return {
                    'type': 'common',
                    'start': common['start'].strftime('%Y-%m-%d'),
                    'end': common['end'].strftime('%Y-%m-%d')
                }

        # Période globale
        all_entries = []
        for entries in self.entries_by_entity.values():
            all_entries.extend(entries)

        if all_entries:
            return {
                'type': 'full',
                'start': min(e.ecriture_date for e in all_entries).strftime('%Y-%m-%d'),
                'end': max(e.ecriture_date for e in all_entries).strftime('%Y-%m-%d')
            }

        return {'type': 'unknown'}

    def generate_consolidation_report(self) -> str:
        """
        Génère un rapport de consolidation complet.

        Returns:
            Rapport formaté
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT DE CONSOLIDATION GROUPE")
        lines.append("=" * 80)

        # Informations groupe
        parent = self.entity_manager.get_parent_entity()
        if parent:
            lines.append(f"\n🏢 Société mère: {parent.name}")

        sccv = self.entity_manager.get_sccv_entities()
        lines.append(f"📊 Nombre de SCCV: {len(sccv)}")
        lines.append(f"📁 Entités chargées: {len(self.entries_by_entity)}")

        # Couverture des périodes
        coverage = self.get_period_coverage()
        if coverage.get('has_offset'):
            lines.append("\n⚠️  Attention: Exercices décalés détectés")

        if coverage.get('common_period'):
            cp = coverage['common_period']
            lines.append(f"📅 Période commune: {cp['start']} au {cp['end']} ({cp['duration_days']} jours)")

        # KPI consolidés
        kpi = self.get_consolidated_kpi(use_common_period=True)
        cons = kpi['consolidated']

        lines.append("\n" + "=" * 80)
        lines.append("KPI CONSOLIDÉS GROUPE")
        lines.append("=" * 80)

        lines.append(f"\n💰 Chiffre d'affaires:    {cons['ca']:>20,.2f} €")
        lines.append(f"📊 Charges:               {cons['charges']:>20,.2f} €")
        lines.append(f"✨ Résultat net:          {cons['resultat']:>20,.2f} €")
        lines.append(f"📈 Marge nette:           {cons['marge_pct']:>19.2f} %")
        lines.append(f"\n💵 Trésorerie groupe:     {cons['tresorerie']:>20,.2f} €")

        # Inter-compagnies
        ic = kpi['intercompany']
        lines.append("\n" + "=" * 80)
        lines.append("ANALYSE INTER-COMPAGNIES")
        lines.append("=" * 80)

        lines.append(f"\n🔄 Flux identifiés:       {ic['total_flows']}")
        lines.append(f"✓  Flux rapprochés:       {ic['reconciled']} ({ic['reconciliation_rate']:.1f}%)")
        lines.append(f"⚠️  Flux non rapprochés:   {ic['unreconciled']}")
        lines.append(f"💱 Soldes IC nets:        {ic['total_ic_balances']:>20,.2f} €")

        if ic['balances']:
            lines.append("\n📊 Top 5 des soldes inter-compagnies:")
            for i, bal in enumerate(ic['balances'][:5], 1):
                lines.append(f"\n  {i}. {bal['entity1']} ↔ {bal['entity2']}")
                lines.append(f"     {bal['who_owes']}")

        # Comparaison entités
        comparison = self.get_entity_comparison()
        lines.append("\n" + "=" * 80)
        lines.append("COMPARAISON DES ENTITÉS")
        lines.append("=" * 80)

        lines.append(f"\n{'Entité':<30} {'CA':>15} {'Résultat':>15} {'Marge':>10}")
        lines.append("-" * 80)

        for entity in comparison[:10]:
            lines.append(
                f"{entity['name'][:30]:<30} "
                f"{entity['ca']:>15,.0f} "
                f"{entity['resultat']:>15,.0f} "
                f"{entity['marge_pct']:>9.1f}%"
            )

        # Classement SCCV
        if sccv:
            ranking = self.get_sccv_performance_ranking()
            lines.append("\n" + "=" * 80)
            lines.append("CLASSEMENT DES SCCV PAR RENTABILITÉ")
            lines.append("=" * 80)

            for i, sccv_data in enumerate(ranking, 1):
                lines.append(f"\n{i}. {sccv_data['name']}")
                lines.append(f"   CA: {sccv_data['ca']:,.2f} € | Marge: {sccv_data['marge_pct']:.2f}% | {sccv_data['rentabilite']}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)
