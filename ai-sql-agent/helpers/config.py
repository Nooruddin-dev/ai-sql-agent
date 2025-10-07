import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

class Config(BaseModel):
    app: dict
    llm: dict
    database: dict
    limits: dict
    security: dict
    chat_history: dict
    schema: dict
    ui: dict
    retriever: dict  
    mock_flow: dict  

def load_config(path: str = "config/config.yaml") -> Config:
    load_dotenv()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(**data)
