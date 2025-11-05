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

## Flux de travail recommandé

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
