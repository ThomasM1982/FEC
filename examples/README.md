# Exemples d'utilisation

Ce dossier contient des scripts d'exemple pour utiliser la bibliothèque de gestion des écritures comptables.

## Scripts disponibles

### 1. generate_sample_fec.py

Génère un fichier FEC d'exemple pour tester les fonctionnalités.

```bash
python generate_sample_fec.py sample_fec.txt
```

### 2. analyze_fec.py

Analyse un fichier FEC et affiche des statistiques détaillées sans l'uploader vers Grist.

```bash
python analyze_fec.py sample_fec.txt
```

Affiche:
- Statistiques générales (nombre d'écritures, totaux débit/crédit)
- Analyse par journal
- Analyse par classe de comptes
- Rapport de validation

### 3. upload_to_grist.py

Lit un fichier FEC, le valide et l'upload vers Grist.

```bash
python upload_to_grist.py sample_fec.txt
```

**Prérequis**: Configurer le fichier `.env` avec vos credentials Grist.

### 4. generate_kpi_report.py

Génère un rapport KPI complet à partir d'un fichier FEC avec analyse financière et opérationnelle.

```bash
python generate_kpi_report.py sample_fec.txt
```

Options:
- Format texte (par défaut) : Rapport lisible avec interprétations
- Format JSON : `python generate_kpi_report.py sample_fec.txt --format json`

Le rapport inclut:
- KPI financiers (CA, charges, résultat, trésorerie, BFR, etc.)
- Ratios financiers (liquidité, solvabilité, rentabilité)
- Délais de paiement et rotation
- KPI opérationnels (qualité des données, productivité)
- Top clients
- Évolution mensuelle
- Balance âgée clients

### 5. upload_kpi_to_grist.py

Calcule les KPI et les upload dans une table Grist dédiée pour suivi historique.

```bash
python upload_kpi_to_grist.py sample_fec.txt
```

Crée automatiquement une table "KPI" dans Grist avec:
- Date de calcul
- Période analysée
- Tous les KPI financiers et ratios principaux
- Historique pour suivre l'évolution dans le temps

**Prérequis**: Configurer le fichier `.env` avec vos credentials Grist.

## Flux de travail recommandé

### Workflow de base

1. **Générer un fichier d'exemple** (ou utiliser votre propre fichier FEC):
   ```bash
   python generate_sample_fec.py test.txt
   ```

2. **Analyser le fichier** pour vérifier sa validité:
   ```bash
   python analyze_fec.py test.txt
   ```

3. **Uploader vers Grist** si tout est correct:
   ```bash
   python upload_to_grist.py test.txt
   ```

### Workflow avec analyse KPI

1. **Générer un fichier d'exemple**:
   ```bash
   python generate_sample_fec.py test.txt
   ```

2. **Générer le rapport KPI complet**:
   ```bash
   python generate_kpi_report.py test.txt
   ```
   Cela crée un fichier `kpi_report_YYYYMMDD_HHMMSS.txt` avec l'analyse complète.

3. **Uploader les écritures ET les KPI vers Grist**:
   ```bash
   # Upload des écritures
   python upload_to_grist.py test.txt

   # Upload des KPI dans une table séparée
   python upload_kpi_to_grist.py test.txt
   ```

4. **Consulter dans Grist**: Vos données sont maintenant dans Grist avec:
   - Table "EcrituresComptables" : Toutes vos écritures
   - Table "KPI" : Historique des KPI pour analyse d'évolution

### Analyse périodique

Pour un suivi régulier (mensuel, trimestriel):

```bash
# À chaque période, uploader les nouvelles données et KPI
python upload_to_grist.py FEC_Q1_2024.txt
python upload_kpi_to_grist.py FEC_Q1_2024.txt

python upload_to_grist.py FEC_Q2_2024.txt
python upload_kpi_to_grist.py FEC_Q2_2024.txt
```

Grist conservera l'historique des KPI pour suivre l'évolution dans le temps.

## Configuration pour l'upload vers Grist

Créez un fichier `.env` à la racine du projet:

```bash
cp ../.env.example ../.env
```

Puis éditez `.env` avec vos informations:

```
GRIST_API_KEY=votre_clé_api
GRIST_SERVER_URL=https://docs.getgrist.com
GRIST_DOC_ID=votre_doc_id
TABLE_NAME=EcrituresComptables
```

### Obtenir vos credentials Grist

1. **API Key**: Dans Grist, allez dans votre profil > Settings > API
2. **Document ID**: Visible dans l'URL de votre document Grist
   - Exemple: `https://docs.getgrist.com/doc/ABC123XYZ` → `ABC123XYZ`
3. **Table Name**: Le nom de la table où stocker les écritures (sera créée automatiquement)

## Formats de fichiers supportés

- **TXT**: Fichiers texte délimités (tabulation, pipe |, point-virgule)
- **CSV**: Fichiers CSV (virgule, point-virgule, tabulation)
- **XLSX**: Fichiers Excel

## Structure du fichier FEC

Le fichier doit contenir les colonnes suivantes (format standard FEC):

- JournalCode
- JournalLib
- EcritureNum
- EcritureDate (format YYYYMMDD)
- CompteNum
- CompteLib
- CompAuxNum (optionnel)
- CompAuxLib (optionnel)
- PieceRef
- PieceDate (format YYYYMMDD)
- EcritureLib
- Debit
- Credit
- EcritureLet (optionnel)
- DateLet (optionnel)
- ValidDate (format YYYYMMDD)
- Montantdevise (optionnel)
- Idevise (optionnel)
