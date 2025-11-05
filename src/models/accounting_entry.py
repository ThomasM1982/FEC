"""Modèle de données pour une écriture comptable (format FEC)."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Journal(BaseModel):
    """Modèle pour un journal comptable."""
    code: str = Field(..., description="Code du journal (ex: VE, AC, BQ)")
    libelle: str = Field(..., description="Libellé du journal")


class AccountingEntry(BaseModel):
    """
    Modèle pour une écriture comptable selon le format FEC.

    Format FEC (Fichier des Écritures Comptables) selon l'article A47 A-1 du LPF.
    """

    # Champs obligatoires FEC
    journal_code: str = Field(..., description="Code journal (JournalCode)")
    journal_lib: str = Field(..., description="Libellé journal (JournalLib)")
    ecriture_num: str = Field(..., description="Numéro d'écriture (EcritureNum)")
    ecriture_date: date = Field(..., description="Date d'écriture (EcritureDate)")
    compte_num: str = Field(..., description="Numéro de compte (CompteNum)")
    compte_lib: str = Field(..., description="Libellé de compte (CompteLib)")
    comp_aux_num: Optional[str] = Field(None, description="Numéro de compte auxiliaire (CompAuxNum)")
    comp_aux_lib: Optional[str] = Field(None, description="Libellé de compte auxiliaire (CompAuxLib)")
    piece_ref: str = Field(..., description="Référence de la pièce (PieceRef)")
    piece_date: date = Field(..., description="Date de la pièce (PieceDate)")
    ecriture_lib: str = Field(..., description="Libellé de l'écriture (EcritureLib)")
    debit: Decimal = Field(default=Decimal("0"), description="Montant débit (Debit)")
    credit: Decimal = Field(default=Decimal("0"), description="Montant crédit (Credit)")
    ecriture_let: Optional[str] = Field(None, description="Lettrage de l'écriture (EcritureLet)")
    date_let: Optional[date] = Field(None, description="Date de lettrage (DateLet)")
    valid_date: date = Field(..., description="Date de validation (ValidDate)")
    montant_devise: Optional[Decimal] = Field(None, description="Montant en devise (Montantdevise)")
    idevise: Optional[str] = Field(None, description="Identifiant devise (Idevise)")

    @field_validator('debit', 'credit', 'montant_devise', mode='before')
    @classmethod
    def parse_decimal(cls, v):
        """Convertit les valeurs en Decimal."""
        if v is None or v == '':
            return Decimal("0")
        if isinstance(v, str):
            # Remplace la virgule par un point pour les décimaux français
            v = v.replace(',', '.').replace(' ', '')
        return Decimal(str(v))

    @field_validator('ecriture_date', 'piece_date', 'valid_date', 'date_let', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse les dates au format FEC (YYYYMMDD)."""
        if v is None or v == '':
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            # Format FEC: YYYYMMDD
            if len(v) == 8:
                return datetime.strptime(v, '%Y%m%d').date()
            # Autres formats possibles
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        raise ValueError(f"Format de date non reconnu: {v}")

    def is_balanced(self) -> bool:
        """Vérifie que l'écriture est équilibrée (débit = crédit au niveau du mouvement)."""
        return self.debit == self.credit if self.debit > 0 or self.credit > 0 else True

    def get_amount(self) -> Decimal:
        """Retourne le montant de l'écriture (débit ou crédit)."""
        return self.debit if self.debit > 0 else self.credit

    def get_sense(self) -> str:
        """Retourne le sens de l'écriture (D pour débit, C pour crédit)."""
        return "D" if self.debit > 0 else "C"

    def to_grist_dict(self) -> dict:
        """Convertit l'écriture en dictionnaire pour Grist."""
        return {
            'JournalCode': self.journal_code,
            'JournalLib': self.journal_lib,
            'EcritureNum': self.ecriture_num,
            'EcritureDate': self.ecriture_date.strftime('%Y-%m-%d'),
            'CompteNum': self.compte_num,
            'CompteLib': self.compte_lib,
            'CompAuxNum': self.comp_aux_num or '',
            'CompAuxLib': self.comp_aux_lib or '',
            'PieceRef': self.piece_ref,
            'PieceDate': self.piece_date.strftime('%Y-%m-%d'),
            'EcritureLib': self.ecriture_lib,
            'Debit': float(self.debit),
            'Credit': float(self.credit),
            'EcritureLet': self.ecriture_let or '',
            'DateLet': self.date_let.strftime('%Y-%m-%d') if self.date_let else '',
            'ValidDate': self.valid_date.strftime('%Y-%m-%d'),
            'Montantdevise': float(self.montant_devise) if self.montant_devise else 0,
            'Idevise': self.idevise or '',
        }

    class Config:
        """Configuration Pydantic."""
        json_encoders = {
            date: lambda v: v.strftime('%Y-%m-%d'),
            Decimal: lambda v: float(v)
        }
