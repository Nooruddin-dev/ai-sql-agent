import pandas as pd

def to_markdown(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.shape[0] > max_rows:
        df = df.head(max_rows)
        footer = f"\n\n> Showing first {max_rows} rows."
    else:
        footer = ""
    return df.to_markdown(index=False) + footer
