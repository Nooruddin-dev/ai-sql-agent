# tools/schema_retriever.py

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

        # ✅ Use Sentence Transformers embeddings (free + local)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name="schema", embedding_function=self.embedding_fn
        )

        # Index only once (first run)
        if self.collection.count() == 0:
            self._index_schema(schema_json)

    def _index_schema(self, schema_json: Dict):
        docs, ids, metas = [], [], []
        for i, t in enumerate(schema_json.get("DatabaseSchema", [])):
            table = t["TableName"]
            cols = [c["ColumnName"] for c in t.get("Columns", [])]

            # Include foreign keys in the searchable text (optional, useful for joins)
            fks = [
                f"{fk['ParentColumn']} -> {fk['ReferencedTable']}.{fk['ReferencedColumn']}"
                for fk in t.get("ForeignKeys", [])
            ]

            # Text representation for embedding
            text_parts = [f"Table: {table}", f"Columns: {', '.join(cols)}"]
            if fks:
                text_parts.append(f"Foreign Keys: {', '.join(fks)}")
            text = ". ".join(text_parts)

            # Unique ID to avoid duplicate errors
            unique_id = f"{table}_{i}"

            docs.append(text)
            ids.append(unique_id)
            metas.append({
                "table": table,
                "columns": ", ".join(cols),   # Flatten list → string
                "foreign_keys": ", ".join(fks) if fks else ""
            })

        self.collection.add(documents=docs, ids=ids, metadatas=metas)

    def query(self, user_query: str) -> List[Dict]:
        results = self.collection.query(query_texts=[user_query], n_results=self.top_k)

        matches = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            matches.append({
                "table": meta["table"],
                "columns": meta["columns"].split(", ") if meta.get("columns") else [],
                "foreign_keys": meta["foreign_keys"].split(", ") if meta.get("foreign_keys") else [],
                "doc": doc
            })

        return matches
