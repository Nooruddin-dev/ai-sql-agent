import pandas as pd
import plotly.express as px
import base64

def chart_png_base64(df: pd.DataFrame, x: str, y: str) -> str:
    fig = px.line(df, x=x, y=y)
    png = fig.to_image(format="png", scale=2)
    return base64.b64encode(png).decode("utf-8")
