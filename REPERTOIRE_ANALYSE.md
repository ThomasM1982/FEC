# Analyse du référentiel FEC

Cette note décrit l'organisation actuelle du projet, les principales fonctionnalités par module et les points d'entrée disponibles pour manipuler des fichiers d'écritures comptables et interagir avec Grist.

## Structure générale
- `src/models` : modèles de données Pydantic pour représenter une écriture comptable FEC et son journal.
- `src/readers` : lecture et filtrage des fichiers FEC (CSV, TXT, Excel) avec normalisation des colonnes.
- `src/validators` : règles de validation des écritures et vérification de l'équilibrage global.
- `src/kpi` : calculs de KPI financiers et opérationnels à partir des écritures lues.
- `src/grist` : client HTTP pour pousser les écritures ou KPI dans une table Grist en créant la structure si nécessaire.
- `src/consolidation` : primitives pour agréger plusieurs entités (SCCV) et identifier des flux intercompagnies.
- `examples` : scripts prêts à l'emploi pour analyser un FEC, générer un rapport de KPI ou lancer la consolidation multi-entités.
- `tests` : tests unitaires ciblant le modèle d'écriture comptable.

## Points clés par composant
### Modèles
`src/models/accounting_entry.py` définit le modèle `AccountingEntry` avec conversion automatique des dates/decimales, vérification d'équilibre par écriture et export prêt pour l'API Grist via `to_grist_dict`. Le modèle `Journal` encapsule l'identité d'un journal comptable.

### Lecture et validation
`src/readers/fec_reader.py` gère la détection du délimiteur, la normalisation des noms de colonnes FEC et produit des instances `AccountingEntry`. Il expose des filtres basiques (journal, compte, plages de dates) et des statistiques d'ensemble (totaux débit/crédit, équilibrage, ventilation par journal).
`src/validators/fec_validator.py` fournit des validations globales : équilibrage total, contrôle du lettrage et détection des entrées sans libellé ou numéro de pièce.

### Calculs de KPI
`src/kpi/calculator.py` centralise les agrégations financières courantes (CA, charges, résultat net, trésorerie, BFR, etc.) et expose `calculate_all_kpi` pour produire un dictionnaire complet utilisable par les KPI financiers/opérationnels ou un upload Grist.
`src/kpi/financial_kpi.py` et `src/kpi/operational_kpi.py` ajoutent des ratios (liquidité, solvabilité, ROE/ROA, marges) et des indicateurs d’activité (nombre d’écritures, comptes utilisés, top clients).

### Intégration Grist
`src/grist/client.py` encapsule l’authentification (API key, doc/table IDs), la création conditionnelle de table avec les colonnes FEC standard, et les opérations CRUD (ajout batch, lecture filtrée, mise à jour, suppression). La méthode `upload_entries` gère un découpage en lots avec suivi des erreurs.

### Consolidation multi-entités
`src/consolidation/consolidation.py`, `entity.py` et `intercompany.py` définissent les entités consolidées, le calcul des flux intercompagnies et l’agrégation groupe (totaux, KPI consolidés, classement des entités). Les scripts d’exemple orchestrent ces briques.

## Tests
`tests/test_accounting_entry.py` valide le parsing des dates et décimales, la détection d’équilibrage et la conversion au format Grist. Le jeu de tests est léger et se concentre sur les conversions critiques du modèle.

## Points d’attention
- Les warnings Pytest signalent une configuration Pydantic v1 (`Config`, `json_encoders`) encore utilisée ; une migration vers Pydantic v2 (ConfigDict/custom serializers) sera à prévoir.
- Aucun guide de contribution ou pipeline CI n’est présent ; l’exécution de `pytest` couvre uniquement le modèle d’écriture.

## Axes d'amélioration recommandés
- **Accroître la couverture de tests** : aujourd’hui seuls les modèles sont vérifiés (`tests/test_accounting_entry.py`). Ajouter des scénarios sur les fonctions critiques de lecture/validation (détection de délimiteur, normalisation des colonnes, filtres, équilibrage global) aiderait à sécuriser `src/readers/fec_reader.py` et `src/validators/fec_validator.py`.
- **Rendre les erreurs lisibles** : `FECReader.read` imprime les erreurs de ligne avec `print` puis les masque dans un `ValueError` général. Remplacer ces impressions par du `logging` structuré et relayer la ligne fautive (index ou ref pièce) permettrait de diagnostiquer plus vite les fichiers invalides.
- **Préparer la migration Pydantic v2** : le modèle `AccountingEntry` utilise encore `Config` et `field_validator`. Planifier le passage vers `ConfigDict`/`field_validator(mode="before")` v2 et les `model_dump` explicites réduira les avertissements et facilitera la sérialisation vers Grist.
- **Garder la mémoire sous contrôle** : la lecture charge tout le DataFrame en mémoire avant conversion. Pour les FEC volumineux, l’usage de `pandas.read_csv(..., chunksize=...)` ou d’un générateur d’`AccountingEntry` limiterait le pic mémoire et accélérerait les pipelines batch/CI.
