"""
Ontology database builder for unified normalizer.

This is a convenience wrapper around build_merged_duckdb for ontology-only builds.
"""

from __future__ import annotations

import polars as pl

from norm_toolkit.build_merged import build_merged_duckdb


def build_ontology_duckdb(
    onto_df: pl.DataFrame,
    db_path: str,
    threads: int = 20,
    pref_rank: int = 3,
    syn_rank: int = 1,
) -> None:
    """
    Build ontology-only DuckDB database with unified schema.

    Args:
        onto_df: Polars DataFrame with ontology data
        db_path: Output DuckDB database path
        threads: Number of DuckDB threads to use
        pref_rank: Scoring weight for preferred names (default: 3)
        syn_rank: Scoring weight for synonyms (default: 1)

    Required columns in onto_df:
        - global_identifier: str - Unique concept ID (e.g., "CHEBI:15377")
        - identifier: str - Source-specific ID (e.g., "15377")
        - pref_name: str - Preferred/canonical name
        - synonyms: list[str] - Display synonyms
        - description: str | None - Concept definition
        - source: str - Source ontology (e.g., "CHEBI")
        - pref_name_norm: str - LVG-normalized preferred name
        - synonyms_norm: list[str] - LVG-normalized synonyms

    This creates a database with the same schema as build_merged_duckdb,
    but containing only ontology data.
    """
    build_merged_duckdb(
        db_path=db_path,
        meta_dir=None,
        ontology_dfs=[onto_df],
        threads=threads,
        pref_rank=pref_rank,
        syn_rank=syn_rank,
    )
