"""
Ollama Operations Module
"""

import ollama
from config import Settings


# From user query/query to query embedding
def create_embedding(input_text:str):
    vec = ollama.embed(model=Settings.EMB_MODEL, input=input_text)["embeddings"][0] 
    return vec
  