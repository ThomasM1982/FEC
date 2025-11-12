"""Analyseur de flux inter-compagnies."""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from collections import defaultdict
from datetime import date

from ..models.accounting_entry import AccountingEntry
from .entity import Entity, EntityManager


class IntercompanyFlow:
    """Représente un flux inter-compagnies."""

    def __init__(self, entity_from: str, entity_to: str,
                 account_from: str, account_to: str,
                 amount: Decimal, date: date, reference: str):
        """
        Initialise un flux inter-compagnies.

        Args:
            entity_from: Code entité émettrice
            entity_to: Code entité réceptrice
            account_from: Compte dans l'entité émettrice
            account_to: Compte dans l'entité réceptrice
            amount: Montant du flux
            date: Date du flux
            reference: Référence de la transaction
        """
        self.entity_from = entity_from
        self.entity_to = entity_to
        self.account_from = account_from
        self.account_to = account_to
        self.amount = amount
        self.date = date
        self.reference = reference
        self.reconciled = False
        self.difference = Decimal('0')


class IntercompanyAnalyzer:
    """
    Analyse les flux inter-compagnies entre entités.

    Identifie les transactions entre entités du groupe et vérifie
    leur cohérence (réciprocité).
    """

    def __init__(self, entity_manager: EntityManager):
        """
        Initialise l'analyseur inter-compagnies.

        Args:
            entity_manager: Gestionnaire d'entités
        """
        self.entity_manager = entity_manager
        self.entries_by_entity: Dict[str, List[AccountingEntry]] = {}
        self.flows: List[IntercompanyFlow] = []

    def load_entries(self, entity_code: str, entries: List[AccountingEntry]) -> None:
        """
        Charge les écritures d'une entité.

        Args:
            entity_code: Code de l'entité
            entries: Liste des écritures comptables
        """
        self.entries_by_entity[entity_code] = entries

    def identify_intercompany_accounts(self, entries: List[AccountingEntry],
                                      entity: Entity) -> List[AccountingEntry]:
        """
        Identifie les écritures sur comptes inter-compagnies.

        Args:
            entries: Liste des écritures
            entity: Entité concernée

        Returns:
            Liste des écritures inter-compagnies
        """
        ic_entries = []
        prefix = entity.intercompany_account_prefix

        for entry in entries:
            # Vérifier si le compte commence par le préfixe inter-compagnies (ex: 451)
            if entry.compte_num.startswith(prefix):
                ic_entries.append(entry)

            # Vérifier aussi les comptes auxiliaires pour identifier l'entité partenaire
            if entry.comp_aux_num and entry.comp_aux_num.startswith(prefix):
                ic_entries.append(entry)

        return ic_entries

    def extract_partner_entity(self, entry: AccountingEntry) -> Optional[str]:
        """
        Extrait le code de l'entité partenaire depuis une écriture.

        Utilise le compte auxiliaire ou le libellé pour identifier l'entité.

        Args:
            entry: Écriture comptable

        Returns:
            Code de l'entité partenaire ou None
        """
        # Chercher dans le compte auxiliaire
        if entry.comp_aux_num:
            # Exemple: 451001 -> entité "001"
            aux_num = entry.comp_aux_num
            for entity in self.entity_manager.get_all_entities():
                if entity.code in aux_num or aux_num.endswith(entity.code):
                    return entity.code

        # Chercher dans le libellé
        if entry.comp_aux_lib:
            lib = entry.comp_aux_lib.upper()
            for entity in self.entity_manager.get_all_entities():
                if entity.code.upper() in lib or entity.name.upper() in lib:
                    return entity.code

        # Chercher dans le libellé d'écriture
        if entry.ecriture_lib:
            lib = entry.ecriture_lib.upper()
            for entity in self.entity_manager.get_all_entities():
                if entity.code.upper() in lib or entity.name.upper() in lib:
                    return entity.code

        return None

    def analyze_all_flows(self) -> List[IntercompanyFlow]:
        """
        Analyse tous les flux inter-compagnies entre entités.

        Returns:
            Liste des flux identifiés
        """
        self.flows = []

        # Pour chaque entité
        for entity_code, entries in self.entries_by_entity.items():
            entity = self.entity_manager.get_entity(entity_code)
            if not entity:
                continue

            # Identifier les écritures inter-compagnies
            ic_entries = self.identify_intercompany_accounts(entries, entity)

            # Analyser chaque écriture
            for entry in ic_entries:
                partner_code = self.extract_partner_entity(entry)
                if not partner_code or partner_code == entity_code:
                    continue

                # Créer un flux
                amount = entry.debit if entry.debit > 0 else -entry.credit

                flow = IntercompanyFlow(
                    entity_from=entity_code if amount > 0 else partner_code,
                    entity_to=partner_code if amount > 0 else entity_code,
                    account_from=entry.compte_num,
                    account_to='',  # Sera déterminé lors du rapprochement
                    amount=abs(amount),
                    date=entry.ecriture_date,
                    reference=entry.piece_ref
                )

                self.flows.append(flow)

        return self.flows

    def reconcile_flows(self) -> Dict[str, Any]:
        """
        Rapproche les flux inter-compagnies réciproques.

        Vérifie que chaque flux dans une entité a un flux inverse
        dans l'entité partenaire.

        Returns:
            Statistiques de rapprochement
        """
        # Grouper par paire d'entités et date
        flows_by_pair = defaultdict(list)

        for flow in self.flows:
            pair_key = tuple(sorted([flow.entity_from, flow.entity_to]))
            date_key = flow.date.strftime('%Y-%m')
            key = (pair_key, date_key)
            flows_by_pair[key].append(flow)

        reconciled = 0
        unreconciled = 0
        differences = []

        # Rapprocher les flux par paire
        for (pair, month), flows in flows_by_pair.items():
            entity1, entity2 = pair

            # Calculer le solde net
            balance_e1_to_e2 = Decimal('0')
            balance_e2_to_e1 = Decimal('0')

            for flow in flows:
                if flow.entity_from == entity1:
                    balance_e1_to_e2 += flow.amount
                else:
                    balance_e2_to_e1 += flow.amount

            difference = abs(balance_e1_to_e2 - balance_e2_to_e1)

            if difference < Decimal('0.01'):
                reconciled += len(flows)
                for flow in flows:
                    flow.reconciled = True
            else:
                unreconciled += len(flows)
                differences.append({
                    'entity1': entity1,
                    'entity2': entity2,
                    'month': month,
                    'balance_e1_to_e2': float(balance_e1_to_e2),
                    'balance_e2_to_e1': float(balance_e2_to_e1),
                    'difference': float(difference)
                })

        return {
            'total_flows': len(self.flows),
            'reconciled': reconciled,
            'unreconciled': unreconciled,
            'differences': differences,
            'reconciliation_rate': (reconciled / len(self.flows) * 100) if self.flows else 0
        }

    def get_intercompany_balances(self) -> List[Dict[str, Any]]:
        """
        Calcule les soldes inter-compagnies par paire d'entités.

        Returns:
            Liste des soldes inter-compagnies
        """
        balances = defaultdict(lambda: {
            'entity1': '',
            'entity2': '',
            'balance_e1_to_e2': Decimal('0'),
            'balance_e2_to_e1': Decimal('0'),
            'net_balance': Decimal('0'),
            'who_owes': ''
        })

        for flow in self.flows:
            pair_key = tuple(sorted([flow.entity_from, flow.entity_to]))
            entity1, entity2 = pair_key

            bal = balances[pair_key]
            bal['entity1'] = entity1
            bal['entity2'] = entity2

            if flow.entity_from == entity1:
                bal['balance_e1_to_e2'] += flow.amount
            else:
                bal['balance_e2_to_e1'] += flow.amount

        result = []
        for pair_key, bal in balances.items():
            net = bal['balance_e1_to_e2'] - bal['balance_e2_to_e1']
            bal['net_balance'] = abs(net)

            if net > 0:
                bal['who_owes'] = f"{bal['entity2']} doit {bal['net_balance']:.2f} € à {bal['entity1']}"
            elif net < 0:
                bal['who_owes'] = f"{bal['entity1']} doit {bal['net_balance']:.2f} € à {bal['entity2']}"
            else:
                bal['who_owes'] = "Équilibré"

            result.append({
                'entity1': bal['entity1'],
                'entity2': bal['entity2'],
                'balance_e1_to_e2': float(bal['balance_e1_to_e2']),
                'balance_e2_to_e1': float(bal['balance_e2_to_e1']),
                'net_balance': float(bal['net_balance']),
                'who_owes': bal['who_owes']
            })

        return sorted(result, key=lambda x: x['net_balance'], reverse=True)

    def get_flows_by_entity_pair(self, entity1: str, entity2: str) -> List[Dict[str, Any]]:
        """
        Récupère les flux entre deux entités.

        Args:
            entity1: Code première entité
            entity2: Code seconde entité

        Returns:
            Liste des flux
        """
        flows = []

        for flow in self.flows:
            if (flow.entity_from == entity1 and flow.entity_to == entity2) or \
               (flow.entity_from == entity2 and flow.entity_to == entity1):
                flows.append({
                    'from': flow.entity_from,
                    'to': flow.entity_to,
                    'amount': float(flow.amount),
                    'date': flow.date.strftime('%Y-%m-%d'),
                    'reference': flow.reference,
                    'reconciled': flow.reconciled
                })

        return sorted(flows, key=lambda x: x['date'])

    def get_unreconciled_flows(self) -> List[Dict[str, Any]]:
        """
        Récupère les flux non rapprochés.

        Returns:
            Liste des flux non rapprochés
        """
        unreconciled = []

        for flow in self.flows:
            if not flow.reconciled:
                unreconciled.append({
                    'from': flow.entity_from,
                    'to': flow.entity_to,
                    'amount': float(flow.amount),
                    'date': flow.date.strftime('%Y-%m-%d'),
                    'reference': flow.reference,
                    'account': flow.account_from
                })

        return sorted(unreconciled, key=lambda x: x['date'])

    def generate_report(self) -> str:
        """
        Génère un rapport d'analyse inter-compagnies.

        Returns:
            Rapport formaté
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT D'ANALYSE INTER-COMPAGNIES")
        lines.append("=" * 80)

        # Statistiques générales
        lines.append(f"\n📊 Statistiques générales:")
        lines.append(f"  Nombre de flux identifiés: {len(self.flows)}")

        if self.flows:
            # Rapprochement
            recon = self.reconcile_flows()
            lines.append(f"\n🔄 Rapprochement:")
            lines.append(f"  Flux rapprochés: {recon['reconciled']}")
            lines.append(f"  Flux non rapprochés: {recon['unreconciled']}")
            lines.append(f"  Taux de rapprochement: {recon['reconciliation_rate']:.1f}%")

            # Différences
            if recon['differences']:
                lines.append(f"\n⚠️  Différences détectées ({len(recon['differences'])}):")
                for diff in recon['differences'][:5]:
                    lines.append(f"\n  {diff['entity1']} ↔ {diff['entity2']} ({diff['month']})")
                    lines.append(f"    {diff['entity1']} → {diff['entity2']}: {diff['balance_e1_to_e2']:,.2f} €")
                    lines.append(f"    {diff['entity2']} → {diff['entity1']}: {diff['balance_e2_to_e1']:,.2f} €")
                    lines.append(f"    Différence: {diff['difference']:,.2f} €")

            # Soldes
            balances = self.get_intercompany_balances()
            lines.append(f"\n💰 Soldes inter-compagnies:")
            for bal in balances[:10]:
                lines.append(f"\n  {bal['entity1']} ↔ {bal['entity2']}")
                lines.append(f"    {bal['who_owes']}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)
