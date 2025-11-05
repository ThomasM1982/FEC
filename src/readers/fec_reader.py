"""Lecteur de fichiers FEC (Fichier des Écritures Comptables)."""
import csv
from pathlib import Path
from typing import List, Optional
import pandas as pd

from ..models.accounting_entry import AccountingEntry


class FECReader:
    """
    Lecteur de fichiers FEC.

    Supporte les formats:
    - TXT (délimité par tabulation ou pipe |)
    - CSV (délimité par virgule, point-virgule, ou tabulation)
    - Excel (XLSX)
    """

    # Mapping des noms de colonnes FEC standards
    COLUMN_MAPPING = {
        'JournalCode': 'journal_code',
        'JournalLib': 'journal_lib',
        'EcritureNum': 'ecriture_num',
        'EcritureDate': 'ecriture_date',
        'CompteNum': 'compte_num',
        'CompteLib': 'compte_lib',
        'CompAuxNum': 'comp_aux_num',
        'CompAuxLib': 'comp_aux_lib',
        'PieceRef': 'piece_ref',
        'PieceDate': 'piece_date',
        'EcritureLib': 'ecriture_lib',
        'Debit': 'debit',
        'Credit': 'credit',
        'EcritureLet': 'ecriture_let',
        'DateLet': 'date_let',
        'ValidDate': 'valid_date',
        'Montantdevise': 'montant_devise',
        'Idevise': 'idevise',
    }

    def __init__(self, file_path: str, encoding: str = 'utf-8'):
        """
        Initialise le lecteur FEC.

        Args:
            file_path: Chemin vers le fichier FEC
            encoding: Encodage du fichier (défaut: utf-8, peut être latin1 ou cp1252)
        """
        self.file_path = Path(file_path)
        self.encoding = encoding

        if not self.file_path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")

    def _detect_delimiter(self) -> str:
        """Détecte le délimiteur du fichier."""
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            first_line = f.readline()

            # Compter les occurrences de différents délimiteurs
            delimiters = {
                '\t': first_line.count('\t'),
                '|': first_line.count('|'),
                ';': first_line.count(';'),
                ',': first_line.count(',')
            }

            # Retourner le délimiteur le plus fréquent
            return max(delimiters, key=delimiters.get)

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalise les noms de colonnes."""
        # Supprimer les espaces et les BOM
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')

        # Renommer selon le mapping
        df = df.rename(columns=self.COLUMN_MAPPING)

        return df

    def read(self) -> List[AccountingEntry]:
        """
        Lit le fichier FEC et retourne une liste d'écritures comptables.

        Returns:
            Liste des écritures comptables

        Raises:
            ValueError: Si le format du fichier n'est pas reconnu
        """
        file_ext = self.file_path.suffix.lower()

        try:
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(self.file_path)
            elif file_ext in ['.txt', '.csv']:
                delimiter = self._detect_delimiter()
                df = pd.read_csv(
                    self.file_path,
                    delimiter=delimiter,
                    encoding=self.encoding,
                    dtype=str  # Tout lire en string d'abord
                )
            else:
                raise ValueError(f"Format de fichier non supporté: {file_ext}")

            # Normaliser les colonnes
            df = self._normalize_column_names(df)

            # Convertir en liste d'écritures
            entries = []
            for _, row in df.iterrows():
                try:
                    entry_dict = row.to_dict()
                    # Remplacer NaN par None
                    entry_dict = {k: (None if pd.isna(v) else v) for k, v in entry_dict.items()}
                    entry = AccountingEntry(**entry_dict)
                    entries.append(entry)
                except Exception as e:
                    print(f"Erreur lors du parsing de la ligne: {e}")
                    print(f"Données: {row.to_dict()}")

            return entries

        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier: {e}")

    def read_with_filter(
        self,
        journal_code: Optional[str] = None,
        compte_num: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[AccountingEntry]:
        """
        Lit le fichier avec des filtres.

        Args:
            journal_code: Code journal à filtrer
            compte_num: Numéro de compte à filtrer
            date_from: Date de début (format YYYY-MM-DD)
            date_to: Date de fin (format YYYY-MM-DD)

        Returns:
            Liste filtrée des écritures comptables
        """
        entries = self.read()

        # Appliquer les filtres
        if journal_code:
            entries = [e for e in entries if e.journal_code == journal_code]

        if compte_num:
            entries = [e for e in entries if e.compte_num.startswith(compte_num)]

        if date_from:
            date_from_obj = pd.to_datetime(date_from).date()
            entries = [e for e in entries if e.ecriture_date >= date_from_obj]

        if date_to:
            date_to_obj = pd.to_datetime(date_to).date()
            entries = [e for e in entries if e.ecriture_date <= date_to_obj]

        return entries

    def get_statistics(self) -> dict:
        """
        Retourne des statistiques sur le fichier FEC.

        Returns:
            Dictionnaire de statistiques
        """
        entries = self.read()

        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)

        journals = {}
        for entry in entries:
            if entry.journal_code not in journals:
                journals[entry.journal_code] = {
                    'code': entry.journal_code,
                    'libelle': entry.journal_lib,
                    'count': 0,
                    'debit': 0,
                    'credit': 0
                }
            journals[entry.journal_code]['count'] += 1
            journals[entry.journal_code]['debit'] += float(entry.debit)
            journals[entry.journal_code]['credit'] += float(entry.credit)

        return {
            'total_entries': len(entries),
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
            'is_balanced': abs(total_debit - total_credit) < 0.01,
            'journals': list(journals.values()),
            'date_range': {
                'min': min(e.ecriture_date for e in entries).strftime('%Y-%m-%d'),
                'max': max(e.ecriture_date for e in entries).strftime('%Y-%m-%d')
            }
        }
