
"""
First run:
> bash start_ollama.sh
> ollama pull nomic-embed-text (if not pulled yet)
> ollama list (to check if it is installed pulled)
"""

import faiss
import chromadb
import ollama
import numpy as np
import json
import requests
from pathlib import Path
from termcolor import cprint

VECTOR_STORE = "faiss"  # Change to "chromadb" if using ChromaDB | Change to "faiss" if using FAISS

def get_embedding_ollama(text: str, model="nomic-embed-text") -> list[float]:
    url = "http://localhost:11434/api/embed"
    payload = {
        "model": model,
        "input": text
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("embeddings", [])[0]

class VectorMemoryStore:
    def __init__(self, dim=768, path="./backend/src/long-term-memory/vector_memory", vector_store: str = VECTOR_STORE):  # 768 is correct for nomic
        self.dim = dim
        self.path = Path(path + "_" + vector_store)
        self.path.mkdir(parents=True, exist_ok=True)
        self.vector_store = vector_store
        
        # Initialize Vector Store
        if self.vector_store == "chromadb":
            self.client = chromadb.PersistentClient(path=self.path, settings=chromadb.config.Settings(allow_reset=True))
            self.collection = self.client.get_or_create_collection(name="docs")
        
        elif self.vector_store == "faiss":
            self.index = faiss.IndexFlatL2(dim)
            self.memories = []
            self.metadata_path = self.path / "metadata.json"
            if self.metadata_path.exists():
                self.memories = json.loads(self.metadata_path.read_text())
                
        self.reset()


    def save(self, content:str, metadata=None):
        vec = np.array(get_embedding_ollama(content), dtype="float32")
        print("Embedding length:", len(vec))

        if self.vector_store == "chromadb":
        
            self.collection.add(
                ids=[str(i)],
                embeddings=vec,
                documents=[content]
            )
        elif self.vector_store == "faiss":

            self.index.add(
                np.array([vec])
            )

            self.memories.append({"content": content, "metadata": metadata or {}})
            self.metadata_path.write_text(json.dumps(self.memories, indent=2))

    def search(self, query: str, k=3):
        # generate an embedding for the input and retrieve the most relevant doc
        q_vec = np.array(get_embedding_ollama(query), dtype="float32")

        # Get the top k results from the collection
        if self.vector_store == "chromadb":
            
            results = self.collection.query(
            query_embeddings=[q_vec],
            n_results=k
            )
            
            D, I = results['distances'][0], results['ids'][0]

            top_results = results['documents'][0] # list of documents
            
        elif self.vector_store == "faiss":
            
            D, I = self.index.search(np.array([q_vec]), k)

            top_results = [self.memories[i]['content'] for i in I[0] if i < len(self.memories)]
            
        print("Distances:", D)
        print("Indices:", I)
        return top_results

    def reset(self):
        if self.vector_store == "chromadb":
            self.client.reset()
            self.collection = self.client.get_or_create_collection(name="docs")
            
        elif self.vector_store == "faiss":
            self.index = faiss.IndexFlatL2(self.dim)
            self.memories = []
            self.metadata_path.write_text("[]")
            
        print("Vector store reset.")
        
# store each document in a vector embedding database
documents = [
  "Llamas are members of the camelid family meaning they're pretty closely related to vicuñas and camels",
  "Llamas were first domesticated and used as pack animals 4,000 to 5,000 years ago in the Peruvian highlands",
  "Llamas can grow as much as 6 feet tall though the average llama between 5 feet 6 inches and 5 feet 9 inches tall",
  "Llamas weigh between 280 and 450 pounds and can carry 25 to 30 percent of their body weight",
  "Llamas are vegetarians and have very efficient digestive systems",
  "Llamas live to be about 20 years old, though some only live for 15 years and others live to be 30 years old",
]

vector_store = VectorMemoryStore()

for i, d in enumerate(documents):

  vector_store.save(
    content=d,
    metadata={"id": str(i)}
  )

query = "What is the weight of a llama?"
results = vector_store.search(query)
for result in results:
    print(result)

# Step 3: Generate
# # generate a response combining the prompt and data we retrieved in step 2
generation_prompt = f"Using this data: {results}. Respond to this prompt: {query}"

output = ollama.generate(
  model="mistral-small3.2:24b",
  prompt=generation_prompt
)

cprint(generation_prompt, "green")
cprint(output['response'], "blue")