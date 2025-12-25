"""
Unified normalization package.

Provides normalizer implementations that work with UMLS, ontology,
and merged databases using a standardized schema.

Build functions:
- build_umls_duckdb: Build UMLS database from Metathesaurus RRF files
- build_ontology_duckdb: Build ontology database from Polars DataFrame
- build_merged_duckdb: Build merged UMLS + ontology database

All build functions output the same schema, so you can use DuckDBNormalizer
or PostgresNormalizer with any database built by any of the build functions.

Normalizers:
- DuckDBNormalizer: High-throughput sync normalizer for DuckDB (batch processing)
- PostgresNormalizer: Async normalizer for PostgreSQL via asyncpg (small batches)

Data models:
- ConceptInfo: Unified concept metadata
- SemanticType: Semantic type info (UMLS only)
"""

from norm_toolkit.build_merged import build_merged_duckdb
from norm_toolkit.build_ontology import build_ontology_duckdb
from norm_toolkit.build_umls import build_umls_duckdb
from norm_toolkit.constants import ONTOLOGY_DF_SCHEMA
from norm_toolkit.models import ConceptInfo, SemanticType
from norm_toolkit.normalizer import DuckDBNormalizer
from norm_toolkit.normalizer_postgres import PostgresNormalizer
from norm_toolkit.utils import prepare_ontology_df, push_to_postgres

__all__ = [
    # Build functions
    "build_umls_duckdb",
    "build_ontology_duckdb",
    "build_merged_duckdb",
    # Normalizers
    "DuckDBNormalizer",
    "PostgresNormalizer",
    # Models
    "ConceptInfo",
    "SemanticType",
    # Schemas
    "ONTOLOGY_DF_SCHEMA",
    # Utils
    "prepare_ontology_df",
    "push_to_postgres",
]
