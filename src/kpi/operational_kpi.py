"""KPI opérationnels pour l'analyse de la performance."""
from typing import Dict, Any, List
from decimal import Decimal
from collections import defaultdict
from datetime import date

from .calculator import KPICalculator


class OperationalKPI:
    """
    Calcule les KPI opérationnels.

    Indicateurs de performance opérationnelle, analyse par journal,
    statistiques de production d'écritures, etc.
    """

    def __init__(self, calculator: KPICalculator):
        """
        Initialise les KPI opérationnels.

        Args:
            calculator: Instance du calculateur de base
        """
        self.calc = calculator

    def get_nombre_ecritures(self) -> int:
        """Retourne le nombre total d'écritures."""
        return len(self.calc.entries)

    def get_nombre_ecritures_par_journal(self) -> Dict[str, int]:
        """
        Compte les écritures par journal.

        Returns:
            Dictionnaire {code_journal: nombre}
        """
        journals = defaultdict(int)
        for entry in self.calc.entries:
            journals[entry.journal_code] += 1
        return dict(journals)

    def get_montant_moyen_ecriture(self) -> Decimal:
        """
        Calcule le montant moyen par écriture.

        Returns:
            Montant moyen
        """
        if not self.calc.entries:
            return Decimal('0')

        total = sum(entry.get_amount() for entry in self.calc.entries)
        return total / len(self.calc.entries)

    def get_repartition_par_journal(self) -> List[Dict[str, Any]]:
        """
        Analyse la répartition par journal.

        Returns:
            Liste des journaux avec statistiques
        """
        journals = defaultdict(lambda: {
            'code': '',
            'libelle': '',
            'nombre': 0,
            'debit': Decimal('0'),
            'credit': Decimal('0'),
            'pourcentage': 0
        })

        for entry in self.calc.entries:
            j = journals[entry.journal_code]
            j['code'] = entry.journal_code
            j['libelle'] = entry.journal_lib
            j['nombre'] += 1
            j['debit'] += entry.debit
            j['credit'] += entry.credit

        total = len(self.calc.entries)

        result = []
        for code, data in journals.items():
            result.append({
                'code': data['code'],
                'libelle': data['libelle'],
                'nombre': data['nombre'],
                'debit': float(data['debit']),
                'credit': float(data['credit']),
                'pourcentage': round((data['nombre'] / total * 100), 2) if total > 0 else 0
            })

        return sorted(result, key=lambda x: x['nombre'], reverse=True)

    def get_taux_equilibrage(self) -> Decimal:
        """
        Calcule le taux d'équilibrage (écritures équilibrées).

        Returns:
            Pourcentage d'écritures équilibrées
        """
        if not self.calc.entries:
            return Decimal('100')

        # Grouper par numéro d'écriture
        entries_by_num = defaultdict(list)
        for entry in self.calc.entries:
            entries_by_num[entry.ecriture_num].append(entry)

        equilibrees = 0
        for ecriture_num, entries in entries_by_num.items():
            total_debit = sum(e.debit for e in entries)
            total_credit = sum(e.credit for e in entries)

            if abs(total_debit - total_credit) < Decimal('0.01'):
                equilibrees += 1

        return (Decimal(equilibrees) / len(entries_by_num)) * 100

    def get_ecritures_par_jour(self) -> Decimal:
        """
        Calcule le nombre moyen d'écritures par jour.

        Returns:
            Moyenne d'écritures par jour
        """
        if not self.calc.entries:
            return Decimal('0')

        dates = set(entry.ecriture_date for entry in self.calc.entries)
        return Decimal(len(self.calc.entries)) / len(dates)

    def get_jours_activite(self) -> int:
        """
        Retourne le nombre de jours avec activité comptable.

        Returns:
            Nombre de jours
        """
        dates = set(entry.ecriture_date for entry in self.calc.entries)
        return len(dates)

    def get_comptes_utilises(self) -> int:
        """
        Retourne le nombre de comptes différents utilisés.

        Returns:
            Nombre de comptes
        """
        comptes = set(entry.compte_num for entry in self.calc.entries)
        return len(comptes)

    def get_top_comptes_utilises(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retourne les comptes les plus utilisés.

        Args:
            limit: Nombre de comptes à retourner

        Returns:
            Liste des top comptes
        """
        comptes = defaultdict(lambda: {
            'nombre': 0,
            'libelle': '',
            'debit': Decimal('0'),
            'credit': Decimal('0')
        })

        for entry in self.calc.entries:
            c = comptes[entry.compte_num]
            c['nombre'] += 1
            c['libelle'] = entry.compte_lib
            c['debit'] += entry.debit
            c['credit'] += entry.credit

        result = []
        for compte_num, data in comptes.items():
            result.append({
                'compte': compte_num,
                'libelle': data['libelle'],
                'nombre_ecritures': data['nombre'],
                'debit': float(data['debit']),
                'credit': float(data['credit'])
            })

        return sorted(result, key=lambda x: x['nombre_ecritures'], reverse=True)[:limit]

    def get_repartition_par_classe(self) -> List[Dict[str, Any]]:
        """
        Analyse la répartition par classe de comptes.

        Returns:
            Liste des classes avec statistiques
        """
        classes = defaultdict(lambda: {
            'nombre': 0,
            'debit': Decimal('0'),
            'credit': Decimal('0')
        })

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

        for entry in self.calc.entries:
            classe = entry.compte_num[0] if entry.compte_num else '0'
            classes[classe]['nombre'] += 1
            classes[classe]['debit'] += entry.debit
            classes[classe]['credit'] += entry.credit

        total = len(self.calc.entries)

        result = []
        for classe, data in sorted(classes.items()):
            result.append({
                'classe': classe,
                'libelle': classe_names.get(classe, 'Autres'),
                'nombre': data['nombre'],
                'pourcentage': round((data['nombre'] / total * 100), 2) if total > 0 else 0,
                'debit': float(data['debit']),
                'credit': float(data['credit']),
                'solde': float(data['debit'] - data['credit'])
            })

        return result

    def get_qualite_donnees(self) -> Dict[str, Any]:
        """
        Évalue la qualité des données comptables.

        Returns:
            Indicateurs de qualité
        """
        total = len(self.calc.entries)
        if total == 0:
            return {}

        # Compter les problèmes potentiels
        sans_libelle = sum(1 for e in self.calc.entries if not e.ecriture_lib or e.ecriture_lib.strip() == '')
        sans_piece = sum(1 for e in self.calc.entries if not e.piece_ref or e.piece_ref.strip() == '')
        avec_auxiliaire = sum(1 for e in self.calc.entries if e.comp_aux_num)
        avec_lettrage = sum(1 for e in self.calc.entries if e.ecriture_let)

        return {
            'total_ecritures': total,
            'sans_libelle': sans_libelle,
            'sans_piece': sans_piece,
            'avec_auxiliaire': avec_auxiliaire,
            'avec_lettrage': avec_lettrage,
            'taux_libelles_renseignes_pct': round(((total - sans_libelle) / total * 100), 2),
            'taux_pieces_renseignees_pct': round(((total - sans_piece) / total * 100), 2),
            'taux_utilisation_auxiliaire_pct': round((avec_auxiliaire / total * 100), 2),
            'taux_lettrage_pct': round((avec_lettrage / total * 100), 2),
            'score_qualite': self._calculate_quality_score(
                (total - sans_libelle) / total,
                (total - sans_piece) / total,
                avec_auxiliaire / total
            )
        }

    def _calculate_quality_score(self, taux_libelle: float, taux_piece: float,
                                 taux_aux: float) -> int:
        """
        Calcule un score de qualité sur 100.

        Args:
            taux_libelle: Taux de libellés renseignés
            taux_piece: Taux de pièces renseignées
            taux_aux: Taux d'utilisation des comptes auxiliaires

        Returns:
            Score sur 100
        """
        score = (
            taux_libelle * 40 +  # 40% pour les libellés
            taux_piece * 40 +     # 40% pour les pièces
            taux_aux * 20         # 20% pour les auxiliaires
        )
        return round(score * 100)

    def get_productivite(self) -> Dict[str, Any]:
        """
        Analyse la productivité comptable.

        Returns:
            Indicateurs de productivité
        """
        return {
            'nombre_ecritures': self.get_nombre_ecritures(),
            'jours_activite': self.get_jours_activite(),
            'ecritures_par_jour': float(self.get_ecritures_par_jour()),
            'montant_moyen_ecriture': float(self.get_montant_moyen_ecriture()),
            'comptes_utilises': self.get_comptes_utilises(),
            'taux_equilibrage_pct': float(self.get_taux_equilibrage())
        }

    def calculate_all_operational_kpi(self) -> Dict[str, Any]:
        """
        Calcule tous les KPI opérationnels.

        Returns:
            Dictionnaire de tous les KPI opérationnels
        """
        return {
            'vue_ensemble': {
                'nombre_ecritures': self.get_nombre_ecritures(),
                'comptes_utilises': self.get_comptes_utilises(),
                'jours_activite': self.get_jours_activite()
            },
            'repartition_journaux': self.get_repartition_par_journal(),
            'repartition_classes': self.get_repartition_par_classe(),
            'top_comptes': self.get_top_comptes_utilises(10),
            'productivite': self.get_productivite(),
            'qualite_donnees': self.get_qualite_donnees()
        }
