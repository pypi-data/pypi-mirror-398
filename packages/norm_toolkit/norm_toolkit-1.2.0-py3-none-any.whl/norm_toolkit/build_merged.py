"""
Merged database builder for unified normalizer.

Builds a single DuckDB database containing both UMLS and ontology data,
allowing simultaneous normalization across all sources.

Tables created:
- ns: Normalized string index (nstr -> concept_id, name_id)
- nw: Normalized word index (nwd -> concept_id, string_id, source)
- atoms: All atoms with unified schema
- concepts: Concept metadata
- types: Semantic types (UMLS only)
- defs: Definitions from all sources
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl

# UMLS RRF column definitions
# fmt: off
MRCONSO_COLS = ["CUI", "LAT", "TS", "LUI", "STT", "SUI", "ISPREF", "AUI", "SAUI", "SCUI", "SDUI", "SAB", "TTY", "CODE", "STR", "SRL", "SUPPRESS", "CVF"]
MRXNS_ENG_COLS = ["LAT", "NSTR", "CUI", "LUI", "SUI"]
MRXNW_ENG_COLS = ["LAT", "NWD", "CUI", "LUI", "SUI"]
MRSTY_COLS = ["CUI", "TUI", "STN", "STY", "ATUI", "CVF"]
MRRANK_COLS = ["RANK", "SAB", "TTY", "SUPPRESS"]
MRDEF_COLS = ["CUI", "AUI", "ATUI", "SATUI", "SAB", "DEF", "SUPPRESS", "CVF"]
MRREL_COLS = ["CUI1", "AUI1", "STYPE1", "REL", "CUI2", "AUI2", "STYPE2", "RELA", "RUI", "SRUI", "SAB", "SL", "RG", "DIR", "SUPPRESS", "CVF"]
# fmt: on


def build_merged_duckdb(
    db_path: str,
    meta_dir: str | None = None,
    ontology_dfs: list[pl.DataFrame] | None = None,
    edges_df: pl.DataFrame | None = None,
    filter_concepts_df: pl.DataFrame | None = None,
    threads: int = 8,
    pref_rank: int = 3,
    syn_rank: int = 1,
) -> None:
    """
    Build merged DuckDB database from UMLS and/or ontology sources.

    Args:
        db_path: Output DuckDB database path
        meta_dir: Directory containing UMLS META RRF files (optional)
        ontology_dfs: List of Polars DataFrames with ontology data (optional)
        edges_df: Hierarchy edges for ontologies (parent_id, child_id, source columns)
        filter_concepts_df: Optional DataFrame with 'global_identifier' column to filter
            which concepts to include. Only concepts matching these IDs will be included
            (applies to both UMLS CUIs and ontology global_identifiers).
        threads: Number of DuckDB threads to use
        pref_rank: Scoring weight for ontology preferred names (default: 3)
        syn_rank: Scoring weight for ontology synonyms (default: 1)

    At least one of meta_dir or ontology_dfs must be provided.

    UMLS RRF files required (if meta_dir provided):
        - MRCONSO.RRF, MRXNS_ENG.RRF, MRXNW_ENG.RRF, MRSTY.RRF, MRRANK.RRF, MRDEF.RRF
        - MRREL.RRF (optional, for hierarchy traversal)

    Ontology DataFrame columns required (if ontology_dfs provided):
        - global_identifier: str - Unique concept ID
        - identifier: str - Source-specific ID
        - pref_name: str - Preferred name
        - synonyms: list[str] - Display synonyms
        - description: str | None - Definition
        - source: str - Source ontology name
        - pref_name_norm: str - Normalized preferred name
        - synonyms_norm: list[str] - Normalized synonyms

    Edges DataFrame columns (if edges_df provided):
        - parent_id: str - Parent concept ID (broader term)
        - child_id: str - Child concept ID (narrower term)
        - source: str - Source ontology name
    """
    if not meta_dir and not ontology_dfs:
        raise ValueError("At least one of meta_dir or ontology_dfs must be provided")

    # Extract filter set if provided
    filter_ids: set[str] | None = None
    if filter_concepts_df is not None:
        if "global_identifier" not in filter_concepts_df.columns:
            raise ValueError("filter_concepts_df must have a 'global_identifier' column")
        filter_ids = set(filter_concepts_df["global_identifier"].drop_nulls().to_list())
        print(f"Filtering to {len(filter_ids):,} concepts")

    # Ensure output directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(db_path)
    con.execute(f"PRAGMA threads={threads}")

    # ==========================================================================
    # Process UMLS data (if provided)
    # ==========================================================================

    umls_atoms: pl.DataFrame | None = None
    umls_ns: pl.DataFrame | None = None
    umls_nw: pl.DataFrame | None = None
    umls_concepts: pl.DataFrame | None = None
    umls_types: pl.DataFrame | None = None
    umls_defs: pl.DataFrame | None = None
    umls_edges: pl.DataFrame | None = None

    if meta_dir:
        print("Loading UMLS data...")
        umls_atoms, umls_ns, umls_nw, umls_concepts, umls_types, umls_defs, umls_edges = _load_umls_data(
            con, meta_dir, filter_ids
        )
        print(f"  Loaded {len(umls_atoms):,} UMLS atoms")
        if umls_edges is not None:
            print(f"  Loaded {len(umls_edges):,} UMLS hierarchy edges")

    # ==========================================================================
    # Process ontology data (if provided)
    # ==========================================================================

    onto_atoms: pl.DataFrame | None = None
    onto_ns: pl.DataFrame | None = None
    onto_nw: pl.DataFrame | None = None
    onto_concepts: pl.DataFrame | None = None
    onto_defs: pl.DataFrame | None = None

    if ontology_dfs:
        print("Loading ontology data...")
        onto_atoms, onto_ns, onto_nw, onto_concepts, onto_defs = _load_ontology_data(
            ontology_dfs, pref_rank, syn_rank, filter_ids
        )
        print(f"  Loaded {len(onto_atoms):,} ontology atoms")

    # ==========================================================================
    # Merge and write tables
    # ==========================================================================

    print("Writing merged tables...")

    # Drop existing tables
    for tbl in ("atoms", "ns", "nw", "concepts", "types", "defs", "edges"):
        con.execute(f"DROP TABLE IF EXISTS {tbl};")

    # Merge atoms
    atoms_dfs = [df for df in [umls_atoms, onto_atoms] if df is not None]
    merged_atoms = pl.concat(atoms_dfs, how="vertical") if atoms_dfs else pl.DataFrame()
    _write_table(con, merged_atoms, "atoms")
    print(f"  atoms: {len(merged_atoms):,} rows")

    # Merge NS index
    ns_dfs = [df for df in [umls_ns, onto_ns] if df is not None]
    merged_ns = pl.concat(ns_dfs, how="vertical") if ns_dfs else pl.DataFrame()
    _write_table(con, merged_ns, "ns")
    print(f"  ns: {len(merged_ns):,} rows")

    # Merge NW index
    nw_dfs = [df for df in [umls_nw, onto_nw] if df is not None]
    merged_nw = pl.concat(nw_dfs, how="vertical") if nw_dfs else pl.DataFrame()
    _write_table(con, merged_nw, "nw")
    print(f"  nw: {len(merged_nw):,} rows")

    # Merge concepts
    concepts_dfs = [df for df in [umls_concepts, onto_concepts] if df is not None]
    merged_concepts = pl.concat(concepts_dfs, how="vertical") if concepts_dfs else pl.DataFrame()
    _write_table(con, merged_concepts, "concepts")
    print(f"  concepts: {len(merged_concepts):,} rows")

    # Types (UMLS only)
    merged_types = (
        umls_types
        if umls_types is not None
        else pl.DataFrame(
            schema={"concept_id": pl.Utf8, "type_id": pl.Utf8, "type_name": pl.Utf8, "type_tree": pl.Utf8}
        )
    )
    _write_table(con, merged_types, "types")
    print(f"  types: {len(merged_types):,} rows")

    # Merge definitions
    defs_dfs = [df for df in [umls_defs, onto_defs] if df is not None]
    merged_defs = pl.concat(defs_dfs, how="vertical") if defs_dfs else pl.DataFrame()
    _write_table(con, merged_defs, "defs")
    print(f"  defs: {len(merged_defs):,} rows")

    # Merge edges (hierarchy relationships)
    # Note: edges are NOT filtered by filter_concepts_df - we keep the full hierarchy
    edges_dfs = [df for df in [umls_edges, edges_df] if df is not None]
    merged_edges = pl.concat(edges_dfs, how="vertical") if edges_dfs else pl.DataFrame()
    _write_table(con, merged_edges, "edges")
    print(f"  edges: {len(merged_edges):,} rows")

    # Print size of database in GB
    size_bytes = Path(db_path).stat().st_size
    size_gb = size_bytes / (1024**3)
    print(f"  Database size: {size_gb:.2f} GB")

    # ==========================================================================
    # Create indexes
    # ==========================================================================

    print("Creating indexes...")

    # NS index - exact match lookup
    con.execute("CREATE INDEX IF NOT EXISTS idx_ns_nstr ON ns(nstr);")

    # NW index - partial match lookup
    con.execute("CREATE INDEX IF NOT EXISTS idx_nw_nwd ON nw(nwd);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_nw_nwd_source ON nw(nwd, source);")

    # Atoms - join acceleration
    con.execute("CREATE INDEX IF NOT EXISTS idx_atoms_concept_name ON atoms(concept_id, name_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_atoms_string ON atoms(string_id);")

    # Concepts - metadata lookup
    con.execute("CREATE INDEX IF NOT EXISTS idx_concepts_id ON concepts(concept_id);")

    # Types - TUI filtering and hierarchy expansion
    con.execute("CREATE INDEX IF NOT EXISTS idx_types_concept ON types(concept_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_types_type ON types(type_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_types_tree ON types(type_tree);")

    # Definitions
    con.execute("CREATE INDEX IF NOT EXISTS idx_defs_concept ON defs(concept_id);")

    if len(merged_edges) > 0:
        # Edges (hierarchy traversal)
        con.execute("CREATE INDEX IF NOT EXISTS idx_edges_parent ON edges(parent_id);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_edges_parent_source ON edges(parent_id, source);")

    # ==========================================================================
    # Finalize
    # ==========================================================================

    con.execute("ANALYZE;")
    con.close()

    print(f"Built merged DuckDB at {db_path}")


def _write_table(con: duckdb.DuckDBPyConnection, df: pl.DataFrame, table_name: str) -> None:
    """Write a Polars DataFrame to DuckDB."""
    if len(df) == 0:
        # Create empty table with schema
        cols = ", ".join(f"{c} VARCHAR" for c in df.columns) if df.columns else "dummy VARCHAR"
        con.execute(f"CREATE TABLE {table_name} ({cols});")
    else:
        con.register("_tmp", df.to_arrow())
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _tmp;")
        con.unregister("_tmp")


def _load_umls_data(
    con: duckdb.DuckDBPyConnection,
    meta_dir: str,
    filter_ids: set[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame | None]:
    """
    Load UMLS data and transform to unified schema.

    Args:
        con: DuckDB connection
        meta_dir: Directory containing UMLS META RRF files
        filter_ids: Optional set of CUIs to filter to (only include these concepts)

    Returns: (atoms, ns, nw, concepts, types, defs, edges)
    """
    meta = Path(meta_dir)

    paths = {
        "MRCONSO": meta / "MRCONSO.RRF",
        "MRXNS_ENG": meta / "MRXNS_ENG.RRF",
        "MRXNW_ENG": meta / "MRXNW_ENG.RRF",
        "MRSTY": meta / "MRSTY.RRF",
        "MRRANK": meta / "MRRANK.RRF",
        "MRDEF": meta / "MRDEF.RRF",
    }

    # MRREL is optional (for hierarchy traversal)
    mrrel_path = meta / "MRREL.RRF"
    has_mrrel = mrrel_path.exists()

    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing {name}: {path}")

    # Load raw RRF tables into temporary DuckDB tables
    con.execute(f"CREATE TEMP TABLE _mrconso({', '.join(c + ' VARCHAR' for c in MRCONSO_COLS)});")
    con.execute(f"CREATE TEMP TABLE _mrxns_eng({', '.join(c + ' VARCHAR' for c in MRXNS_ENG_COLS)});")
    con.execute(f"CREATE TEMP TABLE _mrxnw_eng({', '.join(c + ' VARCHAR' for c in MRXNW_ENG_COLS)});")
    con.execute(f"CREATE TEMP TABLE _mrsty({', '.join(c + ' VARCHAR' for c in MRSTY_COLS)});")
    con.execute(f"CREATE TEMP TABLE _mrrank({', '.join(c + ' VARCHAR' for c in MRRANK_COLS)});")
    con.execute(f"CREATE TEMP TABLE _mrdef({', '.join(c + ' VARCHAR' for c in MRDEF_COLS)});")

    con.execute(f"COPY _mrconso FROM '{paths['MRCONSO']}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")
    con.execute(f"COPY _mrxns_eng FROM '{paths['MRXNS_ENG']}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")
    con.execute(f"COPY _mrxnw_eng FROM '{paths['MRXNW_ENG']}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")
    con.execute(f"COPY _mrsty FROM '{paths['MRSTY']}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")
    con.execute(f"COPY _mrrank FROM '{paths['MRRANK']}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")
    con.execute(f"COPY _mrdef FROM '{paths['MRDEF']}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")

    # Load MRREL if available
    if has_mrrel:
        con.execute(f"CREATE TEMP TABLE _mrrel({', '.join(c + ' VARCHAR' for c in MRREL_COLS)});")
        con.execute(f"COPY _mrrel FROM '{mrrel_path}' (DELIMITER '|', HEADER false, QUOTE '', ESCAPE '');")

    # Convert RANK to integer
    con.execute("ALTER TABLE _mrrank ALTER COLUMN RANK TYPE INTEGER;")

    # Register filter table if provided
    cui_filter_clause = ""
    cui_filter_clause_ns = ""
    cui_filter_clause_nw = ""
    cui_filter_clause_sty = ""
    cui_filter_clause_def = ""
    if filter_ids is not None:
        filter_df = pl.DataFrame({"CUI": list(filter_ids)})
        con.register("_cui_filter", filter_df.to_arrow())
        cui_filter_clause = " AND mc.CUI IN (SELECT CUI FROM _cui_filter)"
        cui_filter_clause_ns = " AND CUI IN (SELECT CUI FROM _cui_filter)"
        cui_filter_clause_nw = " AND nw.CUI IN (SELECT CUI FROM _cui_filter)"
        cui_filter_clause_sty = " WHERE CUI IN (SELECT CUI FROM _cui_filter)"
        cui_filter_clause_def = " AND CUI IN (SELECT CUI FROM _cui_filter)"

    # Build enriched atoms (English, non-suppressed, with pre-joined rank)
    # Normalize UMLS ranks to 0-10 scale to be comparable with ontology ranks (1-3)
    # MRRANK values typically range 0-1000+, so divide by 100
    atoms_df = con.execute(f"""
        SELECT
            mc.CUI AS concept_id,
            mc.LUI AS name_id,
            mc.SUI AS string_id,
            mc.CUI AS identifier,
            mc.STR AS str,
            mc.SAB AS source,
            mc.TTY AS name_type,
            mc.ISPREF AS ispref,
            mc.STT AS stt,
            ROUND(COALESCE(mr.RANK, 0) / 100.0)::INTEGER AS rank
        FROM _mrconso mc
        LEFT JOIN _mrrank mr ON mr.SAB = mc.SAB AND mr.TTY = mc.TTY
        WHERE mc.LAT = 'ENG'
          AND mc.SUPPRESS = 'N'
          AND COALESCE(mr.SUPPRESS, 'N') = 'N'{cui_filter_clause}
    """).pl()

    # Build NS index (normalized string -> concept, name)
    ns_df = con.execute(f"""
        SELECT DISTINCT
            NSTR AS nstr,
            CUI AS concept_id,
            LUI AS name_id
        FROM _mrxns_eng
        WHERE 1=1{cui_filter_clause_ns}
    """).pl()

    # Build NW index (word -> concept, string, source)
    # Note: UMLS mrxnw_eng doesn't have source, so we join to get it
    nw_df = con.execute(f"""
        SELECT DISTINCT
            nw.NWD AS nwd,
            nw.CUI AS concept_id,
            nw.SUI AS string_id,
            mc.SAB AS source
        FROM _mrxnw_eng nw
        JOIN _mrconso mc ON mc.CUI = nw.CUI AND mc.SUI = nw.SUI
        WHERE mc.LAT = 'ENG' AND mc.SUPPRESS = 'N'{cui_filter_clause_nw}
    """).pl()

    # Build concepts (distinct CUIs)
    # Note: We don't pre-compute pref_name here; concept_info() handles that
    # Cast NULLs to VARCHAR to match ontology schema for concat
    concepts_df = con.execute(f"""
        SELECT DISTINCT
            mc.CUI AS concept_id,
            mc.CUI AS identifier,
            NULL::VARCHAR AS source,
            NULL::VARCHAR AS pref_name,
            NULL::VARCHAR AS description
        FROM _mrconso mc
        WHERE mc.LAT = 'ENG' AND mc.SUPPRESS = 'N'{cui_filter_clause}
    """).pl()

    # Build types (semantic types)
    types_df = con.execute(f"""
        SELECT DISTINCT
            CUI AS concept_id,
            TUI AS type_id,
            STY AS type_name,
            STN AS type_tree
        FROM _mrsty{cui_filter_clause_sty}
    """).pl()

    # Build definitions
    defs_df = con.execute(f"""
        SELECT
            CUI AS concept_id,
            SAB AS source,
            DEF AS def_text
        FROM _mrdef
        WHERE COALESCE(SUPPRESS, 'N') = 'N'
          AND DEF IS NOT NULL AND DEF <> ''{cui_filter_clause_def}
    """).pl()

    # Build edges from MRREL (hierarchy relationships)
    # CHD/RN: CUI1 is parent of CUI2 (direct child/narrower)
    # PAR/RB: CUI2 is parent of CUI1 (reversed - CUI1 is child/narrower)
    # Note: edges are NOT filtered by filter_ids - we keep the full hierarchy
    edges_df: pl.DataFrame | None = None
    if has_mrrel:
        edges_df = con.execute("""
            SELECT DISTINCT parent_id, child_id, source
            FROM (
                -- CHD (child) and RN (narrower): CUI1 -> CUI2
                SELECT
                    CUI1 AS parent_id,
                    CUI2 AS child_id,
                    SAB AS source
                FROM _mrrel
                WHERE REL IN ('CHD', 'RN')
                  AND COALESCE(SUPPRESS, 'N') = 'N'

                UNION

                -- PAR (parent) and RB (broader): CUI2 -> CUI1 (reversed)
                SELECT
                    CUI2 AS parent_id,
                    CUI1 AS child_id,
                    SAB AS source
                FROM _mrrel
                WHERE REL IN ('PAR', 'RB')
                  AND COALESCE(SUPPRESS, 'N') = 'N'
            ) combined
            WHERE parent_id <> child_id
        """).pl()

    # Clean up temp tables
    for tbl in ("_mrconso", "_mrxns_eng", "_mrxnw_eng", "_mrsty", "_mrrank", "_mrdef", "_mrrel"):
        con.execute(f"DROP TABLE IF EXISTS {tbl};")
    if filter_ids is not None:
        con.unregister("_cui_filter")

    return atoms_df, ns_df, nw_df, concepts_df, types_df, defs_df, edges_df


def _load_ontology_data(
    ontology_dfs: list[pl.DataFrame],
    pref_rank: int,
    syn_rank: int,
    filter_ids: set[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """
    Load ontology data and transform to unified schema.

    Args:
        ontology_dfs: List of Polars DataFrames with ontology data
        pref_rank: Scoring weight for preferred names
        syn_rank: Scoring weight for synonyms
        filter_ids: Optional set of global_identifiers to filter to

    Returns: (atoms, ns, nw, concepts, defs)
    """
    # Combine all ontology DataFrames
    combined = pl.concat(ontology_dfs, how="vertical")

    # Filter to specified concepts if filter_ids provided
    if filter_ids is not None:
        combined = combined.filter(pl.col("global_identifier").is_in(filter_ids))

    # Normalize columns
    combined = combined.with_columns(
        pl.col("synonyms").cast(pl.List(pl.Utf8)).fill_null([]),
        pl.col("synonyms_norm").cast(pl.List(pl.Utf8)).fill_null([]),
    )

    # Build concepts table
    concepts_df = combined.select(
        pl.col("global_identifier").alias("concept_id"),
        "identifier",
        "source",
        "pref_name",
        "description",
    ).unique(subset=["concept_id", "source"])

    # Build definitions from descriptions
    defs_df = (
        combined.filter(pl.col("description").is_not_null() & (pl.col("description") != ""))
        .select(
            pl.col("global_identifier").alias("concept_id"),
            "source",
            pl.col("description").alias("def_text"),
        )
        .unique(subset=["concept_id", "source"])
    )

    # Build atoms: preferred names
    pref_df = combined.select(
        pl.col("global_identifier").alias("concept_id"),
        "identifier",
        "source",
        pl.lit("pref").alias("name_type"),
        pl.lit("Y").alias("ispref"),
        pl.lit(None).cast(pl.Utf8).alias("stt"),  # NULL for ontology
        pl.col("pref_name_norm").alias("nstr"),
        pl.col("pref_name").alias("str"),
        pl.lit(pref_rank).alias("rank"),
    ).filter(pl.col("nstr").is_not_null() & (pl.col("nstr") != ""))

    # Build atoms: synonyms
    # Note: Using synonyms_norm for both nstr and str since we can't align lists
    syn_df = (
        combined.explode("synonyms_norm")
        .select(
            pl.col("global_identifier").alias("concept_id"),
            "identifier",
            "source",
            pl.lit("syn").alias("name_type"),
            pl.lit("N").alias("ispref"),
            pl.lit(None).cast(pl.Utf8).alias("stt"),
            pl.col("synonyms_norm").alias("nstr"),
            pl.col("synonyms_norm").alias("str"),
            pl.lit(syn_rank).alias("rank"),
        )
        .filter(pl.col("nstr").is_not_null() & (pl.col("nstr") != ""))
    )

    # Combine and deduplicate atoms
    names_df = pl.concat([pref_df, syn_df], how="vertical").unique(
        subset=["concept_id", "source", "name_type", "nstr", "str"]
    )

    # Generate name_id and string_id
    atoms_df = names_df.with_columns(
        # name_id = hash of (concept_id, nstr) - groups variants with same normalized form
        pl.concat_str([pl.col("concept_id"), pl.lit("|"), pl.col("nstr")]).hash().cast(pl.Utf8).alias("name_id"),
        # string_id = hash of (concept_id, str) - unique per display string
        pl.concat_str([pl.col("concept_id"), pl.lit("|"), pl.col("str")]).hash().cast(pl.Utf8).alias("string_id"),
    )

    # Build NS index (before we drop nstr from atoms_df)
    ns_df = atoms_df.select("nstr", "concept_id", "name_id").unique(subset=["nstr", "concept_id", "name_id"])

    # Reorder columns to match merged schema (drop nstr since it's in ns_df)
    atoms_df = atoms_df.select(
        "concept_id", "name_id", "string_id", "identifier", "str", "source", "name_type", "ispref", "stt", "rank"
    )

    # Build NW index (word-level)
    nw_base = names_df.with_columns(
        pl.concat_str([pl.col("concept_id"), pl.lit("|"), pl.col("str")]).hash().cast(pl.Utf8).alias("string_id"),
    )

    nw_df = (
        nw_base.with_columns(pl.col("nstr").fill_null("").str.strip_chars().str.split(" ").alias("tokens"))
        .explode("tokens")
        .filter(pl.col("tokens") != "")
        .select(
            pl.col("tokens").alias("nwd"),
            "concept_id",
            "string_id",
            "source",
        )
        .unique(subset=["nwd", "concept_id", "string_id", "source"])
    )

    return atoms_df, ns_df, nw_df, concepts_df, defs_df
