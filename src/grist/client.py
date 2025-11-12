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

    def create_kpi_table_if_not_exists(self, kpi_table_name: str = 'KPI') -> bool:
        """
        Crée la table des KPI si elle n'existe pas.

        Args:
            kpi_table_name: Nom de la table KPI

        Returns:
            True si la table a été créée ou existe déjà
        """
        # Vérifier si la table existe
        tables_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        response = requests.get(tables_url, headers=self.headers)

        if response.status_code == 200:
            tables = response.json().get('tables', [])
            if any(t['id'] == kpi_table_name for t in tables):
                return True

        # Créer la table KPI
        columns = [
            {'id': 'DateCalcul', 'fields': {'type': 'DateTime', 'label': 'Date de calcul'}},
            {'id': 'PeriodeDebut', 'fields': {'type': 'Date', 'label': 'Période début'}},
            {'id': 'PeriodeFin', 'fields': {'type': 'Date', 'label': 'Période fin'}},
            {'id': 'ChiffreAffaires', 'fields': {'type': 'Numeric', 'label': 'Chiffre d\'affaires'}},
            {'id': 'Charges', 'fields': {'type': 'Numeric', 'label': 'Charges'}},
            {'id': 'ResultatNet', 'fields': {'type': 'Numeric', 'label': 'Résultat net'}},
            {'id': 'MargeBrute', 'fields': {'type': 'Numeric', 'label': 'Marge brute'}},
            {'id': 'Tresorerie', 'fields': {'type': 'Numeric', 'label': 'Trésorerie'}},
            {'id': 'CreancesClients', 'fields': {'type': 'Numeric', 'label': 'Créances clients'}},
            {'id': 'DettesFournisseurs', 'fields': {'type': 'Numeric', 'label': 'Dettes fournisseurs'}},
            {'id': 'FondsRoulement', 'fields': {'type': 'Numeric', 'label': 'Fonds de roulement'}},
            {'id': 'BFR', 'fields': {'type': 'Numeric', 'label': 'BFR'}},
            {'id': 'TauxMargeBrute', 'fields': {'type': 'Numeric', 'label': 'Taux marge brute (%)'}},
            {'id': 'TauxMargeNette', 'fields': {'type': 'Numeric', 'label': 'Taux marge nette (%)'}},
            {'id': 'ROE', 'fields': {'type': 'Numeric', 'label': 'ROE (%)'}},
            {'id': 'ROA', 'fields': {'type': 'Numeric', 'label': 'ROA (%)'}},
            {'id': 'RatioLiquidite', 'fields': {'type': 'Numeric', 'label': 'Ratio liquidité'}},
            {'id': 'AutonomieFinanciere', 'fields': {'type': 'Numeric', 'label': 'Autonomie financière (%)'}},
            {'id': 'DelaiPaiementClients', 'fields': {'type': 'Numeric', 'label': 'Délai clients (jours)'}},
            {'id': 'DelaiPaiementFournisseurs', 'fields': {'type': 'Numeric', 'label': 'Délai fournisseurs (jours)'}},
        ]

        create_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        payload = {
            'tables': [{
                'id': kpi_table_name,
                'columns': columns
            }]
        }

        response = requests.post(create_url, json=payload, headers=self.headers)
        return response.status_code in [200, 201]

    def upload_kpi(self, kpi_data: Dict[str, Any], kpi_table_name: str = 'KPI') -> Dict[str, Any]:
        """
        Upload les KPI vers une table Grist.

        Args:
            kpi_data: Données KPI à uploader
            kpi_table_name: Nom de la table KPI

        Returns:
            Résultat de l'upload
        """
        # Créer la table si nécessaire
        self.create_kpi_table_if_not_exists(kpi_table_name)

        # Préparer les données KPI pour Grist
        kpi_record = {
            'DateCalcul': kpi_data.get('date_calcul', ''),
            'PeriodeDebut': kpi_data.get('periode', {}).get('debut', ''),
            'PeriodeFin': kpi_data.get('periode', {}).get('fin', ''),
            'ChiffreAffaires': kpi_data.get('financiers', {}).get('chiffre_affaires', 0),
            'Charges': kpi_data.get('financiers', {}).get('charges', 0),
            'ResultatNet': kpi_data.get('financiers', {}).get('resultat_net', 0),
            'MargeBrute': kpi_data.get('financiers', {}).get('marge_brute', 0),
            'Tresorerie': kpi_data.get('financiers', {}).get('tresorerie', 0),
            'CreancesClients': kpi_data.get('financiers', {}).get('creances_clients', 0),
            'DettesFournisseurs': kpi_data.get('financiers', {}).get('dettes_fournisseurs', 0),
            'FondsRoulement': kpi_data.get('financiers', {}).get('fonds_roulement', 0),
            'BFR': kpi_data.get('financiers', {}).get('bfr', 0),
            'TauxMargeBrute': kpi_data.get('ratios', {}).get('marge_brute_pct', 0),
            'TauxMargeNette': kpi_data.get('ratios', {}).get('marge_nette_pct', 0),
        }

        # Ajouter les KPI financiers détaillés si disponibles
        if 'kpi_financiers' in kpi_data:
            fin_kpi = kpi_data['kpi_financiers']
            kpi_record['ROE'] = fin_kpi.get('rentabilite', {}).get('roe_pct', 0)
            kpi_record['ROA'] = fin_kpi.get('rentabilite', {}).get('roa_pct', 0)
            kpi_record['RatioLiquidite'] = fin_kpi.get('liquidite', {}).get('ratio_general', 0)
            kpi_record['AutonomieFinanciere'] = fin_kpi.get('solvabilite', {}).get('autonomie_financiere_pct', 0)
            kpi_record['DelaiPaiementClients'] = fin_kpi.get('delais', {}).get('delai_paiement_clients_jours', 0)
            kpi_record['DelaiPaiementFournisseurs'] = fin_kpi.get('delais', {}).get('delai_paiement_fournisseurs_jours', 0)

        # Upload vers Grist
        url = f"{self.server_url}/api/docs/{self.doc_id}/tables/{kpi_table_name}/records"
        payload = {'records': [{'fields': kpi_record}]}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_kpi_history(self, kpi_table_name: str = 'KPI', limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des KPI.

        Args:
            kpi_table_name: Nom de la table KPI
            limit: Nombre maximum d'enregistrements

        Returns:
            Liste des KPI historiques
        """
        url = f"{self.server_url}/api/docs/{self.doc_id}/tables/{kpi_table_name}/records"
        params = {}

        if limit:
            params['limit'] = limit

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json().get('records', [])

    def create_entities_table_if_not_exists(self, table_name: str = 'Entites') -> bool:
        """
        Crée la table des entités si elle n'existe pas.

        Args:
            table_name: Nom de la table

        Returns:
            True si la table a été créée ou existe déjà
        """
        # Vérifier si la table existe
        tables_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        response = requests.get(tables_url, headers=self.headers)

        if response.status_code == 200:
            tables = response.json().get('tables', [])
            if any(t['id'] == table_name for t in tables):
                return True

        # Créer la table
        columns = [
            {'id': 'Code', 'fields': {'type': 'Text', 'label': 'Code'}},
            {'id': 'Nom', 'fields': {'type': 'Text', 'label': 'Nom'}},
            {'id': 'Type', 'fields': {'type': 'Text', 'label': 'Type'}},
            {'id': 'SIREN', 'fields': {'type': 'Text', 'label': 'SIREN'}},
            {'id': 'ExerciceDebut', 'fields': {'type': 'Date', 'label': 'Début exercice'}},
            {'id': 'ExerciceFin', 'fields': {'type': 'Date', 'label': 'Fin exercice'}},
            {'id': 'ParentCode', 'fields': {'type': 'Text', 'label': 'Code société mère'}},
            {'id': 'DetentionPct', 'fields': {'type': 'Numeric', 'label': '% Détention'}},
            {'id': 'CompteICPrefix', 'fields': {'type': 'Text', 'label': 'Préfixe compte IC'}},
            {'id': 'Active', 'fields': {'type': 'Bool', 'label': 'Active'}},
        ]

        create_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        payload = {
            'tables': [{
                'id': table_name,
                'columns': columns
            }]
        }

        response = requests.post(create_url, json=payload, headers=self.headers)
        return response.status_code in [200, 201]

    def upload_entities(self, entities_data: List[Dict[str, Any]],
                       table_name: str = 'Entites') -> Dict[str, Any]:
        """
        Upload les entités vers Grist.

        Args:
            entities_data: Liste des entités
            table_name: Nom de la table

        Returns:
            Résultat de l'upload
        """
        self.create_entities_table_if_not_exists(table_name)

        records = []
        for entity in entities_data:
            records.append({
                'Code': entity.get('code', ''),
                'Nom': entity.get('name', ''),
                'Type': entity.get('type', ''),
                'SIREN': entity.get('siren', ''),
                'ExerciceDebut': entity.get('exercice_start', ''),
                'ExerciceFin': entity.get('exercice_end', ''),
                'ParentCode': entity.get('parent_code', ''),
                'DetentionPct': entity.get('ownership_pct', 100),
                'CompteICPrefix': entity.get('intercompany_prefix', '451'),
                'Active': entity.get('active', True)
            })

        url = f"{self.server_url}/api/docs/{self.doc_id}/tables/{table_name}/records"
        payload = {'records': [{'fields': record} for record in records]}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def create_consolidation_table_if_not_exists(self, table_name: str = 'Consolidation') -> bool:
        """
        Crée la table de consolidation si elle n'existe pas.

        Args:
            table_name: Nom de la table

        Returns:
            True si la table a été créée ou existe déjà
        """
        # Vérifier si la table existe
        tables_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        response = requests.get(tables_url, headers=self.headers)

        if response.status_code == 200:
            tables = response.json().get('tables', [])
            if any(t['id'] == table_name for t in tables):
                return True

        # Créer la table
        columns = [
            {'id': 'DateCalcul', 'fields': {'type': 'DateTime', 'label': 'Date calcul'}},
            {'id': 'PeriodeDebut', 'fields': {'type': 'Date', 'label': 'Période début'}},
            {'id': 'PeriodeFin', 'fields': {'type': 'Date', 'label': 'Période fin'}},
            {'id': 'NombreEntites', 'fields': {'type': 'Int', 'label': 'Nombre entités'}},
            {'id': 'CAConsolide', 'fields': {'type': 'Numeric', 'label': 'CA consolidé'}},
            {'id': 'ChargesConsolidees', 'fields': {'type': 'Numeric', 'label': 'Charges consolidées'}},
            {'id': 'ResultatConsolide', 'fields': {'type': 'Numeric', 'label': 'Résultat consolidé'}},
            {'id': 'MargeConsolidee', 'fields': {'type': 'Numeric', 'label': 'Marge consolidée (%)'}},
            {'id': 'TresorerieGroupe', 'fields': {'type': 'Numeric', 'label': 'Trésorerie groupe'}},
            {'id': 'FluxIC', 'fields': {'type': 'Int', 'label': 'Flux inter-compagnies'}},
            {'id': 'FluxICRappro', 'fields': {'type': 'Int', 'label': 'Flux IC rapprochés'}},
            {'id': 'TauxRappro', 'fields': {'type': 'Numeric', 'label': 'Taux rapprochement (%)'}},
            {'id': 'SoldesIC', 'fields': {'type': 'Numeric', 'label': 'Soldes IC nets'}},
        ]

        create_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        payload = {
            'tables': [{
                'id': table_name,
                'columns': columns
            }]
        }

        response = requests.post(create_url, json=payload, headers=self.headers)
        return response.status_code in [200, 201]

    def upload_consolidation(self, consolidation_data: Dict[str, Any],
                            table_name: str = 'Consolidation') -> Dict[str, Any]:
        """
        Upload les données de consolidation vers Grist.

        Args:
            consolidation_data: Données de consolidation
            table_name: Nom de la table

        Returns:
            Résultat de l'upload
        """
        from datetime import datetime

        self.create_consolidation_table_if_not_exists(table_name)

        cons = consolidation_data.get('consolidated', {})
        ic = consolidation_data.get('intercompany', {})
        period = consolidation_data.get('period', {})

        record = {
            'DateCalcul': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'PeriodeDebut': period.get('start', ''),
            'PeriodeFin': period.get('end', ''),
            'NombreEntites': len(consolidation_data.get('by_entity', {})),
            'CAConsolide': cons.get('ca', 0),
            'ChargesConsolidees': cons.get('charges', 0),
            'ResultatConsolide': cons.get('resultat', 0),
            'MargeConsolidee': cons.get('marge_pct', 0),
            'TresorerieGroupe': cons.get('tresorerie', 0),
            'FluxIC': ic.get('total_flows', 0),
            'FluxICRappro': ic.get('reconciled', 0),
            'TauxRappro': ic.get('reconciliation_rate', 0),
            'SoldesIC': ic.get('total_ic_balances', 0),
        }

        url = f"{self.server_url}/api/docs/{self.doc_id}/tables/{table_name}/records"
        payload = {'records': [{'fields': record}]}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def create_intercompany_table_if_not_exists(self, table_name: str = 'FluxInterCompagnies') -> bool:
        """
        Crée la table des flux inter-compagnies si elle n'existe pas.

        Args:
            table_name: Nom de la table

        Returns:
            True si la table a été créée ou existe déjà
        """
        # Vérifier si la table existe
        tables_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        response = requests.get(tables_url, headers=self.headers)

        if response.status_code == 200:
            tables = response.json().get('tables', [])
            if any(t['id'] == table_name for t in tables):
                return True

        # Créer la table
        columns = [
            {'id': 'Entite1', 'fields': {'type': 'Text', 'label': 'Entité 1'}},
            {'id': 'Entite2', 'fields': {'type': 'Text', 'label': 'Entité 2'}},
            {'id': 'SoldeE1versE2', 'fields': {'type': 'Numeric', 'label': 'Solde E1→E2'}},
            {'id': 'SoldeE2versE1', 'fields': {'type': 'Numeric', 'label': 'Solde E2→E1'}},
            {'id': 'SoldeNet', 'fields': {'type': 'Numeric', 'label': 'Solde net'}},
            {'id': 'QuiDoit', 'fields': {'type': 'Text', 'label': 'Qui doit'}},
            {'id': 'DateCalcul', 'fields': {'type': 'DateTime', 'label': 'Date calcul'}},
        ]

        create_url = f"{self.server_url}/api/docs/{self.doc_id}/tables"
        payload = {
            'tables': [{
                'id': table_name,
                'columns': columns
            }]
        }

        response = requests.post(create_url, json=payload, headers=self.headers)
        return response.status_code in [200, 201]

    def upload_intercompany_balances(self, balances: List[Dict[str, Any]],
                                    table_name: str = 'FluxInterCompagnies') -> Dict[str, Any]:
        """
        Upload les soldes inter-compagnies vers Grist.

        Args:
            balances: Liste des soldes inter-compagnies
            table_name: Nom de la table

        Returns:
            Résultat de l'upload
        """
        from datetime import datetime

        self.create_intercompany_table_if_not_exists(table_name)

        records = []
        for bal in balances:
            records.append({
                'Entite1': bal['entity1'],
                'Entite2': bal['entity2'],
                'SoldeE1versE2': bal['balance_e1_to_e2'],
                'SoldeE2versE1': bal['balance_e2_to_e1'],
                'SoldeNet': bal['net_balance'],
                'QuiDoit': bal['who_owes'],
                'DateCalcul': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        url = f"{self.server_url}/api/docs/{self.doc_id}/tables/{table_name}/records"
        payload = {'records': [{'fields': record} for record in records]}

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        return response.json()
