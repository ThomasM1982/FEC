"""Client pour interagir avec l'API Grist."""
import os
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

from ..models.accounting_entry import AccountingEntry


class GristClient:
    """Client pour interagir avec l'API Grist."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        doc_id: Optional[str] = None,
        table_name: Optional[str] = None
    ):
        """
        Initialise le client Grist.

        Args:
            api_key: Clé API Grist (ou via variable d'environnement GRIST_API_KEY)
            server_url: URL du serveur Grist (ou via GRIST_SERVER_URL)
            doc_id: ID du document Grist (ou via GRIST_DOC_ID)
            table_name: Nom de la table (ou via TABLE_NAME, défaut: EcrituresComptables)
        """
        load_dotenv()

        self.api_key = api_key or os.getenv('GRIST_API_KEY')
        self.server_url = (server_url or os.getenv('GRIST_SERVER_URL', 'https://docs.getgrist.com')).rstrip('/')
        self.doc_id = doc_id or os.getenv('GRIST_DOC_ID')
        self.table_name = table_name or os.getenv('TABLE_NAME', 'EcrituresComptables')

        if not self.api_key:
            raise ValueError("GRIST_API_KEY doit être défini")
        if not self.doc_id:
            raise ValueError("GRIST_DOC_ID doit être défini")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        self.base_url = f"{self.server_url}/api/docs/{self.doc_id}/tables/{self.table_name}"

    def create_table_if_not_exists(self) -> bool:
        """
        Crée la table des écritures comptables si elle n'existe pas.

        Returns:
            True si la table a été créée ou existe déjà
        """
        # Vérifier si la table existe
        tables_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        response = requests.get(tables_url, headers=self.headers)

        if response.status_code == 200:
            tables = response.json().get('tables', [])
            if any(t['id'] == self.table_name for t in tables):
                return True

        # Créer la table avec les colonnes FEC
        columns = [
            {'id': 'JournalCode', 'fields': {'type': 'Text', 'label': 'Code Journal'}},
            {'id': 'JournalLib', 'fields': {'type': 'Text', 'label': 'Libellé Journal'}},
            {'id': 'EcritureNum', 'fields': {'type': 'Text', 'label': 'N° Écriture'}},
            {'id': 'EcritureDate', 'fields': {'type': 'Date', 'label': 'Date Écriture'}},
            {'id': 'CompteNum', 'fields': {'type': 'Text', 'label': 'N° Compte'}},
            {'id': 'CompteLib', 'fields': {'type': 'Text', 'label': 'Libellé Compte'}},
            {'id': 'CompAuxNum', 'fields': {'type': 'Text', 'label': 'N° Compte Aux'}},
            {'id': 'CompAuxLib', 'fields': {'type': 'Text', 'label': 'Libellé Compte Aux'}},
            {'id': 'PieceRef', 'fields': {'type': 'Text', 'label': 'Référence Pièce'}},
            {'id': 'PieceDate', 'fields': {'type': 'Date', 'label': 'Date Pièce'}},
            {'id': 'EcritureLib', 'fields': {'type': 'Text', 'label': 'Libellé Écriture'}},
            {'id': 'Debit', 'fields': {'type': 'Numeric', 'label': 'Débit'}},
            {'id': 'Credit', 'fields': {'type': 'Numeric', 'label': 'Crédit'}},
            {'id': 'EcritureLet', 'fields': {'type': 'Text', 'label': 'Lettrage'}},
            {'id': 'DateLet', 'fields': {'type': 'Date', 'label': 'Date Lettrage'}},
            {'id': 'ValidDate', 'fields': {'type': 'Date', 'label': 'Date Validation'}},
            {'id': 'Montantdevise', 'fields': {'type': 'Numeric', 'label': 'Montant Devise'}},
            {'id': 'Idevise', 'fields': {'type': 'Text', 'label': 'Code Devise'}},
        ]

        create_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        payload = {
            'tables': [{
                'id': self.table_name,
                'columns': columns
            }]
        }

        response = requests.post(create_url, json=payload, headers=self.headers)
        return response.status_code in [200, 201]

    def add_records(self, entries: List[AccountingEntry]) -> Dict[str, Any]:
        """
        Ajoute des enregistrements à la table Grist.

        Args:
            entries: Liste des écritures comptables à ajouter

        Returns:
            Réponse de l'API Grist
        """
        records = [entry.to_grist_dict() for entry in entries]

        url = f"{self.base_url}/records"
        payload = {'records': [{'fields': record} for record in records]}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_records(
        self,
        filter_formula: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère des enregistrements de la table Grist.

        Args:
            filter_formula: Formule de filtrage Grist (optionnel)
            limit: Nombre maximum d'enregistrements à retourner

        Returns:
            Liste des enregistrements
        """
        url = f"{self.base_url}/records"
        params = {}

        if filter_formula:
            params['filter'] = filter_formula
        if limit:
            params['limit'] = limit

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json().get('records', [])

    def update_record(self, record_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un enregistrement.

        Args:
            record_id: ID de l'enregistrement
            fields: Champs à mettre à jour

        Returns:
            Réponse de l'API Grist
        """
        url = f"{self.base_url}/records"
        payload = {'records': [{'id': record_id, 'fields': fields}]}

        response = requests.patch(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def delete_records(self, record_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des enregistrements.

        Args:
            record_ids: Liste des IDs d'enregistrements à supprimer

        Returns:
            Réponse de l'API Grist
        """
        url = f"{self.base_url}/records"
        payload = {'records': record_ids}

        response = requests.delete(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def upload_entries(
        self,
        entries: List[AccountingEntry],
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Upload des écritures comptables par lots.

        Args:
            entries: Liste des écritures à uploader
            batch_size: Taille des lots (défaut: 500)

        Returns:
            Statistiques de l'upload
        """
        total = len(entries)
        uploaded = 0
        errors = []

        # Créer la table si nécessaire
        self.create_table_if_not_exists()

        # Upload par lots
        for i in range(0, total, batch_size):
            batch = entries[i:i + batch_size]
            try:
                result = self.add_records(batch)
                uploaded += len(batch)
                print(f"Uploaded {uploaded}/{total} écritures...")
            except Exception as e:
                errors.append({'batch': i, 'error': str(e)})
                print(f"Erreur lors de l'upload du lot {i}: {e}")

        return {
            'total': total,
            'uploaded': uploaded,
            'errors': errors,
            'success': len(errors) == 0
        }

    def get_balance_by_account(self) -> List[Dict[str, Any]]:
        """
        Récupère les soldes par compte.

        Returns:
            Liste des soldes par compte
        """
        records = self.get_records()

        balances = {}
        for record in records:
            fields = record.get('fields', {})
            compte = fields.get('CompteNum')
            debit = float(fields.get('Debit', 0))
            credit = float(fields.get('Credit', 0))

            if compte not in balances:
                balances[compte] = {
                    'compte': compte,
                    'libelle': fields.get('CompteLib', ''),
                    'debit': 0,
                    'credit': 0,
                    'solde': 0
                }

            balances[compte]['debit'] += debit
            balances[compte]['credit'] += credit
            balances[compte]['solde'] = balances[compte]['debit'] - balances[compte]['credit']

        return list(balances.values())
