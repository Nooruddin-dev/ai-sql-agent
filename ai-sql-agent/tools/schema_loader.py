import json
from typing import Dict, Set, Tuple

def load_schema(schema_path: str) -> Dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_allowlists(schema_json: Dict) -> Tuple[Set[str], Dict[str, Set[str]]]:
    tables = set()
    columns_by_table = {}
    for t in schema_json.get("DatabaseSchema", []):
        tname = t["TableName"]
        tables.add(tname)
        columns_by_table[tname] = {c["ColumnName"] for c in t.get("Columns", [])}
    return tables, columns_by_table
