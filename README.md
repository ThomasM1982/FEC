# Gestion des Écritures Comptables avec Grist

Ce projet permet d'exploiter des fichiers d'écritures comptables (FEC - Fichier des Écritures Comptables) et de les intégrer avec Grist.

## Fonctionnalités

- Lecture de fichiers FEC (CSV, Excel, TXT)
- Validation des écritures comptables
- Intégration avec l'API Grist
- Export et import des données

## Structure du projet

```
.
├── src/
│   ├── models/          # Modèles de données
│   ├── grist/           # Client API Grist
│   ├── readers/         # Lecteurs de fichiers
│   └── validators/      # Validateurs d'écritures
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

## Format FEC

Le format FEC suit la norme française pour les fichiers des écritures comptables :
- Date d'écriture
- Numéro de compte
- Libellé
- Montant débit
- Montant crédit
- Journal
- etc.
