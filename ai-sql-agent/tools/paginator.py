from helpers.errors import PaginationError

def wrap_with_pagination(sql: str, page: int, page_size: int) -> str:
    # SQL Server requires ORDER BY for OFFSET/FETCH; fall back to ORDER BY 1 if none present.
    normalized = sql.strip().rstrip(";")
    if " offset " in normalized.lower() and " fetch " in normalized.lower():
        return normalized
    # Wrap in derived table to not alter user semantics; ORDER BY 1 is acceptable for pagination baseline.
    return f"SELECT * FROM ({normalized}) AS _q ORDER BY 1 OFFSET {max(0,(page-1)*page_size)} ROWS FETCH NEXT {page_size} ROWS ONLY"
