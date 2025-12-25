"""
Unified normalizer for biomedical concept normalization.

Works with DuckDB databases built by build_umls_duckdb, build_ontology_duckdb,
or build_merged_duckdb. All use a standardized schema.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping, Sequence

import duckdb
import polars as pl
from lvg_norm import lvg_normalize

from norm_toolkit.constants import (
    ATOMS_TABLE,
    DEFAULT_PREFER_TTYS,
    DEFS_TABLE,
    EDGES_TABLE,
    EXACT_BUMP,
    HIT_STRUCT_TYPE,
    ISPREF_WEIGHT,
    NS_TABLE,
    NW_TABLE,
    RANK_MULTIPLIER,
    STT_WEIGHT,
    TTY_WEIGHT,
    TYPES_TABLE,
)
from norm_toolkit.models import ConceptInfo, SemanticType


class DuckDBNormalizer:
    """
    High-throughput normalizer using DuckDB.

    Works with databases built by any of the build functions. Uses exact match
    via normalized string index and optional partial match via word-level index.
    """

    def __init__(
        self,
        db_path: str,
        threads: int = 8,
    ) -> None:
        """
        Initialize the normalizer.

        Args:
            db_path: Path to DuckDB database file
            threads: Number of DuckDB threads to use
        """
        self.db_path = db_path
        self.con = duckdb.connect(db_path, read_only=True)
        self.con.execute(f"PRAGMA threads={threads}")

        # Detect database capabilities
        self._has_types = self._table_has_rows(TYPES_TABLE)
        self._has_defs = self._table_has_rows(DEFS_TABLE)
        self._has_edges = self._table_has_rows(EDGES_TABLE)
        self._has_stt = self._column_has_values(ATOMS_TABLE, "stt")

    def _table_has_rows(self, table: str) -> bool:
        """Check if a table exists and has rows."""
        try:
            result = self.con.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
            return result is not None
        except Exception:
            return False

    def _column_has_values(self, table: str, column: str) -> bool:
        """Check if a column has any non-null values."""
        try:
            result = self.con.execute(f"SELECT 1 FROM {table} WHERE {column} IS NOT NULL LIMIT 1").fetchone()
            return result is not None
        except Exception:
            return False

    def _lookup(
        self,
        q_to_nstrs: Mapping[str, Sequence[str]],
        all_queries: Sequence[str],
        prefer_ttys: list[str] | None,
        filter_sources: list[str] | None,
        exclude_sources: list[str] | None,
        *,
        top_k: int = 25,
        allow_partial: bool = True,
        min_coverage: float = 0.6,
        min_word_hits: int | None = None,
        coverage_weight: int = 25,
    ) -> pl.DataFrame:
        """
        Core lookup via exact + partial match paths.

        Returns DataFrame with columns: input_string, hits (list of structs)
        """
        top_k = max(1, int(top_k))

        # Flatten q_to_nstrs to rows
        rows: list[tuple[str, str]] = []
        for q, nstrs in q_to_nstrs.items():
            for nstr in dict.fromkeys(nstrs):
                if nstr:
                    rows.append((q, nstr))

        if not rows:
            return pl.DataFrame({"input_string": all_queries, "hits": [[] for _ in all_queries]}).cast(
                {"hits": pl.List(HIT_STRUCT_TYPE)}
            )

        qmap_df = pl.DataFrame(rows, schema=["Q", "NSTR"], orient="row")
        self.con.register("qmap", qmap_df.to_arrow())

        # Word-level table for partial path
        if allow_partial:
            word_rows = [(q, n, w) for q, n in rows for w in dict.fromkeys(n.split()) if w]
            qwords_df = pl.DataFrame(word_rows, schema=["Q", "NSTR", "NWD"], orient="row")
            self.con.register("qwords", qwords_df.to_arrow())

        # Build preference clauses
        tty_join = ""
        tty_bump_expr = "0"
        if prefer_ttys:
            tty_vals = ", ".join(f"('{t}')" for t in prefer_ttys)
            tty_join = f"LEFT JOIN (VALUES {tty_vals}) AS pt(tty) ON a.name_type = pt.tty"
            tty_bump_expr = "CASE WHEN pt.tty IS NULL THEN 0 ELSE 1 END"

        # Source filtering (include and exclude)
        source_filter_exprs = []
        nw_filter_clauses = []
        if filter_sources:
            filt_vals = ", ".join(f"'{src}'" for src in filter_sources)
            source_filter_exprs.append(f"a.source IN ({filt_vals})")
            nw_filter_clauses.append(f"nw.source IN ({filt_vals})")
        if exclude_sources:
            excl_vals = ", ".join(f"'{src}'" for src in exclude_sources)
            source_filter_exprs.append(f"a.source NOT IN ({excl_vals})")
            nw_filter_clauses.append(f"nw.source NOT IN ({excl_vals})")
        nw_filter_clause = (" AND " + " AND ".join(nw_filter_clauses)) if nw_filter_clauses else ""

        # Build WHERE clause from source filters
        combined_where = f"WHERE {' AND '.join(source_filter_exprs)}" if source_filter_exprs else ""

        # STT bump
        stt_bump_expr = "CASE WHEN a.stt='PF' THEN 1 ELSE 0 END" if self._has_stt else "0"

        # Scoring constants
        min_hits_sql = str(min_word_hits) if min_word_hits is not None else "0"
        cov_sql = f"{min_coverage:.6f}"

        # Build exact match CTE
        exact_cte = f"""
