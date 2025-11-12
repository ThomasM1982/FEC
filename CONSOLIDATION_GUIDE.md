# Guide de Consolidation Multi-Entités

Ce guide explique comment utiliser le système de consolidation pour analyser plusieurs FEC de SCCV (Sociétés Civiles de Construction Vente) en tenant compte des exercices décalés et des flux inter-compagnies.

## Cas d'usage

Le système est conçu pour :
- **Sociétés de promotion immobilière** avec 10 à 20 SCCV
- **Exercices comptables décalés** entre les différentes entités
- **Identification automatique des flux inter-compagnies** (comptes courants)
- **Consolidation des KPI** au niveau groupe
- **Suivi dans Grist** avec historisation

## Architecture

```
Société Mère (Promotion Immobilière)
    ├─ SCCV001 (Projet Résidence A) - Exercice 01/2024 → 12/2024
    ├─ SCCV002 (Projet Parc B)      - Exercice 03/2024 → 02/2025
    ├─ SCCV003 (Projet Villa C)     - Exercice 07/2023 → 06/2024
    └─ SCCV...
```

## Configuration

### 1. Créer le fichier de configuration des entités

Créez un fichier `entities_config.json` :

```json
{
  "entities": [
    {
      "code": "PROMO",
      "name": "Société de Promotion",
      "type": "MERE",
      "siren": "123456789",
      "exercice_start": "2024-01-01",
      "exercice_end": "2024-12-31",
      "intercompany_prefix": "451",
      "active": true
    },
    {
      "code": "SCCV001",
      "name": "SCCV Projet A",
      "type": "SCCV",
      "siren": "234567890",
      "exercice_start": "2024-01-01",
      "exercice_end": "2024-12-31",
      "parent_code": "PROMO",
      "ownership_pct": 100.0,
      "intercompany_prefix": "451001",
      "active": true
    }
  ]
}
```

**Champs importants** :
- `code` : Code unique de l'entité (utilisé dans les noms de fichiers FEC)
- `type` : `MERE` pour la société mère, `SCCV` pour les filiales
- `exercice_start` / `exercice_end` : Dates de l'exercice comptable
- `parent_code` : Code de la société mère
- `intercompany_prefix` : Préfixe des comptes courants (ex: 451, 451001, etc.)

### 2. Organiser les fichiers FEC

Placez vos fichiers FEC dans un répertoire avec la nomenclature :

```
data/fec_sccv/
  ├── PROMO_2024.txt
  ├── SCCV001_2024.txt
  ├── SCCV002_2024.txt
  └── SCCV003_2024.txt
```

Le script cherchera automatiquement les fichiers contenant le code de l'entité.

## Utilisation

### Script de consolidation

```bash
python examples/consolidation_groupe.py entities_config.json data/fec_sccv/
```

Le script va :

1. **Charger les entités** depuis le fichier JSON
2. **Trouver et lire les FEC** pour chaque entité
3. **Analyser les périodes** et identifier les exercices décalés
4. **Calculer la période commune** pour la consolidation
5. **Identifier les flux inter-compagnies** (comptes 451xxx)
6. **Rapprocher les flux** entre entités
7. **Calculer les KPI consolidés** (CA, résultat, trésorerie, etc.)
8. **Classer les SCCV** par performance
9. **Uploader vers Grist** (optionnel)
10. **Générer un rapport** de consolidation

### Exemple de sortie

