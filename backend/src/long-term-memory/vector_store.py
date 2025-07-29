
"""
First run:
> bash start_ollama.sh
> ollama pull nomic-embed-text (if not pulled yet)
> ollama list (to check if it is installed pulled)
"""

from datetime import datetime
import uuid
import faiss
import chromadb
import ollama
import numpy as np
import json
import requests
from pathlib import Path
from termcolor import cprint

VECTOR_STORE = "chromadb"  # Change to "chromadb" if using ChromaDB | Change to "faiss" if using FAISS

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
        #print("Embedding length:", len(vec))
        unique_id = str(uuid.uuid4())
        cprint(f"Saved document with ID: {unique_id}.", "yellow")

        if self.vector_store == "chromadb":
            self.collection.add(
                ids=unique_id,
                embeddings=np.array([vec]),
                documents=[content],
                metadatas=[metadata or {}]
            )
        elif self.vector_store == "faiss":

            self.index.add(
                np.array([vec])
            )

            self.memories.append({"content": content, "id": unique_id, "metadata": metadata or {}})
            self.metadata_path.write_text(json.dumps(self.memories, indent=2))

    def search(self, query:str, k:int=3, include_tags:list=[]):
        # generate an embedding for the input and retrieve the most relevant doc
        cprint(f"Searching for query: {query}", "yellow")

        q_vec = np.array(get_embedding_ollama(query), dtype="float32")

        # Get the top k results from the collection
        if self.vector_store == "chromadb":
            
            # Build filter dictionary
            filters = {}
            if include_tags:
                filters["tags"] = {"$in": include_tags}
            

            # Query the collection with filtering
            results = self.collection.query(
                query_embeddings=[q_vec],
                n_results=k,
                where=None if not filters else filters,
            )
       
            
            D, I = results['distances'][0], results['ids'][0]

            top_results = results['documents'][0] # list of documents
            
        elif self.vector_store == "faiss":
            
            # Query the index
            D, I = self.index.search(np.array([q_vec]), k)
            top_results = [
                self.memories[i]['content']
                for i in I[0]
                if i < len(self.memories)
            ]
         
            if include_tags:
                warning = "Filtering by tags is not supported in FAISS. Returning all results."
                cprint(warning, "red")
                
        print("Distances:", D)
        print("Doc Ids:", I)
        print(f"Documents ({len(top_results)}):", top_results)

        return top_results

    def reset(self):
        if self.vector_store == "chromadb":
            # Get all document IDs from the collection
            all_ids = self.collection.peek()["ids"]
        
            if all_ids:  # only delete if there are documents
                self.collection.delete(ids=all_ids)
            
        elif self.vector_store == "faiss":
            self.index = faiss.IndexFlatL2(self.dim)
            self.memories = []
            self.metadata_path.write_text("[]")
            
        cprint("Vector store reset.", "yellow")
        
    def show_all(self):
        cprint("Vector store contents:", "yellow")

        if self.vector_store == "faiss":
            for i, memory in enumerate(self.memories):
                print(f"[{i}] Content: {memory['content']}")
                print(f"     Metadata: {memory['metadata']}")
                print("-" * 40)

        elif self.vector_store == "chromadb":
            # Retrieve all documents in the collection
            # NOTE: Chroma currently requires you to know the IDs to fetch them all
            # So we fetch all IDs first:
            all_ids = self.collection.peek()["ids"]

            results = self.collection.get(
                ids=all_ids,
                include=["documents", "metadatas"]
            )
            
            for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
                print(f"[{i}] Content: {doc}")
                print(f"     Metadata: {meta}")
                print("-" * 40)
            

# Initialize Vector Memory Store
vector_store = VectorMemoryStore()

# Step 1: Save documents
documents = [
  {"content": "Llamas are members of the camelid family meaning they're pretty closely related to vicuñas and camels", 
   "metadata": {"tags": "llamas", "importance": "5"}},
  {"content": "Llamas were first domesticated and used as pack animals 4,000 to 5,000 years ago in the Peruvian highlands", 
   "metadata": {"tags": "llamas", "importance": "5"}},
  {"content": "Llamas can grow as much as 6 feet tall though the average llama between 5 feet 6 inches and 5 feet 9 inches tall", 
   "metadata": {"tags": "llamas", "importance": "5"}},
  {"content": "Llamas weigh between 280 and 450 pounds and can carry 25 to 30 percent of their body weight", 
   "metadata": {"tags": "llamas", "importance": "5"}},
  {"content": "Llamas are vegetarians and have very efficient digestive systems", 
   "metadata": {"tags": "llamas", "importance": "5"}},
  {"content": "Llamas live to be about 20 years old, though some only live for 15 years and others live to be 30 years old", 
   "metadata": {"tags": "llamas", "importance": "5"}},
  {"content": "Iria's favorite animal is the cat.", 
   "metadata": {"tags": "cats", "importance": "5"}},
  {"content": "Turtles are green.", 
   "metadata": {"tags": "turtles", "importance": "5"}},
]

for i, d in enumerate(documents):
  vector_store.save(
    content=d["content"],
    metadata={**d["metadata"], "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  )
  
vector_store.show_all()

# Step 2: Search (retrieve)
query = "What is the weight of a llama?"
results = vector_store.search(query, k=3, include_tags=["turtles"])

# Step 3: Generate
# # generate a response combining the prompt and data we retrieved in step 2
generation_prompt = f"Using this data: {results}. Respond to this prompt: {query}"

output = ollama.generate(
  model="mistral-small3.2:24b",
  prompt=generation_prompt
)

cprint(f"GENERATION PROMPT: {generation_prompt}", "green")
cprint(f"GENERATION OUTPUT: {output['response']}", "blue")
