# ✅ Patch sqlite3 if system version is too old
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.utils import embedding_functions
from typing import Dict, List

class SchemaRetriever:
    def __init__(
        self,
        schema_json: Dict,
        persist_path: str = "./chroma_schema_index",
        top_k: int = 10
    ):
        self.top_k = top_k
        self.client = chromadb.PersistentClient(path=persist_path)

        # ✅ Sentence Transformer embeddings (fast & local)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name="schema", embedding_function=self.embedding_fn
        )

        # Only index once (first run)
        if self.collection.count() == 0:
            self._index_schema(schema_json)

    def _index_schema(self, schema_json: Dict):
        docs, ids, metas = [], [], []

        for i, t in enumerate(schema_json.get("DatabaseSchema", [])):
            schema_name = t.get("SchemaName")
            table_name = t.get("TableName")
            full_name = t.get("FullTableName", f"{schema_name}.{table_name}")

            # ✅ Columns are now a dict {col: type}
            cols = list(t.get("Columns", {}).keys())

            # ✅ Foreign keys (same as before)
            fks = [
                f"{fk['ParentColumn']} -> {fk['ReferencedTable']}.{fk['ReferencedColumn']}"
                for fk in t.get("ForeignKeys", [])
            ]

            # ✅ Text content for embeddings
            text_parts = [
                f"Schema: {schema_name}",
                f"Table: {full_name}",
                f"Columns: {', '.join(cols)}"
            ]
            if fks:
                text_parts.append(f"Foreign Keys: {', '.join(fks)}")

            text = ". ".join(text_parts)

            unique_id = f"{full_name}_{i}"

            docs.append(text)
            ids.append(unique_id)
            metas.append({
                "schema": schema_name,
                "table": full_name,
                "columns": ", ".join(cols),
                "foreign_keys": ", ".join(fks) if fks else ""
            })

        self.collection.add(documents=docs, ids=ids, metadatas=metas)

    def _index_schema(self, schema_json: Dict):
        docs, ids, metas = [], [], []

        for i, t in enumerate(schema_json.get("DatabaseSchema", [])):
            schema_name = t.get("SchemaName") or ""  # ✅ ensure not None
            table_name = t.get("TableName") or ""
            full_name = t.get("FullTableName") or f"{schema_name}.{table_name}".strip(".")

            # ✅ Columns are dict {col: type}
            cols = list(t.get("Columns", {}).keys())

            # ✅ Handle missing FK keys safely
            fks = []
            for fk in t.get("ForeignKeys", []):
                parent = fk.get("ParentColumn")
                ref_table = fk.get("ReferencedTable")
                ref_col = fk.get("ReferencedColumn")
                if not (parent and ref_table and ref_col):
                    continue
                fks.append(f"{parent} -> {ref_table}.{ref_col}")

            # ✅ Text content for embeddings
            text_parts = [
                f"Schema: {schema_name}",
                f"Table: {full_name}",
                f"Columns: {', '.join(cols)}"
            ]
            if fks:
                text_parts.append(f"Foreign Keys: {', '.join(fks)}")

            text = ". ".join(text_parts)
            unique_id = f"{full_name}_{i}"

            docs.append(text)
            ids.append(unique_id)
            metas.append({
                # ✅ ensure all are strings (Chroma requires)
                "schema": str(schema_name or ""),
                "table": str(full_name or ""),
                "columns": str(", ".join(cols) or ""),
                "foreign_keys": str(", ".join(fks) or "")
            })

        # ✅ Double-check no None remains
        metas = [
            {k: ("" if v is None else v) for k, v in meta.items()}
            for meta in metas
        ]

        self.collection.add(documents=docs, ids=ids, metadatas=metas)



    def query(self, user_query: str) -> List[Dict]:
        """Return top-k relevant tables for a user question."""
        results = self.collection.query(query_texts=[user_query], n_results=self.top_k)

        matches = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            matches.append({
                "schema": meta.get("schema"),
                "table": meta.get("table"),
                "columns": meta.get("columns").split(", ") if meta.get("columns") else [],
                "foreign_keys": meta.get("foreign_keys").split(", ") if meta.get("foreign_keys") else [],
                "doc": doc
            })

        return matches