```
================================================================================
CONSOLIDATION MULTI-ENTITÉS - ANALYSE GROUPE
================================================================================

1️⃣  Chargement de la configuration des entités...
   ✓ 6 entités chargées
   📊 Société mère: Société de Promotion Immobilière
   🏢 SCCV: 5
      - SCCV001: SCCV Résidence Les Jardins
      - SCCV002: SCCV Parc des Lilas
      ...

2️⃣  Chargement des fichiers FEC...
   📁 PROMO: PROMO_2024.txt
      ✓ 1250 écritures chargées
   📁 SCCV001: SCCV001_2024.txt
      ✓ 850 écritures chargées
   ...

3️⃣  Analyse des périodes comptables...
   ⚠️  Attention: Exercices décalés détectés

   📅 Périodes par entité:
      PROMO: 2024-01-01 → 2024-12-31
      SCCV001: 2024-01-01 → 2024-12-31
      SCCV002: 2024-03-01 → 2025-02-28
      SCCV003: 2023-07-01 → 2024-06-30

   ✅ Période commune identifiée:
      2024-03-01 → 2024-06-30 (122 jours)

4️⃣  Calcul de la consolidation groupe...

   💰 KPI Consolidés:
      CA groupe:              2,450,000.00 €
      Charges:                1,950,000.00 €
      Résultat net:             500,000.00 €
      Marge:                         20.41 %
      Trésorerie:               750,000.00 €

5️⃣  Analyse des flux inter-compagnies...

   🔄 Flux inter-compagnies:
      Total flux:       45
      Rapprochés:       42 (93.3%)
      Non rapprochés:   3
      Soldes nets:           15,000.00 €

   📊 Top 5 des soldes inter-compagnies:

      1. PROMO ↔ SCCV001
         SCCV001 doit 50000.00 € à PROMO

      2. PROMO ↔ SCCV002
         Équilibré

6️⃣  Classement des SCCV par performance...

   Rang   SCCV                           CA         Marge         Perf
   ---------------------------------------------------------------------------
   1      SCCV Résidence Les Jardins     850,000       25.5%   Excellente
   2      SCCV Parc des Lilas            620,000       18.2%        Bonne
   3      SCCV Villa Moderne             450,000       15.1%   Excellente
   ...
```

## Gestion des exercices décalés

Le système gère automatiquement les exercices décalés de plusieurs façons :

### 1. Période commune

Le système identifie automatiquement la **période d'intersection** entre tous les exercices :

```python
# Exemple d'exercices décalés
PROMO:     [========== 01/2024 → 12/2024 ==========]
SCCV001:   [========== 01/2024 → 12/2024 ==========]
SCCV002:         [========== 03/2024 → 02/2025 ==========]
SCCV003: [========== 07/2023 → 06/2024 =====]

Période commune:  [=== 03/2024 → 06/2024 ===]
```

### 2. Consolidation sur période commune

Par défaut, la consolidation utilise la période commune pour assurer la cohérence :

```python
kpi = consolidation.get_consolidated_kpi(use_common_period=True)
```

### 3. Consolidation sur période complète

Vous pouvez aussi consolider sur la période complète (union de toutes les périodes) :

```python
kpi = consolidation.get_consolidated_kpi(use_common_period=False)
```

⚠️ **Attention** : Dans ce cas, certaines entités peuvent avoir des données partielles.

## Flux inter-compagnies

### Identification automatique

Le système identifie automatiquement les flux inter-compagnies via :

1. **Comptes courants** (préfixe 451)
2. **Comptes auxiliaires** contenant le code de l'entité partenaire
3. **Libellés** mentionnant l'entité partenaire

### Rapprochement

Le système rapproche automatiquement les flux :

```
PROMO → SCCV001 : 100,000 € (débit PROMO compte 451001)
SCCV001 → PROMO : 100,000 € (crédit SCCV001 compte 451)

✓ Flux rapproché (différence: 0 €)
```

### Non-rapprochement

Si les flux ne se rapprochent pas :

```
PROMO → SCCV002 : 50,000 €
SCCV002 → PROMO : 48,500 €

⚠️  Différence détectée: 1,500 €
```

## Tables Grist créées

Le système crée automatiquement 4 tables dans Grist :

### 1. **Entites**
Référentiel des entités du groupe

| Code | Nom | Type | SIREN | Exercice Début | Exercice Fin | % Détention |
|------|-----|------|-------|----------------|--------------|-------------|
| PROMO | Société Promo | MERE | 123... | 2024-01-01 | 2024-12-31 | 100 |
| SCCV001 | SCCV Projet A | SCCV | 234... | 2024-01-01 | 2024-12-31 | 100 |

### 2. **Consolidation**
Historique des consolidations

| Date Calcul | Période | CA Consolidé | Résultat | Flux IC | Taux Rappro |
|-------------|---------|--------------|----------|---------|-------------|
| 2024-11-12 | 03→06/24 | 2,450,000 | 500,000 | 45 | 93.3% |