cand_exact AS (
    SELECT
        q.Q, q.NSTR,
        a.concept_id,
        a.identifier,
        a.str,
        a.source,
        a.name_type,
        a.ispref,
        a.rank,
        CASE WHEN a.ispref='Y' THEN 1 ELSE 0 END AS ispref_bump,
        {stt_bump_expr} AS stt_bump,
        {tty_bump_expr} AS tty_bump,
        1.0 AS coverage
    FROM qmap q
    JOIN {NS_TABLE} ns ON ns.nstr = q.NSTR
    JOIN {ATOMS_TABLE} a
        ON a.concept_id = ns.concept_id
        AND a.name_id = ns.name_id
    {tty_join}
    {combined_where}
),
dedup_exact AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY Q, concept_id
            ORDER BY rank DESC, ispref_bump DESC, stt_bump DESC, tty_bump DESC, concept_id
        ) AS rnc
    FROM cand_exact
),
scored_exact AS (
    SELECT
        Q, NSTR, concept_id, identifier, str, source, name_type, ispref, rank,
        (rank*{RANK_MULTIPLIER} + ispref_bump*{ISPREF_WEIGHT} + stt_bump*{STT_WEIGHT}
            + tty_bump*{TTY_WEIGHT} + {EXACT_BUMP} + ROUND(coverage * {coverage_weight}))::INTEGER AS total_score,
        TRUE AS is_exact
    FROM dedup_exact
    WHERE rnc = 1
)
"""

        # Build partial match CTE (if enabled)
        partial_cte = ""
        union_partial = ""
        if allow_partial:
            partial_cte = f"""
