"""
config.py
~~~~~~~~~

Configuration for loading ecological succession rules from the AgroSuccess
Neo4j graph database.
"""
import os
from pathlib import Path

HOST: str = 'localhost'
PORT: int = 7687
USER: str = 'neo4j'
PASSWORD: str = 'password'

MODEL_ID: str = 'AgroSuccess-dev'


def get_output_dir() -> Path:
    return Path(os.path.realpath(__file__)).parent.parent / 'outputs'


OUTPUT_JSON_FILE: Path = get_output_dir() / 'succession_rules.json'
