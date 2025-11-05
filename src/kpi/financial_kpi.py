"""KPI financiers et ratios d'analyse financière."""
from typing import Dict, Any
from decimal import Decimal

from .calculator import KPICalculator


class FinancialKPI:
    """
    Calcule les KPI financiers et ratios d'analyse.

    Ratios de liquidité, solvabilité, rentabilité, etc.
    """

    def __init__(self, calculator: KPICalculator):
        """
        Initialise les KPI financiers.

        Args:
            calculator: Instance du calculateur de base
        """
        self.calc = calculator

    def get_ratio_liquidite_generale(self) -> Decimal:
        """
        Ratio de liquidité générale (current ratio).
        Actif circulant / Dettes à court terme

        Returns:
            Ratio de liquidité générale
        """
        # Actif circulant (classes 3, 4, 5)
        actif_circulant = (
            self.calc.get_total_by_account_range('300000', '399999', 'solde') +
            self.calc.get_total_by_account_range('400000', '499999', 'solde') +
            self.calc.get_total_by_account_range('500000', '599999', 'solde')
        )

        # Dettes à court terme (comptes 40x + 42x + 43x + 44x)
        dettes_ct = (
            abs(self.calc.get_total_by_account_range('400000', '409999', 'solde')) +
            abs(self.calc.get_total_by_account_range('420000', '449999', 'solde'))
        )

        if dettes_ct == 0:
            return Decimal('0')

        return actif_circulant / dettes_ct

    def get_ratio_liquidite_immediate(self) -> Decimal:
        """
        Ratio de liquidité immédiate (quick ratio).
        (Actif circulant - Stocks) / Dettes à court terme

        Returns:
            Ratio de liquidité immédiate
        """
        # Actif circulant sans stocks
        actif_liquide = (
            self.calc.get_total_by_account_range('400000', '499999', 'solde') +
            self.calc.get_total_by_account_range('500000', '599999', 'solde')
        )

        # Dettes à court terme
        dettes_ct = (
            abs(self.calc.get_total_by_account_range('400000', '409999', 'solde')) +
            abs(self.calc.get_total_by_account_range('420000', '449999', 'solde'))
        )

        if dettes_ct == 0:
            return Decimal('0')

        return actif_liquide / dettes_ct

    def get_ratio_tresorerie(self) -> Decimal:
        """
        Ratio de trésorerie (cash ratio).
        Trésorerie / Dettes à court terme

        Returns:
            Ratio de trésorerie
        """
        tresorerie = self.calc.get_tresorerie()

        dettes_ct = (
            abs(self.calc.get_total_by_account_range('400000', '409999', 'solde')) +
            abs(self.calc.get_total_by_account_range('420000', '449999', 'solde'))
        )

        if dettes_ct == 0:
            return Decimal('0')

        return tresorerie / dettes_ct

    def get_ratio_autonomie_financiere(self) -> Decimal:
        """
        Ratio d'autonomie financière.
        Capitaux propres / Total passif

        Returns:
            Ratio d'autonomie financière (%)
        """
        capitaux_propres = abs(self.calc.get_total_by_account_range('100000', '199999', 'solde'))
        total_passif = self.calc.get_passif()

        if total_passif == 0:
            return Decimal('0')

        return (capitaux_propres / total_passif) * 100

    def get_ratio_endettement(self) -> Decimal:
        """
        Ratio d'endettement.
        Dettes totales / Capitaux propres

        Returns:
            Ratio d'endettement
        """
        capitaux_propres = abs(self.calc.get_total_by_account_range('100000', '199999', 'solde'))
        dettes_totales = (
            abs(self.calc.get_total_by_account_range('160000', '169999', 'solde')) +
            abs(self.calc.get_total_by_account_range('400000', '499999', 'solde'))
        )

        if capitaux_propres == 0:
            return Decimal('0')

        return dettes_totales / capitaux_propres

    def get_roe(self) -> Decimal:
        """
        ROE (Return On Equity) - Rentabilité des capitaux propres.
        Résultat net / Capitaux propres * 100

        Returns:
            ROE en pourcentage
        """
        resultat = self.calc.get_resultat_net()
        capitaux_propres = abs(self.calc.get_total_by_account_range('100000', '199999', 'solde'))

        if capitaux_propres == 0:
            return Decimal('0')

        return (resultat / capitaux_propres) * 100

    def get_roa(self) -> Decimal:
        """
        ROA (Return On Assets) - Rentabilité de l'actif.
        Résultat net / Total actif * 100

        Returns:
            ROA en pourcentage
        """
        resultat = self.calc.get_resultat_net()
        actif = self.calc.get_actif()

        if actif == 0:
            return Decimal('0')

        return (resultat / actif) * 100

    def get_delai_paiement_clients(self) -> Decimal:
        """
        Délai moyen de paiement clients en jours.
        (Créances clients / CA TTC) * 365

        Returns:
            Nombre de jours moyen
        """
        creances = self.calc.get_creances_clients()
        ca = self.calc.get_chiffre_affaires()

        # CA TTC (approximation avec TVA 20%)
        ca_ttc = ca * Decimal('1.20')

        if ca_ttc == 0:
            return Decimal('0')

        return (creances / ca_ttc) * 365

    def get_delai_paiement_fournisseurs(self) -> Decimal:
        """
        Délai moyen de paiement fournisseurs en jours.
        (Dettes fournisseurs / Achats TTC) * 365

        Returns:
            Nombre de jours moyen
        """
        dettes = self.calc.get_dettes_fournisseurs()
        achats = self.calc.get_total_by_account_range('600000', '609999', 'debit')

        # Achats TTC (approximation avec TVA 20%)
        achats_ttc = achats * Decimal('1.20')

        if achats_ttc == 0:
            return Decimal('0')

        return (dettes / achats_ttc) * 365

    def get_rotation_stocks(self) -> Decimal:
        """
        Rotation des stocks en jours.
        (Stock moyen / Coût d'achat des marchandises vendues) * 365

        Returns:
            Nombre de jours de stock
        """
        stocks = self.calc.get_total_by_account_range('300000', '399999', 'solde')
        achats = self.calc.get_total_by_account_range('600000', '609999', 'debit')

        if achats == 0:
            return Decimal('0')

        return (stocks / achats) * 365

    def get_taux_marge_commerciale(self) -> Decimal:
        """
        Taux de marge commerciale.
        (Marge commerciale / Ventes de marchandises) * 100

        Returns:
            Taux de marge en pourcentage
        """
        ventes = self.calc.get_chiffre_affaires()
        achats = self.calc.get_total_by_account_range('600000', '609999', 'debit')
        marge = ventes - achats

        if ventes == 0:
            return Decimal('0')

        return (marge / ventes) * 100

    def get_taux_marge_nette(self) -> Decimal:
        """
        Taux de marge nette.
        (Résultat net / CA) * 100

        Returns:
            Taux de marge nette en pourcentage
        """
        resultat = self.calc.get_resultat_net()
        ca = self.calc.get_chiffre_affaires()

        if ca == 0:
            return Decimal('0')

        return (resultat / ca) * 100

    def get_seuil_rentabilite(self) -> Decimal:
        """
        Calcule le seuil de rentabilité (point mort).
        Charges fixes / Taux de marge sur coûts variables

        Simplifié: Charges totales nécessaires pour atteindre l'équilibre

        Returns:
            Seuil de rentabilité
        """
        charges = self.calc.get_charges()
        ca = self.calc.get_chiffre_affaires()

        if ca == 0:
            return Decimal('0')

        # Estimation du taux de marge
        taux_marge = (ca - charges) / ca if ca > 0 else Decimal('0')

        if taux_marge == 0:
            return Decimal('0')

        return charges / taux_marge

    def calculate_all_financial_kpi(self) -> Dict[str, Any]:
        """
        Calcule tous les KPI financiers.

        Returns:
            Dictionnaire de tous les KPI financiers
        """
        return {
            'liquidite': {
                'ratio_general': float(self.get_ratio_liquidite_generale()),
                'ratio_immediat': float(self.get_ratio_liquidite_immediate()),
                'ratio_tresorerie': float(self.get_ratio_tresorerie()),
                'interpretation': self._interpret_liquidite()
            },
            'solvabilite': {
                'autonomie_financiere_pct': float(self.get_ratio_autonomie_financiere()),
                'ratio_endettement': float(self.get_ratio_endettement()),
                'interpretation': self._interpret_solvabilite()
            },
            'rentabilite': {
                'roe_pct': float(self.get_roe()),
                'roa_pct': float(self.get_roa()),
                'taux_marge_commerciale_pct': float(self.get_taux_marge_commerciale()),
                'taux_marge_nette_pct': float(self.get_taux_marge_nette()),
                'seuil_rentabilite': float(self.get_seuil_rentabilite()),
                'interpretation': self._interpret_rentabilite()
            },
            'delais': {
                'delai_paiement_clients_jours': float(self.get_delai_paiement_clients()),
                'delai_paiement_fournisseurs_jours': float(self.get_delai_paiement_fournisseurs()),
                'rotation_stocks_jours': float(self.get_rotation_stocks()),
                'interpretation': self._interpret_delais()
            }
        }

    def _interpret_liquidite(self) -> str:
        """Interprète les ratios de liquidité."""
        ratio = float(self.get_ratio_liquidite_generale())

        if ratio >= 2:
            return "Excellente liquidité - L'entreprise peut facilement honorer ses dettes à court terme"
        elif ratio >= 1.5:
            return "Bonne liquidité - Situation financière saine"
        elif ratio >= 1:
            return "Liquidité acceptable - Surveiller l'évolution"
        else:
            return "⚠️ Liquidité faible - Risque de difficultés à payer les dettes à court terme"

    def _interpret_solvabilite(self) -> str:
        """Interprète les ratios de solvabilité."""
        autonomie = float(self.get_ratio_autonomie_financiere())

        if autonomie >= 50:
            return "Excellente autonomie financière - Structure financière très solide"
        elif autonomie >= 30:
            return "Bonne autonomie financière - Équilibre sain entre fonds propres et dettes"
        elif autonomie >= 20:
            return "Autonomie financière moyenne - Attention à l'endettement"
        else:
            return "⚠️ Faible autonomie financière - Dépendance importante aux créanciers"

    def _interpret_rentabilite(self) -> str:
        """Interprète les ratios de rentabilité."""
        marge_nette = float(self.get_taux_marge_nette())

        if marge_nette >= 10:
            return "Excellente rentabilité - Entreprise très performante"
        elif marge_nette >= 5:
            return "Bonne rentabilité - Performance satisfaisante"
        elif marge_nette >= 0:
            return "Rentabilité faible - Possibilités d'amélioration"
        else:
            return "⚠️ Entreprise déficitaire - Actions correctives nécessaires"

    def _interpret_delais(self) -> str:
        """Interprète les délais de paiement."""
        delai_clients = float(self.get_delai_paiement_clients())
        delai_fournisseurs = float(self.get_delai_paiement_fournisseurs())

        if delai_clients < 45:
            return "Bonne gestion des encaissements clients"
        elif delai_clients < 60:
            return "Délais clients dans la moyenne"
        else:
            return "⚠️ Délais clients élevés - Risque sur la trésorerie"
