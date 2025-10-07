import logging, sys
from rich.logging import RichHandler

def setup_logging(level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )
    return logging.getLogger("ai-sql-agent")
