"""
Utility functions for norm_toolkit.
"""

from __future__ import annotations

import contextlib

import duckdb
import polars as pl
from lvg_norm import lvg_normalize
from tqdm import tqdm

from norm_toolkit.constants import (
    ATOMS_TABLE,
    CONCEPTS_TABLE,
    DEFS_TABLE,
    EDGES_TABLE,
    NS_TABLE,
    NW_TABLE,
    ONTOLOGY_DF_SCHEMA,
    TYPES_TABLE,
)

# All tables in the normalizer schema
ALL_TABLES = [NS_TABLE, NW_TABLE, ATOMS_TABLE, CONCEPTS_TABLE, TYPES_TABLE, DEFS_TABLE, EDGES_TABLE]


def prepare_ontology_df(
    df: pl.DataFrame,
    name_col: str = "name",
    source_col: str = "source",
    dedupe: bool = True,
) -> pl.DataFrame:
    """
    Prepare a simple name/source DataFrame for use with build_ontology_duckdb.

    Takes a minimal DataFrame with names and sources and adds all required columns
    for the ontology builder: global_identifier, identifier, pref_name, synonyms,
    description, pref_name_norm, and synonyms_norm.

    Args:
        df: Input DataFrame with at least name and source columns
        name_col: Name of the column containing concept names (default: "name")
        source_col: Name of the column containing source identifiers (default: "source")
        dedupe: Whether to deduplicate by nstring and source (default: True)

    Returns:
        DataFrame with all required columns for build_ontology_duckdb:
        - global_identifier: Unique ID (e.g., "SOURCE:0", "SOURCE:1", ...)
        - identifier: Row index as string
        - source: Source ontology name
        - pref_name: Original name
        - description: None (null)
        - pref_name_norm: First normalized form from lvg_normalize
        - synonyms: Empty list
        - synonyms_norm: Additional normalized forms (if lvg_normalize returns multiple)

    Example:
        >>> df = pl.DataFrame({
        ...     "name": ["Aspirin", "Ibuprofen"],
        ...     "source": ["DRUG", "DRUG"]
        ... })
        >>> onto_df = prepare_ontology_df(df)
        >>> build_ontology_duckdb(onto_df, "drugs.duckdb")
    """
    # Normalize names and split into pref_name_norm + synonyms_norm
    norm_results = []
    for name in tqdm(df[name_col].to_list()):
        norms = list(lvg_normalize(name) or [])
        if norms:
            pref_norm = norms[0]
            syn_norms = norms[1:] if len(norms) > 1 else []
        else:
            # Fallback: use lowercase if normalization fails
            pref_norm = name.lower() if name else ""
            syn_norms = []
        norm_results.append((pref_norm, syn_norms))

    pref_norms = [r[0] for r in norm_results]
    syn_norms = [r[1] for r in norm_results]

    df = pl.DataFrame(
        {
            "global_identifier": None,
            "identifier": None,
            "source": df[source_col],
            "pref_name": df[name_col],
            "description": None,
            "pref_name_norm": pref_norms,
            "synonyms": None,
            "synonyms_norm": syn_norms,
        },
        schema=ONTOLOGY_DF_SCHEMA,
    )
    if dedupe:
        df = df.unique(["pref_name_norm", "source"])

    df = df.with_columns(
        pl.row_index("identifier").cast(pl.Utf8),
        pl.col("synonyms").fill_null(pl.lit([])),
    ).with_columns(
        pl.concat_str([pl.col("source"), pl.col("identifier")], separator=":").alias("global_identifier"),
    )

    return df


def push_to_postgres(
    duckdb_path: str,
    postgres_dsn: str,
    schema: str = "public",
    tables: list[str] | None = None,
    drop_existing: bool = True,
    create_indexes: bool = True,
) -> None:
    """
    Push normalizer tables from a DuckDB database to PostgreSQL.

    Uses DuckDB's postgres extension for efficient bulk transfer.

    Args:
        duckdb_path: Path to source DuckDB database
        postgres_dsn: PostgreSQL connection string (e.g., "postgresql://user:pass@host:5432/db")
        schema: PostgreSQL schema to create tables in (default: "public")
        tables: List of tables to push (default: all normalizer tables)
        drop_existing: Drop existing tables before creating (default: True)
        create_indexes: Create indexes after pushing data (default: True)

    Example:
        >>> # Build DuckDB first
        >>> build_ontology_duckdb(onto_df, "my_ontology.duckdb")
        >>> # Push to PostgreSQL
        >>> push_to_postgres(
        ...     "my_ontology.duckdb",
        ...     "postgresql://user:pass@localhost:5432/normdb"
        ... )
    """
    if tables is None:
        tables = ALL_TABLES

    con = duckdb.connect(duckdb_path, read_only=True)

    try:
        # Install and load postgres extension
        con.execute("INSTALL postgres; LOAD postgres;")

        # Attach PostgreSQL database in read-write mode
        con.execute(f"ATTACH '{postgres_dsn}' AS pg (TYPE POSTGRES, READ_WRITE)")

        # Get list of tables that actually exist in the DuckDB database
        existing_tables = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        }
        tables_to_push = [t for t in tables if t in existing_tables]

        if not tables_to_push:
            print("No tables found to push")
            return

        # Push each table
        for table in tqdm(tables_to_push, desc="Pushing tables"):
            qualified_name = f"pg.{schema}.{table}" if schema else f"pg.{table}"

            if drop_existing:
                con.execute(f"DROP TABLE IF EXISTS {qualified_name}")

            # Copy table to PostgreSQL
            con.execute(f"CREATE TABLE {qualified_name} AS SELECT * FROM {table}")

        # Create indexes for query performance
        if create_indexes:
            _create_postgres_indexes(con, schema, tables_to_push)

    finally:
        con.close()


def _create_postgres_indexes(con: duckdb.DuckDBPyConnection, schema: str, tables: list[str]) -> None:
    """Create indexes on PostgreSQL tables for query performance."""
    schema_prefix = f"{schema}." if schema else ""

    index_definitions = [
        # ns table - exact string lookup
        (NS_TABLE, "ns_nstr_idx", "nstr"),
        (NS_TABLE, "ns_concept_idx", "concept_id"),
        # nw table - word lookup
        (NW_TABLE, "nw_nwd_idx", "nwd"),
        (NW_TABLE, "nw_concept_idx", "concept_id"),
        # atoms table - joins
        (ATOMS_TABLE, "atoms_concept_idx", "concept_id"),
        (ATOMS_TABLE, "atoms_name_idx", "concept_id, name_id"),
        (ATOMS_TABLE, "atoms_string_idx", "string_id"),
        # concepts table
        (CONCEPTS_TABLE, "concepts_pk_idx", "concept_id"),
        # types table
        (TYPES_TABLE, "types_concept_idx", "concept_id"),
        # defs table
        (DEFS_TABLE, "defs_concept_idx", "concept_id"),
        # edges table - hierarchy traversal
        (EDGES_TABLE, "edges_parent_idx", "parent_id"),
        (EDGES_TABLE, "edges_child_idx", "child_id"),
    ]

    for table, idx_name, columns in index_definitions:
        if table not in tables:
            continue
        # Index creation might fail if table is empty or column doesn't exist
        with contextlib.suppress(Exception):
            con.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON pg.{schema_prefix}{table} ({columns})")
