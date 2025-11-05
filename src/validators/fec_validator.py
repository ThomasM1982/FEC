"""Validateur pour les fichiers FEC."""
from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict

from ..models.accounting_entry import AccountingEntry


class FECValidator:
    """Validateur pour les fichiers FEC selon les normes françaises."""

    def __init__(self, entries: List[AccountingEntry]):
        """
        Initialise le validateur.

        Args:
            entries: Liste des écritures à valider
        """
        self.entries = entries
        self.errors = []
        self.warnings = []

    def validate_all(self) -> Dict[str, Any]:
        """
        Exécute toutes les validations.

        Returns:
            Dictionnaire contenant les résultats de validation
        """
        self.errors = []
        self.warnings = []

        self.validate_balance()
        self.validate_account_numbers()
        self.validate_dates()
        self.validate_journals()
        self.validate_entries_balance()

        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'total_entries': len(self.entries)
        }

    def validate_balance(self) -> bool:
        """
        Valide que le total débit = total crédit.

        Returns:
            True si équilibré
        """
        total_debit = sum(e.debit for e in self.entries)
        total_credit = sum(e.credit for e in self.entries)

        diff = abs(total_debit - total_credit)

        if diff > Decimal('0.01'):
            self.errors.append({
                'type': 'BALANCE_ERROR',
                'message': f'Le fichier n\'est pas équilibré: Débit={total_debit}, Crédit={total_credit}, Différence={diff}'
            })
            return False

        return True

    def validate_account_numbers(self) -> bool:
        """
        Valide les numéros de compte (doivent être numériques et cohérents).

        Returns:
            True si valide
        """
        for i, entry in enumerate(self.entries):
            # Vérifier que le numéro de compte n'est pas vide
            if not entry.compte_num or entry.compte_num.strip() == '':
                self.errors.append({
                    'type': 'ACCOUNT_ERROR',
                    'line': i + 1,
                    'message': f'Numéro de compte vide à la ligne {i + 1}'
                })

            # Vérifier que le compte commence par un chiffre
            elif not entry.compte_num[0].isdigit():
                self.warnings.append({
                    'type': 'ACCOUNT_WARNING',
                    'line': i + 1,
                    'message': f'Le compte {entry.compte_num} ne commence pas par un chiffre'
                })

            # Vérifier la longueur du compte (généralement entre 3 et 10 caractères)
            if len(entry.compte_num) < 2 or len(entry.compte_num) > 20:
                self.warnings.append({
                    'type': 'ACCOUNT_WARNING',
                    'line': i + 1,
                    'message': f'Longueur inhabituelle pour le compte {entry.compte_num}'
                })

        return len([e for e in self.errors if e['type'] == 'ACCOUNT_ERROR']) == 0

    def validate_dates(self) -> bool:
        """
        Valide la cohérence des dates.

        Returns:
            True si valide
        """
        for i, entry in enumerate(self.entries):
            # La date d'écriture doit être <= date de validation
            if entry.ecriture_date > entry.valid_date:
                self.errors.append({
                    'type': 'DATE_ERROR',
                    'line': i + 1,
                    'message': f'Date d\'écriture ({entry.ecriture_date}) postérieure à la date de validation ({entry.valid_date})'
                })

            # La date de pièce doit être proche de la date d'écriture
            days_diff = abs((entry.piece_date - entry.ecriture_date).days)
            if days_diff > 365:
                self.warnings.append({
                    'type': 'DATE_WARNING',
                    'line': i + 1,
                    'message': f'Écart important entre date de pièce et date d\'écriture: {days_diff} jours'
                })

        return len([e for e in self.errors if e['type'] == 'DATE_ERROR']) == 0

    def validate_journals(self) -> bool:
        """
        Valide la cohérence des journaux.

        Returns:
            True si valide
        """
        # Vérifier que les codes journaux sont cohérents avec leurs libellés
        journal_mapping = {}
        for i, entry in enumerate(self.entries):
            if entry.journal_code in journal_mapping:
                if journal_mapping[entry.journal_code] != entry.journal_lib:
                    self.warnings.append({
                        'type': 'JOURNAL_WARNING',
                        'line': i + 1,
                        'message': f'Libellé incohérent pour le journal {entry.journal_code}'
                    })
            else:
                journal_mapping[entry.journal_code] = entry.journal_lib

        return True

    def validate_entries_balance(self) -> bool:
        """
        Valide que chaque écriture (numéro d'écriture) est équilibrée.

        Returns:
            True si valide
        """
        # Grouper par numéro d'écriture
        entries_by_num = defaultdict(list)
        for entry in self.entries:
            entries_by_num[entry.ecriture_num].append(entry)

        # Vérifier l'équilibre de chaque écriture
        for ecriture_num, entries in entries_by_num.items():
            total_debit = sum(e.debit for e in entries)
            total_credit = sum(e.credit for e in entries)

            diff = abs(total_debit - total_credit)

            if diff > Decimal('0.01'):
                self.errors.append({
                    'type': 'ENTRY_BALANCE_ERROR',
                    'ecriture_num': ecriture_num,
                    'message': f'L\'écriture {ecriture_num} n\'est pas équilibrée: Débit={total_debit}, Crédit={total_credit}'
                })

        return len([e for e in self.errors if e['type'] == 'ENTRY_BALANCE_ERROR']) == 0

    def get_duplicate_entries(self) -> List[Dict[str, Any]]:
        """
        Détecte les écritures potentiellement dupliquées.

        Returns:
            Liste des doublons potentiels
        """
        seen = {}
        duplicates = []

        for entry in self.entries:
            key = (
                entry.journal_code,
                entry.ecriture_num,
                entry.compte_num,
                str(entry.debit),
                str(entry.credit)
            )

            if key in seen:
                duplicates.append({
                    'original': seen[key],
                    'duplicate': entry.ecriture_num
                })
            else:
                seen[key] = entry.ecriture_num

        return duplicates

    def get_report(self) -> str:
        """
        Génère un rapport de validation.

        Returns:
            Rapport formaté en texte
        """
        results = self.validate_all()

        report = []
        report.append("=" * 60)
        report.append("RAPPORT DE VALIDATION FEC")
        report.append("=" * 60)
        report.append(f"\nNombre total d'écritures: {results['total_entries']}")
        report.append(f"Statut: {'✓ VALIDE' if results['is_valid'] else '✗ INVALIDE'}")

        if results['errors']:
            report.append(f"\n❌ ERREURS ({len(results['errors'])}):")
            for error in results['errors']:
                report.append(f"  - {error['message']}")

        if results['warnings']:
            report.append(f"\n⚠️  AVERTISSEMENTS ({len(results['warnings'])}):")
            for warning in results['warnings']:
                report.append(f"  - {warning['message']}")

        duplicates = self.get_duplicate_entries()
        if duplicates:
            report.append(f"\n🔍 DOUBLONS POTENTIELS ({len(duplicates)}):")
            for dup in duplicates[:10]:  # Limiter à 10
                report.append(f"  - Écriture {dup['original']} et {dup['duplicate']}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
