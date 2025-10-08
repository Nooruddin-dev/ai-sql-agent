import json
from typing import Dict, Set, Tuple

def load_schema(schema_path: str) -> Dict:
    """Load the entire database schema JSON file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_allowlists(schema_json: Dict) -> Tuple[Set[str], Dict[str, Set[str]]]:
    """
    Build allow-lists for table and column validation.
    Works with new schema format.
    """
    tables = set()
    columns_by_table = {}

    for t in schema_json.get("DatabaseSchema", []):
        # ✅ Graceful fallback if keys are missing
        full_table = (
            t.get("FullTableName")
            or (
                f"{t.get('SchemaName', 'dbo')}.{t.get('TableName')}"
                if t.get("TableName")
                else None
            )
        )

        if not full_table:
            # skip malformed entries
            continue

        tables.add(full_table)

        # ✅ Columns dict → extract keys safely
        columns_dict = t.get("Columns", {})
        if isinstance(columns_dict, dict):
            columns_by_table[full_table] = set(columns_dict.keys())
        else:
            # defensive: handle legacy list format
            columns_by_table[full_table] = {
                c.get("ColumnName") for c in columns_dict if isinstance(c, dict)
            }

    return tables, columns_by_table