,
qn AS (
    SELECT Q, NSTR, COUNT(DISTINCT NWD) AS need
    FROM qwords
    GROUP BY Q, NSTR
),
hits AS (
    SELECT qw.Q, qw.NSTR, nw.string_id, nw.concept_id,
           COUNT(DISTINCT qw.NWD) AS hits
    FROM qwords qw
    JOIN {NW_TABLE} nw ON nw.nwd = qw.NWD{nw_filter_clause}
    GROUP BY qw.Q, qw.NSTR, nw.string_id, nw.concept_id
),
good AS (
    SELECT h.Q, h.NSTR, h.string_id, h.concept_id, h.hits, qn.need,
        CAST(h.hits AS DOUBLE)/NULLIF(qn.need,0) AS coverage
    FROM hits h
    JOIN qn ON qn.Q = h.Q AND qn.NSTR = h.NSTR
    WHERE h.hits >= GREATEST({min_hits_sql}, CAST(CEIL(qn.need * {cov_sql}) AS INTEGER))
),
cand_partial AS (
    SELECT
        g.Q, g.NSTR,
        a.concept_id,
        a.identifier,
        a.str,
        a.source,
        a.name_type,
        a.ispref,
        a.rank,
        CASE WHEN a.ispref='Y' THEN 1 ELSE 0 END AS ispref_bump,
        {stt_bump_expr} AS stt_bump,
        {tty_bump_expr} AS tty_bump,
        COALESCE(g.coverage, 0.0) AS coverage
    FROM good g
    JOIN {ATOMS_TABLE} a ON a.string_id = g.string_id
    {tty_join}
    {combined_where}
),
dedup_partial AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY Q, concept_id
            ORDER BY rank DESC, ispref_bump DESC, stt_bump DESC, tty_bump DESC, concept_id
        ) AS rnc
    FROM cand_partial
),
scored_partial AS (
    SELECT
        Q, NSTR, concept_id, identifier, str, source, name_type, ispref, rank,
        (rank*{RANK_MULTIPLIER} + ispref_bump*{ISPREF_WEIGHT} + stt_bump*{STT_WEIGHT}
            + tty_bump*{TTY_WEIGHT} + ROUND(coverage * {coverage_weight}))::INTEGER AS total_score,
        FALSE AS is_exact
    FROM dedup_partial
    WHERE rnc = 1
)
"""
            union_partial = "UNION ALL SELECT * FROM scored_partial"

        # Final aggregation SQL
        sql = f"""
WITH
{exact_cte}
{partial_cte}
,
scored AS (
    SELECT * FROM scored_exact
    {union_partial}
),
dedup_concept AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY Q, concept_id ORDER BY total_score DESC) AS rcid
    FROM scored
),
best AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY Q ORDER BY total_score DESC, concept_id) AS rn
    FROM dedup_concept
    WHERE rcid = 1
),
topk AS (
    SELECT * FROM best WHERE rn <= {top_k}
),
agg AS (
    SELECT
        Q,
        LIST({{
            'global_identifier': concept_id,
            'identifier': identifier,
            'nstr': NSTR,
            'name': str,
            'source': source,
            'name_type': name_type,
            'score': rank::BIGINT,
            'total_score': total_score::BIGINT,
            'match_type': CASE WHEN is_exact THEN 'exact' ELSE 'partial' END
        }} ORDER BY total_score DESC, concept_id) AS hits
    FROM topk
    GROUP BY Q
)
SELECT
    aq.Q AS input_string,
    agg.hits
