"""Module de gestion multi-entités pour consolidation."""
from .entity import Entity, EntityManager
from .intercompany import IntercompanyAnalyzer
from .consolidation import ConsolidationEngine

__all__ = ['Entity', 'EntityManager', 'IntercompanyAnalyzer', 'ConsolidationEngine']
