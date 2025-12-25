"""
UMLS database builder for unified normalizer.

This is a convenience wrapper around build_merged_duckdb for UMLS-only builds.
"""

from __future__ import annotations

from norm_toolkit.build_merged import build_merged_duckdb


def build_umls_duckdb(
    meta_dir: str,
    db_path: str,
    threads: int = 20,
) -> None:
    """
    Build UMLS-only DuckDB database with unified schema.

    Args:
        meta_dir: Directory containing UMLS META RRF files
        db_path: Output DuckDB database path
        threads: Number of DuckDB threads to use

    Required RRF files:
        - MRCONSO.RRF: Concept names and atoms
        - MRXNS_ENG.RRF: Normalized strings (English)
        - MRXNW_ENG.RRF: Normalized words (English)
        - MRSTY.RRF: Semantic types
        - MRRANK.RRF: Source vocabulary rankings
        - MRDEF.RRF: Definitions

    This creates a database with the same schema as build_merged_duckdb,
    but containing only UMLS data.
    """
    build_merged_duckdb(
        db_path=db_path,
        meta_dir=meta_dir,
        ontology_dfs=None,
        threads=threads,
    )