FROM allq aq
LEFT JOIN agg ON agg.Q = aq.Q;
"""

        # Register all queries for preserving order
        allq_df = pl.DataFrame({"Q": all_queries})
        self.con.register("allq", allq_df.to_arrow())

        out = self.con.execute(sql).pl()
        out = out.with_columns(pl.col("hits").fill_null([]).cast(pl.List(HIT_STRUCT_TYPE)))

        with contextlib.suppress(Exception):
            self.con.unregister("qmap")
            self.con.unregister("allq")
            if allow_partial:
                self.con.unregister("qwords")

        return out

    def normalize(
        self,
        strings: Sequence[str],
        synonyms: Mapping[str, Sequence[str]] | None = None,
        top_k: int = 25,
        prefer_ttys: list[str] | None = None,
        filter_sources: list[str] | None = None,
        exclude_sources: list[str] | None = None,
        allow_partial: bool = True,
        min_coverage: float = 0.6,
        min_word_hits: int | None = None,
        coverage_weight: int = 25,
    ) -> pl.DataFrame:
        """
        Normalize input strings to ranked concepts.

        Args:
            strings: Input strings to normalize
            synonyms: Optional mapping of input strings to their synonyms.
                Synonyms are normalized and used alongside the main string
                to improve matching. Results are still keyed by the original
                input string.
            top_k: Maximum number of results per query
            prefer_ttys: Term types to prefer (e.g., ["PT", "MH"])
            filter_sources: Restrict to these sources (include only)
            exclude_sources: Exclude these sources
            allow_partial: Enable word-overlap partial matching
            min_coverage: Minimum fraction of query words that must match
            min_word_hits: Minimum absolute word hits required
            coverage_weight: Weight for coverage in scoring

        Returns:
            DataFrame with columns: input_string, hits (list of match structs),
            and synonyms (list of strings) if synonyms were provided.
        """
        # Apply defaults
        if prefer_ttys is None:
            prefer_ttys = DEFAULT_PREFER_TTYS

        # Build normalized string map
        q_to_nstrs: dict[str, list[str]] = {}
        for s in strings:
            nstrs = list(lvg_normalize(s) or [])
            # Add normalized forms of synonyms
            if synonyms and s in synonyms:
                for syn in synonyms[s]:
                    syn_nstrs = list(lvg_normalize(syn) or [])
                    nstrs.extend(syn_nstrs)
            q_to_nstrs[s] = nstrs

        result = self._lookup(
            q_to_nstrs=q_to_nstrs,
            all_queries=list(strings),
            prefer_ttys=prefer_ttys,
            filter_sources=filter_sources,
            exclude_sources=exclude_sources,
            top_k=top_k,
            allow_partial=allow_partial,
            min_coverage=min_coverage,
            min_word_hits=min_word_hits,
            coverage_weight=coverage_weight,
        )

        # Add synonyms column if synonyms were provided
        if synonyms:
            syn_list = [list(synonyms.get(s, [])) for s in strings]
            result = result.with_columns(pl.Series("synonyms", syn_list))

        return result

    def concept_info(
        self,
        concept_ids: Sequence[str],
        prefer_ttys: list[str] | None = None,
        prefer_def_sources: list[str] | None = None,
    ) -> dict[str, ConceptInfo]:
        """
        Get detailed information for concepts.

        Args:
            concept_ids: List of concept IDs
            prefer_ttys: Preferred term types
            prefer_def_sources: Preferred sources for definitions

        Returns:
            Dict mapping concept_id to ConceptInfo
        """
        if not concept_ids:
            return {}

        id_list = list(dict.fromkeys(concept_ids))
        id_df = pl.DataFrame({"concept_id": id_list})
        self.con.register("idmap", id_df.to_arrow())

        # Initialize results with defaults
        res: dict[str, ConceptInfo] = {}
        for cid in id_list:
            res[cid] = ConceptInfo(
                concept_id=cid,
                identifier=None,
                source=None,
                preferred_name=None,
                name_type=None,
                description=None,
                def_source=None,
                synonyms=[],
                semantic_types=[],
            )

        self._populate_concept_info(res, prefer_ttys, prefer_def_sources)

        with contextlib.suppress(Exception):
            self.con.unregister("idmap")

        return res

    def _populate_concept_info(
        self,
        res: dict[str, ConceptInfo],
        prefer_ttys: list[str] | None,
        prefer_def_sources: list[str] | None,
    ) -> None:
        """Populate ConceptInfo for all concepts."""
        if prefer_ttys is None:
            prefer_ttys = DEFAULT_PREFER_TTYS

        # Build preference clauses
        tty_join = def_pref_join = ""
        tty_bump = def_pref_bump = "0"

        if prefer_ttys:
            tty_vals = ", ".join(f"('{t}')" for t in prefer_ttys)
            tty_join = f"LEFT JOIN (VALUES {tty_vals}) AS pt(tty) ON a.name_type = pt.tty"
            tty_bump = "CASE WHEN pt.tty IS NULL THEN 0 ELSE 1 END"

        if prefer_def_sources:
            def_vals = ", ".join(f"('{src}')" for src in prefer_def_sources)
            def_pref_join = f"LEFT JOIN (VALUES {def_vals}) AS pds(sab) ON d.source = pds.sab"
            def_pref_bump = "CASE WHEN pds.sab IS NULL THEN 0 ELSE 1 END"

        stt_bump = "CASE WHEN a.stt='PF' THEN 1 ELSE 0 END" if self._has_stt else "0"

        # Main query for names
        sql = f"""
