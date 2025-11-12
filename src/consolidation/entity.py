"""Modèle d'entité pour la consolidation multi-sociétés."""
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """
    Représente une entité juridique (SCCV, société mère, etc.).
    """
    code: str = Field(..., description="Code unique de l'entité")
    name: str = Field(..., description="Nom de l'entité")
    entity_type: str = Field(..., description="Type: SCCV, MERE, FILIALE")
    siren: Optional[str] = Field(None, description="Numéro SIREN")

    # Exercice comptable
    exercice_start: date = Field(..., description="Début d'exercice")
    exercice_end: date = Field(..., description="Fin d'exercice")

    # Relations groupe
    parent_code: Optional[str] = Field(None, description="Code de la société mère")
    ownership_pct: float = Field(100.0, description="% de détention")

    # Comptes inter-compagnies
    intercompany_account_prefix: str = Field("451", description="Préfixe compte courant")

    # Métadonnées
    address: Optional[str] = None
    city: Optional[str] = None
    active: bool = True

    class Config:
        """Configuration Pydantic."""
        json_encoders = {
            date: lambda v: v.strftime('%Y-%m-%d')
        }


class EntityManager:
    """
    Gestionnaire d'entités pour la consolidation.

    Gère le référentiel des entités du groupe et leurs relations.
    """

    def __init__(self):
        """Initialise le gestionnaire d'entités."""
        self.entities: Dict[str, Entity] = {}

    def add_entity(self, entity: Entity) -> None:
        """
        Ajoute une entité au référentiel.

        Args:
            entity: Entité à ajouter
        """
        self.entities[entity.code] = entity

    def get_entity(self, code: str) -> Optional[Entity]:
        """
        Récupère une entité par son code.

        Args:
            code: Code de l'entité

        Returns:
            Entité ou None si non trouvée
        """
        return self.entities.get(code)

    def get_all_entities(self) -> List[Entity]:
        """
        Récupère toutes les entités.

        Returns:
            Liste des entités
        """
        return list(self.entities.values())

    def get_active_entities(self) -> List[Entity]:
        """
        Récupère les entités actives.

        Returns:
            Liste des entités actives
        """
        return [e for e in self.entities.values() if e.active]

    def get_subsidiaries(self, parent_code: str) -> List[Entity]:
        """
        Récupère les filiales d'une entité.

        Args:
            parent_code: Code de la société mère

        Returns:
            Liste des filiales
        """
        return [e for e in self.entities.values() if e.parent_code == parent_code]

    def get_sccv_entities(self) -> List[Entity]:
        """
        Récupère toutes les SCCV.

        Returns:
            Liste des SCCV
        """
        return [e for e in self.entities.values() if e.entity_type == 'SCCV']

    def get_parent_entity(self) -> Optional[Entity]:
        """
        Récupère la société mère.

        Returns:
            Entité mère ou None
        """
        for entity in self.entities.values():
            if entity.entity_type == 'MERE':
                return entity
        return None

    def get_intercompany_mapping(self) -> Dict[str, str]:
        """
        Crée un mapping code entité -> préfixe compte courant.

        Returns:
            Dictionnaire {code_entité: préfixe_compte}
        """
        return {
            entity.code: entity.intercompany_account_prefix
            for entity in self.entities.values()
        }

    def check_period_overlap(self, entity1_code: str, entity2_code: str,
                            target_date: date) -> bool:
        """
        Vérifie si une date est dans l'exercice des deux entités.

        Args:
            entity1_code: Code première entité
            entity2_code: Code seconde entité
            target_date: Date à vérifier

        Returns:
            True si la date est dans les deux exercices
        """
        entity1 = self.get_entity(entity1_code)
        entity2 = self.get_entity(entity2_code)

        if not entity1 or not entity2:
            return False

        in_entity1 = entity1.exercice_start <= target_date <= entity1.exercice_end
        in_entity2 = entity2.exercice_start <= target_date <= entity2.exercice_end

        return in_entity1 and in_entity2

    def get_common_period(self, entity_codes: List[str]) -> Optional[Dict[str, date]]:
        """
        Trouve la période commune à plusieurs entités.

        Args:
            entity_codes: Liste des codes d'entités

        Returns:
            Dictionnaire avec 'start' et 'end' ou None
        """
        entities = [self.get_entity(code) for code in entity_codes]
        entities = [e for e in entities if e]

        if not entities:
            return None

        # Trouver la période d'intersection
        start = max(e.exercice_start for e in entities)
        end = min(e.exercice_end for e in entities)

        if start <= end:
            return {'start': start, 'end': end}

        return None

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convertit toutes les entités en liste de dictionnaires.

        Returns:
            Liste de dictionnaires
        """
        return [
            {
                'code': e.code,
                'name': e.name,
                'type': e.entity_type,
                'siren': e.siren or '',
                'exercice_start': e.exercice_start.strftime('%Y-%m-%d'),
                'exercice_end': e.exercice_end.strftime('%Y-%m-%d'),
                'parent_code': e.parent_code or '',
                'ownership_pct': e.ownership_pct,
                'intercompany_prefix': e.intercompany_account_prefix,
                'active': e.active
            }
            for e in self.entities.values()
        ]

    def load_from_dict_list(self, entities_data: List[Dict[str, Any]]) -> None:
        """
        Charge les entités depuis une liste de dictionnaires.

        Args:
            entities_data: Liste de dictionnaires d'entités
        """
        from datetime import datetime

        self.entities.clear()

        for data in entities_data:
            entity = Entity(
                code=data['code'],
                name=data['name'],
                entity_type=data['type'],
                siren=data.get('siren'),
                exercice_start=datetime.strptime(data['exercice_start'], '%Y-%m-%d').date(),
                exercice_end=datetime.strptime(data['exercice_end'], '%Y-%m-%d').date(),
                parent_code=data.get('parent_code'),
                ownership_pct=float(data.get('ownership_pct', 100.0)),
                intercompany_account_prefix=data.get('intercompany_prefix', '451'),
                active=data.get('active', True)
            )
            self.add_entity(entity)
