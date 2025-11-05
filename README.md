# Gestion des Écritures Comptables avec Grist

Ce projet permet d'exploiter des fichiers d'écritures comptables (FEC - Fichier des Écritures Comptables) et de les intégrer avec Grist.

## Fonctionnalités

- Lecture de fichiers FEC (CSV, Excel, TXT)
- Validation des écritures comptables
- Intégration avec l'API Grist
- Export et import des données
- **Calcul automatique de KPI financiers et opérationnels**
- **Génération de rapports d'analyse**
- **Suivi historique des KPI dans Grist**

## Structure du projet

```
.
├── src/
│   ├── models/          # Modèles de données
│   ├── grist/           # Client API Grist
│   ├── readers/         # Lecteurs de fichiers
│   ├── validators/      # Validateurs d'écritures
│   └── kpi/            # Calculateurs de KPI
├── examples/            # Scripts d'exemple
├── tests/              # Tests unitaires
└── requirements.txt    # Dépendances
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Créez un fichier `.env` avec vos credentials Grist :

```
GRIST_API_KEY=votre_clé_api
GRIST_SERVER_URL=https://docs.getgrist.com
GRIST_DOC_ID=votre_doc_id
```

## Utilisation

### Upload des écritures comptables

```python
from src.readers.fec_reader import FECReader
from src.grist.client import GristClient

# Lire un fichier FEC
reader = FECReader('ecritures.txt')
entries = reader.read()

# Envoyer à Grist
client = GristClient()
client.upload_entries(entries)
```

### Calcul et analyse des KPI

```python
from src.kpi.calculator import KPICalculator
from src.kpi.financial_kpi import FinancialKPI
from src.kpi.operational_kpi import OperationalKPI

# Calculer les KPI
calc = KPICalculator(entries)
fin_kpi = FinancialKPI(calc)
op_kpi = OperationalKPI(calc)

# Obtenir les KPI financiers
print(f"CA: {calc.get_chiffre_affaires()}")
print(f"Résultat: {calc.get_resultat_net()}")
print(f"ROE: {fin_kpi.get_roe()}")

# Upload des KPI vers Grist
kpi_data = calc.calculate_all_kpi()
client.upload_kpi(kpi_data)
```

### Scripts d'exemple

```bash
# Analyser un fichier FEC
python examples/analyze_fec.py fichier.txt

# Générer un rapport KPI complet
python examples/generate_kpi_report.py fichier.txt

# Uploader vers Grist avec KPI
python examples/upload_to_grist.py fichier.txt
python examples/upload_kpi_to_grist.py fichier.txt
```

## KPI Disponibles

### KPI Financiers de Base

- **Chiffre d'affaires** : Total des ventes (comptes 70x)
- **Charges** : Total des charges (comptes 6xx)
- **Résultat net** : Produits - Charges
- **Marge brute** : CA - Achats
- **Trésorerie** : Solde des comptes bancaires (51x, 53x)
- **Créances clients** : Solde des comptes clients (41x)
- **Dettes fournisseurs** : Solde des comptes fournisseurs (40x)
- **Fonds de roulement** : Capitaux permanents - Immobilisations
- **BFR** : Besoin en fonds de roulement

### Ratios Financiers

#### Liquidité
- Ratio de liquidité générale (Current Ratio)
- Ratio de liquidité immédiate (Quick Ratio)
- Ratio de trésorerie (Cash Ratio)

#### Solvabilité
- Ratio d'autonomie financière
- Ratio d'endettement

#### Rentabilité
- ROE (Return on Equity)
- ROA (Return on Assets)
- Taux de marge commerciale
- Taux de marge nette
- Seuil de rentabilité

#### Délais et Rotation
- Délai de paiement clients (en jours)
- Délai de paiement fournisseurs (en jours)
- Rotation des stocks (en jours)

### KPI Opérationnels

- **Nombre d'écritures** : Total des écritures comptables
- **Comptes utilisés** : Nombre de comptes différents
- **Jours d'activité** : Nombre de jours avec écritures
- **Écritures par jour** : Productivité comptable
- **Taux d'équilibrage** : Pourcentage d'écritures équilibrées
- **Score de qualité** : Qualité des données comptables (0-100)
- **Top clients** : Classement des meilleurs clients
- **Balance âgée clients** : Ancienneté des créances
- **Évolution mensuelle** : CA, charges et résultat par mois
- **Répartition par journal** : Statistiques par journal comptable

## Format FEC

Le format FEC suit la norme française pour les fichiers des écritures comptables :
- Date d'écriture
- Numéro de compte
- Libellé
- Montant débit
- Montant crédit
- Journal
- etc.
