"""Tests pour le modèle AccountingEntry."""
import unittest
from datetime import date
from decimal import Decimal

from src.models.accounting_entry import AccountingEntry


class TestAccountingEntry(unittest.TestCase):
    """Tests pour AccountingEntry."""

    def test_create_entry(self):
        """Test de création d'une écriture."""
        entry = AccountingEntry(
            journal_code="VE",
            journal_lib="Ventes",
            ecriture_num="VE001",
            ecriture_date=date(2024, 1, 1),
            compte_num="411000",
            compte_lib="Clients",
            piece_ref="FAC001",
            piece_date=date(2024, 1, 1),
            ecriture_lib="Vente",
            debit=Decimal("1000.00"),
            credit=Decimal("0"),
            valid_date=date(2024, 1, 1)
        )

        self.assertEqual(entry.journal_code, "VE")
        self.assertEqual(entry.debit, Decimal("1000.00"))
        self.assertEqual(entry.credit, Decimal("0"))

    def test_get_amount(self):
        """Test de la méthode get_amount."""
        entry_debit = AccountingEntry(
            journal_code="VE",
            journal_lib="Ventes",
            ecriture_num="VE001",
            ecriture_date=date(2024, 1, 1),
            compte_num="411000",
            compte_lib="Clients",
            piece_ref="FAC001",
            piece_date=date(2024, 1, 1),
            ecriture_lib="Vente",
            debit=Decimal("1000.00"),
            credit=Decimal("0"),
            valid_date=date(2024, 1, 1)
        )

        entry_credit = AccountingEntry(
            journal_code="VE",
            journal_lib="Ventes",
            ecriture_num="VE001",
            ecriture_date=date(2024, 1, 1),
            compte_num="707000",
            compte_lib="Ventes",
            piece_ref="FAC001",
            piece_date=date(2024, 1, 1),
            ecriture_lib="Vente",
            debit=Decimal("0"),
            credit=Decimal("1000.00"),
            valid_date=date(2024, 1, 1)
        )

        self.assertEqual(entry_debit.get_amount(), Decimal("1000.00"))
        self.assertEqual(entry_credit.get_amount(), Decimal("1000.00"))

    def test_get_sense(self):
        """Test de la méthode get_sense."""
        entry_debit = AccountingEntry(
            journal_code="VE",
            journal_lib="Ventes",
            ecriture_num="VE001",
            ecriture_date=date(2024, 1, 1),
            compte_num="411000",
            compte_lib="Clients",
            piece_ref="FAC001",
            piece_date=date(2024, 1, 1),
            ecriture_lib="Vente",
            debit=Decimal("1000.00"),
            credit=Decimal("0"),
            valid_date=date(2024, 1, 1)
        )

        entry_credit = AccountingEntry(
            journal_code="VE",
            journal_lib="Ventes",
            ecriture_num="VE001",
            ecriture_date=date(2024, 1, 1),
            compte_num="707000",
            compte_lib="Ventes",
            piece_ref="FAC001",
            piece_date=date(2024, 1, 1),
            ecriture_lib="Vente",
            debit=Decimal("0"),
            credit=Decimal("1000.00"),
            valid_date=date(2024, 1, 1)
        )

        self.assertEqual(entry_debit.get_sense(), "D")
        self.assertEqual(entry_credit.get_sense(), "C")

    def test_to_grist_dict(self):
        """Test de conversion en dictionnaire Grist."""
        entry = AccountingEntry(
            journal_code="VE",
            journal_lib="Ventes",
            ecriture_num="VE001",
            ecriture_date=date(2024, 1, 1),
            compte_num="411000",
            compte_lib="Clients",
            piece_ref="FAC001",
            piece_date=date(2024, 1, 1),
            ecriture_lib="Vente",
            debit=Decimal("1000.00"),
            credit=Decimal("0"),
            valid_date=date(2024, 1, 1)
        )

        grist_dict = entry.to_grist_dict()

        self.assertEqual(grist_dict['JournalCode'], 'VE')
        self.assertEqual(grist_dict['EcritureDate'], '2024-01-01')
        self.assertEqual(grist_dict['Debit'], 1000.00)
        self.assertEqual(grist_dict['Credit'], 0.0)


if __name__ == '__main__':
    unittest.main()