WITH
name_cand AS (
    SELECT
        c.concept_id, a.str, a.source AS sab,
        a.name_type AS tty, a.ispref, a.stt, a.rank,
        CASE WHEN a.ispref='Y' THEN 1 ELSE 0 END AS ispref_bump,
        {stt_bump} AS stt_bump,
        {tty_bump} AS tty_bump,
        a.identifier
    FROM idmap c
    JOIN {ATOMS_TABLE} a ON a.concept_id = c.concept_id
    {tty_join}
),
name_best AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY concept_id
            ORDER BY tty_bump DESC, ispref_bump DESC, stt_bump DESC, rank DESC, str
        ) AS rn
    FROM name_cand
),
chosen AS (
    SELECT concept_id, str AS preferred_name, sab AS name_sab, tty AS name_tty, identifier
    FROM name_best WHERE rn=1
),

syn_cand AS (
    SELECT
        c.concept_id, a.str, a.source AS sab,
        a.name_type AS tty, a.ispref, a.stt, a.rank,
        CASE WHEN a.ispref='Y' THEN 1 ELSE 0 END AS ispref_bump,
        {stt_bump} AS stt_bump,
        {tty_bump} AS tty_bump
    FROM idmap c
    JOIN {ATOMS_TABLE} a ON a.concept_id = c.concept_id
    {tty_join}
),
syn_rank AS (
    SELECT sc.*,
        ROW_NUMBER() OVER (
            PARTITION BY sc.concept_id, LOWER(sc.str)
            ORDER BY sc.tty_bump DESC, sc.ispref_bump DESC,
                sc.stt_bump DESC, sc.rank DESC, sc.str
        ) AS rstr
    FROM syn_cand sc
),
syn_best_uniq AS (
    SELECT s.concept_id, s.str, s.tty_bump, s.ispref_bump, s.stt_bump, s.rank
    FROM syn_rank s
    LEFT JOIN chosen ch ON ch.concept_id = s.concept_id
    WHERE s.rstr = 1 AND NOT (s.str = ch.preferred_name)
),
syn_agg AS (
    SELECT concept_id,
        ARRAY_AGG(
            str ORDER BY
                tty_bump DESC, ispref_bump DESC, stt_bump DESC, rank DESC, str
        ) AS synonyms
    FROM syn_best_uniq
    GROUP BY concept_id
)

SELECT c.concept_id,
    ch.preferred_name, ch.name_sab, ch.name_tty, ch.identifier,
    sa.synonyms
FROM idmap c
LEFT JOIN chosen   ch ON ch.concept_id = c.concept_id
LEFT JOIN syn_agg  sa ON sa.concept_id = c.concept_id
ORDER BY c.concept_id;
        """

        out = self.con.execute(sql).pl()

        for row in out.iter_rows(named=True):
            cid = row["concept_id"]
            ent = res[cid]

            if row["preferred_name"] is not None:
                ent.preferred_name = row["preferred_name"]
                ent.source = row["name_sab"]
                ent.name_type = row["name_tty"]
                ent.identifier = row["identifier"]

            synonyms = row.get("synonyms")
            if isinstance(synonyms, list):
                ent.synonyms = list(dict.fromkeys(synonyms))

        # Definitions (if available)
        if self._has_defs:
            self._populate_definitions(res, def_pref_join, def_pref_bump)

        # Semantic types (if available)
        if self._has_types:
            self._populate_semantic_types(res)

    def _populate_definitions(
        self,
        res: dict[str, ConceptInfo],
        def_pref_join: str,
        def_pref_bump: str,
    ) -> None:
        """Populate definitions for concepts."""
        sql = f"""
