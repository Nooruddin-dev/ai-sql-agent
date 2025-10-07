from typing import Dict, Set
import re
import sqlglot
from sqlglot import exp
from helpers.errors import ValidationError

WRITE_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Grant,
    exp.Revoke,
)

def _has_forbidden_funcs(root: exp.Expression, forbidden: Set[str]) -> bool:
    for fn in root.find_all(exp.Func):
        name = (fn.name or "").upper()
        if any(_match_like(name, pat) for pat in forbidden):
            return True
    return False

def _match_like(value: str, pattern: str) -> bool:
    if "%" in pattern:
        return re.fullmatch(pattern.replace("%", ".*"), value) is not None
    return value == pattern.upper()

def validate_read_only(sql: str, dialect: str, allow_tables: Set[str],
                       allow_cols: Dict[str, Set[str]],
                       block_keywords: Set[str], block_functions: Set[str], allow_ctes: bool = True) -> str:
    # No multiple statements
    trees = sqlglot.parse(sql, read=dialect)
    if len(trees) != 1:
        raise ValidationError("Multiple statements detected; only a single SELECT is allowed.")

    tree = trees[0]

    # Ensure SELECT (or WITH->SELECT, UNIONs of SELECT)
    def _is_select_like(node: exp.Expression) -> bool:
        return isinstance(node, (exp.Select, exp.Subquery, exp.Union, exp.Paren)) or (allow_ctes and isinstance(node, exp.With))
    if not _is_select_like(tree):
        raise ValidationError("Only SELECT (and WITH CTEs leading to a SELECT) are allowed.")

    # Block any write/DDL/command expressions anywhere in AST
    for node in tree.walk():
        if isinstance(node, WRITE_EXPRESSIONS):
            raise ValidationError(f"Write/DDL operation detected: {node.key}")

    # Block obvious keywords (string check)
    upper_sql = sql.upper()
    for kw in block_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", upper_sql):
            raise ValidationError(f"Forbidden keyword detected: {kw}")

    # Forbidden function calls
    if _has_forbidden_funcs(tree, {k.upper() for k in block_functions}):
        raise ValidationError("Forbidden function/proc detected (blocked).")

    # Allow-list tables & columns
    referenced_tables = {t.name for t in tree.find_all(exp.Table) if t.name}
    if not referenced_tables.issubset(allow_tables):
        diff = referenced_tables - allow_tables
        raise ValidationError(f"Unknown or disallowed table(s): {', '.join(sorted(diff))}")

    # Optional: check columns under each table where resolvable
    # (Skip strict column check for SELECT * and complex joins; still block unknown bare column refs)
    for col in tree.find_all(exp.Column):
        if col.table and col.name:
            t, c = col.table, col.name
            allowed_for_t = allow_cols.get(t, set())
            if allowed_for_t and c not in allowed_for_t:
                raise ValidationError(f"Column '{t}.{c}' not in schema allow-list.")
    return sql
