"""
Async PostgreSQL normalizer for biomedical concept normalization.

Works with PostgreSQL databases using the same schema as DuckDB databases
built by build_umls_duckdb, build_ontology_duckdb, or build_merged_duckdb.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl
from lvg_norm import lvg_normalize
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

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


class PostgresNormalizer:
    """
    Async normalizer using PostgreSQL via SQLAlchemy.

    Optimized for small batch processing (1-5 strings at a time).
    Uses VALUES clauses instead of temp tables for efficiency with small batches.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        schema: str = "public",
        owned_resource: Any | None = None,
    ) -> None:
        """
        Initialize the normalizer with an SQLAlchemy AsyncEngine.

        Args:
            engine: SQLAlchemy AsyncEngine (caller manages lifecycle)
            schema: PostgreSQL schema where tables are located (default: "public")
            owned_resource: Optional resource with async close() method to clean up
                when this normalizer is closed (e.g., AlloyDB AsyncConnector)

        Note:
            After creating the normalizer, call `await normalizer.initialize()`
            to detect database capabilities before using other methods.
        """
        self._engine = engine
        self._schema = schema
        self._owned_resource = owned_resource
        self._has_types = False
        self._has_defs = False
        self._has_edges = False
        self._has_stt = False
        self._initialized = False

        # Build qualified table names
        prefix = f"{schema}." if schema else ""
        self._ns_table = f"{prefix}{NS_TABLE}"
        self._nw_table = f"{prefix}{NW_TABLE}"
        self._atoms_table = f"{prefix}{ATOMS_TABLE}"
        self._types_table = f"{prefix}{TYPES_TABLE}"
        self._defs_table = f"{prefix}{DEFS_TABLE}"
        self._edges_table = f"{prefix}{EDGES_TABLE}"

    async def _ensure_initialized(self) -> None:
        """Lazily initialize on first use."""
        if self._initialized:
            return
        self._has_types = await self._table_has_rows(self._types_table)
        self._has_defs = await self._table_has_rows(self._defs_table)
        self._has_edges = await self._table_has_rows(self._edges_table)
        self._has_stt = await self._column_has_values(self._atoms_table, "stt")
        self._initialized = True

    async def _table_has_rows(self, table: str) -> bool:
        """Check if a table exists and has rows."""
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                return result.scalar() is not None
        except Exception:
            return False

    async def _column_has_values(self, table: str, column: str) -> bool:
        """Check if a column has any non-null values."""
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text(f"SELECT 1 FROM {table} WHERE {column} IS NOT NULL LIMIT 1"))
                return result.scalar() is not None
        except Exception:
            return False

    async def normalize(
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
        await self._ensure_initialized()

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

        result = await self._lookup(
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

    async def _lookup(
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
        """Core lookup via exact + partial match paths."""
        top_k = max(1, int(top_k))

        # Flatten q_to_nstrs to rows
        qmap_rows: list[tuple[str, str]] = []
        for q, nstrs in q_to_nstrs.items():
            for nstr in dict.fromkeys(nstrs):
                if nstr:
                    qmap_rows.append((q, nstr))

        if not qmap_rows:
            return pl.DataFrame({"input_string": all_queries, "hits": [[] for _ in all_queries]}).cast(
                {"hits": pl.List(HIT_STRUCT_TYPE)}
            )

        # Build parameters and VALUES clauses using named parameters
        params: dict[str, Any] = {}
        param_idx = 0

        # qmap VALUES clause
        qmap_placeholders = []
        for q, nstr in qmap_rows:
            q_key, nstr_key = f"p{param_idx}", f"p{param_idx + 1}"
            params[q_key] = q
            params[nstr_key] = nstr
            qmap_placeholders.append(f"(:{q_key}, :{nstr_key})")
            param_idx += 2
        qmap_values = ", ".join(qmap_placeholders)

        # qwords VALUES clause (for partial path)
        qwords_values = ""
        if allow_partial:
            qwords_rows = [(q, n, w) for q, n in qmap_rows for w in dict.fromkeys(n.split()) if w]
            qwords_placeholders = []
            for q, nstr, nwd in qwords_rows:
                q_key, nstr_key, nwd_key = f"p{param_idx}", f"p{param_idx + 1}", f"p{param_idx + 2}"
                params[q_key] = q
                params[nstr_key] = nstr
                params[nwd_key] = nwd
                qwords_placeholders.append(f"(:{q_key}, :{nstr_key}, :{nwd_key})")
                param_idx += 3
            qwords_values = ", ".join(qwords_placeholders)

        # allq VALUES clause (preserve order)
        allq_placeholders = []
        for q in all_queries:
            q_key = f"p{param_idx}"
            params[q_key] = q
            allq_placeholders.append(f"(:{q_key})")
            param_idx += 1
        allq_values = ", ".join(allq_placeholders)

        # Build preference clauses (parameterized to prevent SQL injection)
        tty_join = ""
        tty_bump_expr = "0"
        if prefer_ttys:
            tty_placeholders = []
            for tty in prefer_ttys:
                key = f"p{param_idx}"
                params[key] = tty
                tty_placeholders.append(f"(:{key})")
                param_idx += 1
            tty_vals = ", ".join(tty_placeholders)
            tty_join = f"LEFT JOIN (VALUES {tty_vals}) AS pt(tty) ON a.name_type = pt.tty"
            tty_bump_expr = "CASE WHEN pt.tty IS NULL THEN 0 ELSE 1 END"

        # Source filtering (parameterized to prevent SQL injection)
        source_filter_exprs = []
        nw_filter_clauses = []
        if filter_sources:
            filt_placeholders = []
            for src in filter_sources:
                key = f"p{param_idx}"
                params[key] = src
                filt_placeholders.append(f":{key}")
                param_idx += 1
            filt_vals = ", ".join(filt_placeholders)
            source_filter_exprs.append(f"a.source IN ({filt_vals})")
            nw_filter_clauses.append(f"nw.source IN ({filt_vals})")
        if exclude_sources:
            excl_placeholders = []
            for src in exclude_sources:
                key = f"p{param_idx}"
                params[key] = src
                excl_placeholders.append(f":{key}")
                param_idx += 1
            excl_vals = ", ".join(excl_placeholders)
            source_filter_exprs.append(f"a.source NOT IN ({excl_vals})")
            nw_filter_clauses.append(f"nw.source NOT IN ({excl_vals})")
        nw_filter_clause = (" AND " + " AND ".join(nw_filter_clauses)) if nw_filter_clauses else ""
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
    JOIN {self._ns_table} ns ON ns.nstr = q.NSTR
    JOIN {self._atoms_table} a
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
        if allow_partial and qwords_values:
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
    JOIN {self._nw_table} nw ON nw.nwd = qw.NWD{nw_filter_clause}
    GROUP BY qw.Q, qw.NSTR, nw.string_id, nw.concept_id
),
good AS (
    SELECT h.Q, h.NSTR, h.string_id, h.concept_id, h.hits, qn.need,
        CAST(h.hits AS DOUBLE PRECISION)/NULLIF(qn.need,0) AS coverage
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
    JOIN {self._atoms_table} a ON a.string_id = g.string_id
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

        # qwords CTE (only if partial enabled)
        qwords_cte = ""
        if allow_partial and qwords_values:
            qwords_cte = f"qwords(Q, NSTR, NWD) AS (VALUES {qwords_values}),"

        # Final aggregation SQL with JSON_AGG
        sql = f"""
WITH
qmap(Q, NSTR) AS (VALUES {qmap_values}),
{qwords_cte}
allq(Q) AS (VALUES {allq_values}),
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
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'global_identifier', concept_id,
                'identifier', identifier,
                'nstr', NSTR,
                'name', str,
                'source', source,
                'name_type', name_type,
                'score', rank,
                'total_score', total_score,
                'match_type', CASE WHEN is_exact THEN 'exact' ELSE 'partial' END
            ) ORDER BY total_score DESC, concept_id
        ) AS hits
    FROM topk
    GROUP BY Q
)
SELECT
    aq.Q AS input_string,
    agg.hits
FROM allq aq
LEFT JOIN agg ON agg.Q = aq.Q;
"""

        async with self._engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.mappings().all()

        # Parse results into Polars DataFrame
        # Note: asyncpg auto-deserializes JSON, so hits may already be a list
        data = []
        for row in rows:
            input_string = row["input_string"]
            hits_raw = row["hits"]
            if hits_raw is None:
                hits = []
            elif isinstance(hits_raw, list):
                hits = hits_raw  # Already deserialized by asyncpg
            else:
                hits = json.loads(hits_raw)  # String, needs parsing
            data.append({"input_string": input_string, "hits": hits})

        return pl.DataFrame(data).cast({"hits": pl.List(HIT_STRUCT_TYPE)})

    async def concept_info(
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
        await self._ensure_initialized()

        if not concept_ids:
            return {}

        if prefer_ttys is None:
            prefer_ttys = DEFAULT_PREFER_TTYS

        id_list = list(dict.fromkeys(concept_ids))

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

        # Build idmap VALUES clause using named parameters
        params: dict[str, Any] = {}
        param_idx = 0
        idmap_placeholders = []
        for cid in id_list:
            key = f"p{param_idx}"
            params[key] = cid
            idmap_placeholders.append(f"(:{key})")
            param_idx += 1
        idmap_values = ", ".join(idmap_placeholders)

        # Build preference clauses
        tty_join = ""
        tty_bump = "0"
        if prefer_ttys:
            tty_placeholders = []
            for tty in prefer_ttys:
                key = f"p{param_idx}"
                params[key] = tty
                tty_placeholders.append(f"(:{key})")
                param_idx += 1
            tty_vals = ", ".join(tty_placeholders)
            tty_join = f"LEFT JOIN (VALUES {tty_vals}) AS pt(tty) ON a.name_type = pt.tty"
            tty_bump = "CASE WHEN pt.tty IS NULL THEN 0 ELSE 1 END"

        stt_bump = "CASE WHEN a.stt='PF' THEN 1 ELSE 0 END" if self._has_stt else "0"

        # Main query for names
        sql = f"""
WITH
idmap(concept_id) AS (VALUES {idmap_values}),
name_cand AS (
    SELECT
        c.concept_id, a.str, a.source AS sab,
        a.name_type AS tty, a.ispref, a.stt, a.rank,
        CASE WHEN a.ispref='Y' THEN 1 ELSE 0 END AS ispref_bump,
        {stt_bump} AS stt_bump,
        {tty_bump} AS tty_bump,
        a.identifier
    FROM idmap c
    JOIN {self._atoms_table} a ON a.concept_id = c.concept_id
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
    JOIN {self._atoms_table} a ON a.concept_id = c.concept_id
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

        async with self._engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.mappings().all()

        for row in rows:
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
            await self._populate_definitions(res, id_list, prefer_def_sources)

        # Semantic types (if available)
        if self._has_types:
            await self._populate_semantic_types(res, id_list)

        return res

    async def _populate_definitions(
        self,
        res: dict[str, ConceptInfo],
        id_list: list[str],
        prefer_def_sources: list[str] | None,
    ) -> None:
        """Populate definitions for concepts."""
        params: dict[str, Any] = {}
        param_idx = 0
        idmap_placeholders = []
        for cid in id_list:
            key = f"p{param_idx}"
            params[key] = cid
            idmap_placeholders.append(f"(:{key})")
            param_idx += 1
        idmap_values = ", ".join(idmap_placeholders)

        def_pref_join = ""
        def_pref_bump = "0"
        if prefer_def_sources:
            def_placeholders = []
            for src in prefer_def_sources:
                key = f"p{param_idx}"
                params[key] = src
                def_placeholders.append(f"(:{key})")
                param_idx += 1
            def_vals = ", ".join(def_placeholders)
            def_pref_join = f"LEFT JOIN (VALUES {def_vals}) AS pds(sab) ON d.source = pds.sab"
            def_pref_bump = "CASE WHEN pds.sab IS NULL THEN 0 ELSE 1 END"

        sql = f"""
WITH
idmap(concept_id) AS (VALUES {idmap_values}),
def_cand AS (
    SELECT
        d.concept_id, d.source AS sab, d.def_text,
        {def_pref_bump} AS def_pref_bump,
        length(d.def_text) AS def_len
    FROM {self._defs_table} d
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

        async with self._engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.mappings().all()

        for row in rows:
            cid = row["concept_id"]
            if cid in res and row["def_text"]:
                res[cid].description = row["def_text"]
                res[cid].def_source = row["def_sab"]

    async def _populate_semantic_types(
        self,
        res: dict[str, ConceptInfo],
        id_list: list[str],
    ) -> None:
        """Populate semantic types for concepts."""
        params: dict[str, Any] = {}
        idmap_placeholders = []
        for i, cid in enumerate(id_list):
            key = f"p{i}"
            params[key] = cid
            idmap_placeholders.append(f"(:{key})")
        idmap_values = ", ".join(idmap_placeholders)

        sql = f"""
WITH idmap(concept_id) AS (VALUES {idmap_values})
SELECT DISTINCT t.concept_id, t.type_id, t.type_name, t.type_tree
FROM {self._types_table} t
JOIN idmap c ON c.concept_id = t.concept_id
ORDER BY t.concept_id, t.type_tree, t.type_id;
"""

        async with self._engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.mappings().all()

        for row in rows:
            cid = row["concept_id"]
            if cid in res and row["type_id"] and row["type_name"]:
                res[cid].semantic_types.append(SemanticType(type_id=row["type_id"], type_name=row["type_name"]))

    async def concept_semantic_types(
        self,
        concept_ids: Sequence[str],
    ) -> dict[str, list[dict[str, str]]]:
        """
        Get semantic types for concepts.

        Returns dict mapping concept_id to list of {"tui": ..., "sty": ...}
        """
        await self._ensure_initialized()

        if not self._has_types or not concept_ids:
            return {cid: [] for cid in concept_ids}

        id_list = list(dict.fromkeys(concept_ids))

        params: dict[str, Any] = {}
        idmap_placeholders = []
        for i, cid in enumerate(id_list):
            key = f"p{i}"
            params[key] = cid
            idmap_placeholders.append(f"(:{key})")
        idmap_values = ", ".join(idmap_placeholders)

        sql = f"""
WITH idmap(concept_id) AS (VALUES {idmap_values})
SELECT DISTINCT t.concept_id, t.type_id AS tui, t.type_name AS sty, t.type_tree
FROM {self._types_table} t
JOIN idmap c ON c.concept_id = t.concept_id
ORDER BY t.concept_id, t.type_tree, t.type_id;
"""

        async with self._engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.mappings().all()

        res: dict[str, list[dict[str, str]]] = {cid: [] for cid in id_list}
        for row in rows:
            res[row["concept_id"]].append({"tui": row["tui"], "sty": row["sty"]})

        return res

    async def get_narrower_concepts(
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
        await self._ensure_initialized()

        if not self._has_edges:
            return []

        params: dict[str, Any] = {"concept_id": concept_id, "max_depth": max_depth}

        # Build source filter clause
        source_filter = ""
        if filter_sources:
            src_placeholders = []
            for i, src in enumerate(filter_sources):
                key = f"src{i}"
                params[key] = src
                src_placeholders.append(f":{key}")
            sources_sql = ", ".join(src_placeholders)
            source_filter = f" AND e.source IN ({sources_sql})"

        # PostgreSQL recursive CTE with named parameters
        # Use CAST() instead of :: to avoid conflicts with SQLAlchemy named params
        # UNION (not UNION ALL) deduplicates on (concept_id, depth) during recursion
        # DISTINCT in output needed since same concept can be reached at different depths
        query = f"""
WITH RECURSIVE walk(concept_id, depth) AS (
    SELECT CAST(:concept_id AS VARCHAR), 0

    UNION

    SELECT e.child_id, w.depth + 1
    FROM walk w
    JOIN {self._edges_table} e ON e.parent_id = w.concept_id
    WHERE (CAST(:max_depth AS INTEGER) IS NULL OR w.depth < :max_depth){source_filter}
)
SELECT DISTINCT concept_id
FROM walk
WHERE concept_id != :concept_id
"""

        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params)
            rows = result.mappings().all()

        return [r["concept_id"] for r in rows]

    async def close(self) -> None:
        """
        Close the engine and any owned resources.

        Note: Only call this if you want to close the engine. If the engine
        is managed externally, the caller should close it instead.
        """
        await self._engine.dispose()
        if self._owned_resource is not None:
            await self._owned_resource.close()