WITH
def_cand AS (
    SELECT
        d.concept_id, d.source AS sab, d.def_text,
        {def_pref_bump} AS def_pref_bump,
        length(d.def_text) AS def_len
    FROM {DEFS_TABLE} d
    JOIN idmap c ON c.concept_id = d.concept_id
    {def_pref_join}
),
def_best AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY concept_id
            ORDER BY def_pref_bump DESC, def_len DESC
        ) AS drn
    FROM def_cand
)
SELECT concept_id, def_text, sab AS def_sab
FROM def_best
WHERE drn = 1;
        """

        out = self.con.execute(sql).pl()
        for row in out.iter_rows(named=True):
            cid = row["concept_id"]
            if cid in res and row["def_text"]:
                res[cid].description = row["def_text"]
                res[cid].def_source = row["def_sab"]

    def _populate_semantic_types(self, res: dict[str, ConceptInfo]) -> None:
        """Populate semantic types for concepts."""
        sql = f"""
SELECT DISTINCT t.concept_id, t.type_id, t.type_name, t.type_tree
FROM {TYPES_TABLE} t
JOIN idmap c ON c.concept_id = t.concept_id
ORDER BY t.concept_id, t.type_tree, t.type_id;
        """

        out = self.con.execute(sql).pl()
        for row in out.iter_rows(named=True):
            cid = row["concept_id"]
            if cid in res and row["type_id"] and row["type_name"]:
                res[cid].semantic_types.append(SemanticType(type_id=row["type_id"], type_name=row["type_name"]))

    def concept_semantic_types(self, concept_ids: Sequence[str]) -> dict[str, list[dict[str, str]]]:
        """
        Get semantic types for concepts.

        Returns dict mapping concept_id to list of {"tui": ..., "sty": ...}
        """
        if not self._has_types or not concept_ids:
            return {cid: [] for cid in concept_ids}

        id_list = list(dict.fromkeys(concept_ids))
        id_df = pl.DataFrame({"concept_id": id_list})
        self.con.register("idmap", id_df.to_arrow())

        sql = f"""
SELECT DISTINCT t.concept_id, t.type_id AS tui, t.type_name AS sty, t.type_tree
FROM {TYPES_TABLE} t
JOIN idmap c ON c.concept_id = t.concept_id
ORDER BY t.concept_id, t.type_tree, t.type_id;
        """

        out = self.con.execute(sql).pl()

        with contextlib.suppress(Exception):
            self.con.unregister("idmap")

        res: dict[str, list[dict[str, str]]] = {cid: [] for cid in id_list}
        for row in out.iter_rows(named=True):
            res[row["concept_id"]].append({"tui": row["tui"], "sty": row["sty"]})

        return res

    def get_narrower_concepts(
        self,
        concept_id: str,
        max_depth: int | None = 10,
        filter_sources: list[str] | None = None,
    ) -> list[str]:
        """
        Get all narrower (descendant) concept IDs using recursive traversal.

        Uses the hierarchy edges to walk down the tree/DAG from the given concept.

        Args:
            concept_id: Starting concept ID (broader term)
            max_depth: Maximum depth to traverse (1 = direct children only, None = all descendants)
            filter_sources: Only follow edges from these sources (e.g., ["SNOMEDCT_US"])

        Returns:
            List of descendant concept IDs (excludes the starting concept)
        """
        if not self._has_edges:
            return []

        # Build source filter clause
        source_filter = ""
        if filter_sources:
            sources_sql = ", ".join(f"'{src}'" for src in filter_sources)
            source_filter = f" AND e.source IN ({sources_sql})"

        # DuckDB recursive CTE
        query = f"""
        WITH RECURSIVE walk(concept_id, depth) AS (
            SELECT $1::VARCHAR, 0

            UNION ALL

            SELECT e.child_id, w.depth + 1
            FROM walk w
            JOIN {EDGES_TABLE} e ON e.parent_id = w.concept_id
            WHERE ($2 IS NULL OR w.depth < $2){source_filter}
        )
        SELECT DISTINCT concept_id
        FROM walk
        WHERE concept_id != $1
        """

        result = self.con.execute(query, [concept_id, max_depth]).fetchall()
        return [r[0] for r in result]

    def close(self) -> None:
        """Close the database connection."""
        self.con.close()
