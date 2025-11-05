"""Calculateur de KPI à partir des écritures comptables."""
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

from ..models.accounting_entry import AccountingEntry


class KPICalculator:
    """
    Calculateur de KPI (Key Performance Indicators) comptables.

    Analyse les écritures comptables pour produire des indicateurs
    de performance financiers et opérationnels.
    """

    def __init__(self, entries: List[AccountingEntry]):
        """
        Initialise le calculateur de KPI.

        Args:
            entries: Liste des écritures comptables
        """
        self.entries = entries
        self._accounts_cache = None
        self._by_class_cache = None
        self._by_journal_cache = None

    def _get_accounts_balance(self) -> Dict[str, Dict[str, Any]]:
        """Cache pour les soldes par compte."""
        if self._accounts_cache is None:
            self._accounts_cache = self._calculate_accounts_balance()
        return self._accounts_cache

    def _calculate_accounts_balance(self) -> Dict[str, Dict[str, Any]]:
        """Calcule les soldes par compte."""
        accounts = defaultdict(lambda: {
            'compte': '',
            'libelle': '',
            'debit': Decimal('0'),
            'credit': Decimal('0'),
            'solde': Decimal('0')
        })

        for entry in self.entries:
            acc = accounts[entry.compte_num]
            acc['compte'] = entry.compte_num
            acc['libelle'] = entry.compte_lib
            acc['debit'] += entry.debit
            acc['credit'] += entry.credit

        # Calculer les soldes
        for acc_num, acc in accounts.items():
            acc['solde'] = acc['debit'] - acc['credit']

        return dict(accounts)

    def _get_by_class(self) -> Dict[str, Dict[str, Any]]:
        """Cache pour les totaux par classe de comptes."""
        if self._by_class_cache is None:
            self._by_class_cache = self._calculate_by_class()
        return self._by_class_cache

    def _calculate_by_class(self) -> Dict[str, Dict[str, Any]]:
        """Calcule les totaux par classe de comptes."""
        classes = defaultdict(lambda: {
            'debit': Decimal('0'),
            'credit': Decimal('0'),
            'solde': Decimal('0')
        })

        for entry in self.entries:
            classe = entry.compte_num[0] if entry.compte_num else '0'
            classes[classe]['debit'] += entry.debit
            classes[classe]['credit'] += entry.credit

        for classe in classes:
            classes[classe]['solde'] = classes[classe]['debit'] - classes[classe]['credit']

        return dict(classes)

    def get_balance_by_class(self) -> Dict[str, Decimal]:
        """
        Retourne les soldes par classe de comptes.

        Returns:
            Dictionnaire {classe: solde}
        """
        by_class = self._get_by_class()
        return {k: v['solde'] for k, v in by_class.items()}

    def get_total_by_account_range(self, account_from: str, account_to: str,
                                   sense: str = 'solde') -> Decimal:
        """
        Calcule le total pour une plage de comptes.

        Args:
            account_from: Compte de début
            account_to: Compte de fin (inclus)
            sense: 'debit', 'credit' ou 'solde'

        Returns:
            Total pour la plage de comptes
        """
        accounts = self._get_accounts_balance()
        total = Decimal('0')

        for acc_num, acc_data in accounts.items():
            if account_from <= acc_num <= account_to:
                total += acc_data.get(sense, Decimal('0'))

        return total

    def get_chiffre_affaires(self, date_from: Optional[date] = None,
                            date_to: Optional[date] = None) -> Decimal:
        """
        Calcule le chiffre d'affaires (comptes 70x).

        Args:
            date_from: Date de début (optionnel)
            date_to: Date de fin (optionnel)

        Returns:
            Chiffre d'affaires
        """
        ca = Decimal('0')
        for entry in self.entries:
            if entry.compte_num.startswith('70'):
                # Filtrer par date si spécifié
                if date_from and entry.ecriture_date < date_from:
                    continue
                if date_to and entry.ecriture_date > date_to:
                    continue

                ca += entry.credit - entry.debit

        return ca

    def get_charges(self, date_from: Optional[date] = None,
                   date_to: Optional[date] = None) -> Decimal:
        """
        Calcule le total des charges (comptes 6xx).

        Args:
            date_from: Date de début (optionnel)
            date_to: Date de fin (optionnel)

        Returns:
            Total des charges
        """
        charges = Decimal('0')
        for entry in self.entries:
            if entry.compte_num.startswith('6'):
                # Filtrer par date si spécifié
                if date_from and entry.ecriture_date < date_from:
                    continue
                if date_to and entry.ecriture_date > date_to:
                    continue

                charges += entry.debit - entry.credit

        return charges

    def get_tresorerie(self) -> Decimal:
        """
        Calcule la trésorerie (comptes 51x et 53x).

        Returns:
            Trésorerie disponible
        """
        tresorerie = Decimal('0')
        accounts = self._get_accounts_balance()

        for acc_num, acc_data in accounts.items():
            if acc_num.startswith('51') or acc_num.startswith('53'):
                tresorerie += acc_data['solde']

        return tresorerie

    def get_creances_clients(self) -> Decimal:
        """
        Calcule les créances clients (comptes 41x).

        Returns:
            Total des créances clients
        """
        return self.get_total_by_account_range('410000', '419999', 'solde')

    def get_dettes_fournisseurs(self) -> Decimal:
        """
        Calcule les dettes fournisseurs (comptes 40x).

        Returns:
            Total des dettes fournisseurs (valeur positive)
        """
        return abs(self.get_total_by_account_range('400000', '409999', 'solde'))

    def get_resultat_net(self) -> Decimal:
        """
        Calcule le résultat net (produits - charges).

        Returns:
            Résultat net
        """
        produits = self.get_chiffre_affaires()
        charges = self.get_charges()
        return produits - charges

    def get_marge_brute(self) -> Decimal:
        """
        Calcule la marge brute (CA - achats).

        Returns:
            Marge brute
        """
        ca = self.get_chiffre_affaires()
        achats = self.get_total_by_account_range('600000', '609999', 'debit')
        return ca - achats

    def get_actif(self) -> Decimal:
        """
        Calcule le total de l'actif (classes 2 + 3 + 4 + 5).

        Returns:
            Total actif
        """
        by_class = self.get_balance_by_class()
        actif = Decimal('0')

        for classe in ['2', '3', '4', '5']:
            actif += by_class.get(classe, Decimal('0'))

        return actif

    def get_passif(self) -> Decimal:
        """
        Calcule le total du passif (classe 1).

        Returns:
            Total passif
        """
        by_class = self.get_balance_by_class()
        return abs(by_class.get('1', Decimal('0')))

    def get_fonds_roulement(self) -> Decimal:
        """
        Calcule le fonds de roulement (capitaux permanents - immobilisations).

        Returns:
            Fonds de roulement
        """
        capitaux_permanents = abs(self.get_total_by_account_range('100000', '199999', 'solde'))
        immobilisations = self.get_total_by_account_range('200000', '299999', 'solde')

        return capitaux_permanents - immobilisations

    def get_bfr(self) -> Decimal:
        """
        Calcule le besoin en fonds de roulement.
        BFR = Stocks + Créances clients - Dettes fournisseurs

        Returns:
            Besoin en fonds de roulement
        """
        stocks = self.get_total_by_account_range('300000', '399999', 'solde')
        creances = self.get_creances_clients()
        dettes = self.get_dettes_fournisseurs()

        return stocks + creances - dettes

    def get_aging_clients(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyse l'ancienneté des créances clients.

        Returns:
            Créances groupées par ancienneté
        """
        today = date.today()
        aging = {
            '0-30': [],
            '31-60': [],
            '61-90': [],
            '90+': []
        }

        for entry in self.entries:
            if entry.compte_num.startswith('41') and entry.debit > 0:
                days = (today - entry.ecriture_date).days

                if days <= 30:
                    bucket = '0-30'
                elif days <= 60:
                    bucket = '31-60'
                elif days <= 90:
                    bucket = '61-90'
                else:
                    bucket = '90+'

                aging[bucket].append({
                    'compte': entry.compte_num,
                    'libelle': entry.compte_lib,
                    'montant': float(entry.debit),
                    'date': entry.ecriture_date.strftime('%Y-%m-%d'),
                    'jours': days
                })

        return aging

    def get_top_clients(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retourne les top clients par montant.

        Args:
            limit: Nombre de clients à retourner

        Returns:
            Liste des top clients
        """
        clients = defaultdict(lambda: {'total': Decimal('0'), 'libelle': ''})

        for entry in self.entries:
            if entry.compte_num.startswith('41') and entry.comp_aux_num:
                clients[entry.comp_aux_num]['total'] += entry.debit - entry.credit
                clients[entry.comp_aux_num]['libelle'] = entry.comp_aux_lib or entry.comp_aux_num

        top = sorted(
            [{'compte': k, 'libelle': v['libelle'], 'total': float(v['total'])}
             for k, v in clients.items()],
            key=lambda x: x['total'],
            reverse=True
        )

        return top[:limit]

    def get_evolution_mensuelle(self) -> List[Dict[str, Any]]:
        """
        Calcule l'évolution mensuelle du CA et des charges.

        Returns:
            Liste des données mensuelles
        """
        monthly = defaultdict(lambda: {
            'ca': Decimal('0'),
            'charges': Decimal('0'),
            'resultat': Decimal('0')
        })

        for entry in self.entries:
            month_key = entry.ecriture_date.strftime('%Y-%m')

            if entry.compte_num.startswith('70'):
                monthly[month_key]['ca'] += entry.credit - entry.debit
            elif entry.compte_num.startswith('6'):
                monthly[month_key]['charges'] += entry.debit - entry.credit

        # Calculer le résultat
        for month in monthly:
            monthly[month]['resultat'] = monthly[month]['ca'] - monthly[month]['charges']

        # Convertir en liste triée
        result = []
        for month, data in sorted(monthly.items()):
            result.append({
                'mois': month,
                'ca': float(data['ca']),
                'charges': float(data['charges']),
                'resultat': float(data['resultat'])
            })

        return result

    def calculate_all_kpi(self) -> Dict[str, Any]:
        """
        Calcule tous les KPI disponibles.

        Returns:
            Dictionnaire contenant tous les KPI
        """
        return {
            'date_calcul': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'periode': {
                'debut': min(e.ecriture_date for e in self.entries).strftime('%Y-%m-%d'),
                'fin': max(e.ecriture_date for e in self.entries).strftime('%Y-%m-%d')
            },
            'financiers': {
                'chiffre_affaires': float(self.get_chiffre_affaires()),
                'charges': float(self.get_charges()),
                'resultat_net': float(self.get_resultat_net()),
                'marge_brute': float(self.get_marge_brute()),
                'tresorerie': float(self.get_tresorerie()),
                'creances_clients': float(self.get_creances_clients()),
                'dettes_fournisseurs': float(self.get_dettes_fournisseurs()),
                'fonds_roulement': float(self.get_fonds_roulement()),
                'bfr': float(self.get_bfr()),
            },
            'ratios': {
                'marge_brute_pct': float((self.get_marge_brute() / self.get_chiffre_affaires() * 100)
                                        if self.get_chiffre_affaires() > 0 else 0),
                'marge_nette_pct': float((self.get_resultat_net() / self.get_chiffre_affaires() * 100)
                                        if self.get_chiffre_affaires() > 0 else 0),
            },
            'top_clients': self.get_top_clients(10),
            'aging_clients': self.get_aging_clients(),
            'evolution_mensuelle': self.get_evolution_mensuelle()
        }
