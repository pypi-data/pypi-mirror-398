"""
Data models for unified normalizer.

Provides unified Pydantic models that work for both UMLS and ontology concepts.
"""

from __future__ import annotations

from pydantic import BaseModel


class SemanticType(BaseModel):
    """Semantic type (UMLS only)."""

    type_id: str  # TUI
    type_name: str  # STY


class ConceptInfo(BaseModel):
    """
    Unified concept information.

    Works for both UMLS (CUI) and ontology (global_id) concepts.
    For ontology databases, semantic_types will be empty.
    """

    concept_id: str  # CUI or global_id
    identifier: str | None  # Source-specific ID (CUI for UMLS, e.g. "15377" for CHEBI)
    source: str | None  # SAB or source
    preferred_name: str | None
    name_type: str | None  # TTY or name_type
    description: str | None
    def_source: str | None  # Source of definition (UMLS only)
    synonyms: list[str]
    semantic_types: list[SemanticType]  # Empty for ontology


# Type aliases for backward compatibility
OntologyConceptInfo = ConceptInfo
UMLSConceptInfo = ConceptInfo
