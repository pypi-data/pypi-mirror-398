from enum import StrEnum

import polars as pl

# =============================================================================
# Database Schema Constants
# =============================================================================

NS_TABLE = "ns"  # Normalized string index
NW_TABLE = "nw"  # Normalized word index
ATOMS_TABLE = "atoms"  # Atom details
CONCEPTS_TABLE = "concepts"  # Concept metadata
TYPES_TABLE = "types"  # Semantic types (UMLS only)
DEFS_TABLE = "defs"  # Definitions
EDGES_TABLE = "edges"  # Hierarchy edges

# =============================================================================
# Scoring Constants
# =============================================================================

RANK_MULTIPLIER = 100
ISPREF_WEIGHT = 10
STT_WEIGHT = 5
TTY_WEIGHT = 1
EXACT_BUMP = 1000

DEFAULT_PREFER_TTYS = ["MH", "PT", "PN"]

# Polars struct type for normalized hits
HIT_STRUCT_TYPE = pl.Struct(
    {
        "global_identifier": pl.Utf8,
        "identifier": pl.Utf8,
        "nstr": pl.Utf8,
        "name": pl.Utf8,
        "source": pl.Utf8,
        "name_type": pl.Utf8,
        "score": pl.Int64,
        "total_score": pl.Int64,
        "match_type": pl.Utf8,
    }
)

# Schema for ontology DataFrames (input to build_ontology_duckdb)
ONTOLOGY_DF_SCHEMA = {
    "global_identifier": pl.Utf8,
    "identifier": pl.Utf8,
    "source": pl.Utf8,
    "pref_name": pl.Utf8,
    "description": pl.Utf8,
    "pref_name_norm": pl.Utf8,
    "synonyms": pl.List(pl.Utf8),
    "synonyms_norm": pl.List(pl.Utf8),
}

# =============================================================================
# Entity Type Constants
# =============================================================================


class EntityType(StrEnum):
    PROTEIN_GENEFAMILY = "Protein/GeneFamily"
    DISEASE = "Disease"
    CELLTYPE = "CellType"
    GOTERM = "GOTerm"
    ANATOMY = "Anatomy"
    PHENOTYPE = "Phenotype"
    SMALLMOLECULECLASS = "SmallMoleculeClass"
    ORGANISM = "Organism"
    ASSAY_RESULT = "Assay/Result"
    PATHWAY = "Pathway"
    CELLLINE = "CellLine"
    GENE = "Gene"
    PROTEIN = "Protein"
    GENEVARIANT = "GeneVariant"
    SMALLMOLECULE = "SmallMolecule"
    CLINICALTRIAL = "ClinicalTrial"
    PEPTIDE = "Peptide"
    ANTIBODY = "Antibody"
    RNA = "RNA"


UMLS_ENTITY_TYPES = {
    EntityType.PROTEIN_GENEFAMILY,
    EntityType.DISEASE,
    EntityType.CELLTYPE,
    EntityType.GOTERM,
    EntityType.ANATOMY,
    EntityType.PHENOTYPE,
}

ONT_ENTITY_TYPES = {
    EntityType.SMALLMOLECULECLASS,
    EntityType.ORGANISM,
    EntityType.ASSAY_RESULT,
    EntityType.PATHWAY,
    EntityType.CELLLINE,
}

MANUAL_ENTITY_TYPES = {
    EntityType.GENE,
    EntityType.PROTEIN,
    EntityType.GENEVARIANT,
    EntityType.SMALLMOLECULE,
    EntityType.CLINICALTRIAL,
}

UNK_ENTITY_TYPES = {
    EntityType.PEPTIDE,
    EntityType.ANTIBODY,
    EntityType.RNA,
}