### 3. **FluxInterCompagnies**
Soldes inter-compagnies

| Entité 1 | Entité 2 | Solde Net | Qui doit |
|----------|----------|-----------|----------|
| PROMO | SCCV001 | 50,000 | SCCV001 doit 50,000 € à PROMO |
| PROMO | SCCV002 | 0 | Équilibré |

### 4. **EcrituresComptables**
Toutes les écritures de toutes les entités (avec colonne Entité)

## Analyses disponibles

### KPI consolidés
- Chiffre d'affaires groupe
- Charges totales
- Résultat net consolidé
- Marge nette groupe
- Trésorerie consolidée

### Performance par entité
- Classement des SCCV par CA
- Classement par rentabilité
- Identification des meilleures/moins bonnes performances

### Flux inter-compagnies
- Total des flux identifiés
- Taux de rapprochement
- Différences à analyser
- Soldes nets par paire d'entités

### Qualité des données
- Couverture des périodes
- Cohérence des flux IC
- Anomalies détectées

## API Python

### Utilisation programmatique

```python
from src.consolidation.entity import EntityManager, Entity
from src.consolidation.consolidation import ConsolidationEngine
from datetime import date

# 1. Créer le gestionnaire d'entités
manager = EntityManager()

# 2. Ajouter des entités
manager.add_entity(Entity(
    code="PROMO",
    name="Société Mère",
    entity_type="MERE",
    exercice_start=date(2024, 1, 1),
    exercice_end=date(2024, 12, 31),
    intercompany_account_prefix="451"
))

manager.add_entity(Entity(
    code="SCCV001",
    name="SCCV Projet A",
    entity_type="SCCV",
    parent_code="PROMO",
    ownership_pct=100.0,
    exercice_start=date(2024, 1, 1),
    exercice_end=date(2024, 12, 31),
    intercompany_account_prefix="451001"
))

# 3. Créer le moteur de consolidation
consolidation = ConsolidationEngine(manager)

# 4. Charger les données
from src.readers.fec_reader import FECReader

for entity in manager.get_all_entities():
    reader = FECReader(f"{entity.code}_2024.txt")
    entries = reader.read()
    consolidation.load_entity_data(entity.code, entries)

# 5. Obtenir les KPI consolidés
kpi = consolidation.get_consolidated_kpi(use_common_period=True)

# 6. Analyser les flux IC
ic_balances = consolidation.intercompany_analyzer.get_intercompany_balances()

# 7. Classer les SCCV
ranking = consolidation.get_sccv_performance_ranking()
```

## Bonnes pratiques

### Nomenclature des fichiers
- Utilisez un préfixe cohérent : `<CODE_ENTITE>_<ANNEE>.txt`
- Exemple : `SCCV001_2024.txt`, `PROMO_2024.txt`

### Configuration des comptes IC
- Société mère : `451` (générique)
- SCCV : `451001`, `451002`, etc. (spécifique par SCCV)
- Permet l'identification automatique des flux

### Gestion des exercices
- Documentez les exercices décalés dans le fichier de configuration
- Utilisez la période commune pour les comparaisons
- Analysez les périodes complètes pour la vision globale

### Rapprochement IC
- Vérifiez régulièrement le taux de rapprochement
- Investiguez les différences > 1%
- Assurez-vous que les comptes auxiliaires sont bien renseignés

## Dépannage

### "Aucun FEC trouvé pour <entity>"
- Vérifiez que le nom du fichier contient le code de l'entité
- Vérifiez le chemin du répertoire des FEC

### "Exercices décalés détectés"
- C'est normal pour des SCCV avec des démarrages différents
- Le système calculera automatiquement la période commune

### "Flux non rapprochés élevés"
- Vérifiez les comptes auxiliaires dans les FEC
- Assurez-vous que les préfixes IC sont corrects
- Vérifiez que les libellés mentionnent l'entité partenaire

### Erreur de connexion Grist
- Vérifiez votre fichier `.env`
- Vérifiez que `GRIST_API_KEY` et `GRIST_DOC_ID` sont définis

## Support

Pour toute question ou problème :
1. Vérifiez la documentation
2. Consultez les exemples dans `/examples`
3. Ouvrez une issue sur GitHub
