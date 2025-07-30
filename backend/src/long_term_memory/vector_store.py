
"""
First run:
> bash start_ollama.sh
> ollama pull nomic-embed-text (if not pulled yet)
> ollama list (to check if it is installed pulled)
"""

from datetime import datetime
import time
import uuid
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
    def __init__(self, dim=768, collection_name: str = "docs", reset_on_init: bool = False, path: str = "./backend/src/long-term-memory/vector_memory", vector_store: str = VECTOR_STORE):  # 768 is correct for nomic
        self.dim = dim
        self.path = Path(path + "_" + vector_store)
        self.path.mkdir(parents=True, exist_ok=True)
        self.vector_store = vector_store
        
        # Initialize Vector Store
        if self.vector_store == "chromadb":
            self.client = chromadb.PersistentClient(path=self.path, settings=chromadb.config.Settings(allow_reset=True))
            self.collection = self.client.get_or_create_collection(name=collection_name)
        
        elif self.vector_store == "faiss":
            self.index = faiss.IndexFlatL2(dim)
            self.memories = []
            self.metadata_path = self.path / "metadata.json"
            if self.metadata_path.exists():
                self.memories = json.loads(self.metadata_path.read_text())

        if reset_on_init:
            cprint("Resetting vector store...", "yellow")
            self.reset()


    def save(self, content:str, metadata=None):
        vec = np.array(get_embedding_ollama(content), dtype="float32")
        #print("Embedding length:", len(vec))
        unique_id = str(uuid.uuid4())
        cprint(f"Saved document with ID: {unique_id}. Content: {content}", "yellow")

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
        cprint(f"Vector search for query: {query}", "yellow")

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


            distances, unique_ids, metadatas = results['distances'][0], results['ids'][0], results['metadatas'][0]
            documents = results['documents'][0] # list of documents
            
        elif self.vector_store == "faiss":
            
            # Query the index
            distances, indexes = self.index.search(np.array([q_vec]), k)
            distances = distances[0]  # Get the first (and only) result
            indexes = indexes[0]  # Get the first (and only) result
            documents = [
                self.memories[i]['content']
                for i in indexes
                if i < len(self.memories)
            ]
            
            unique_ids = [
                self.memories[i]['id']
                for i in indexes
                if i < len(self.memories)
            ]
         
            metadatas = [
                self.memories[i]['metadata']
                for i in indexes
                if i < len(self.memories)
            ]
         
            if include_tags:
                warning = "Filtering by tags is not supported in FAISS. Returning all results."
                cprint(warning, "red")
        print(distances)
        distances = np.array(distances)  # Remove extra dimension
        recencies = np.array([], dtype=float)
        importances = np.array([], dtype=float)
        for meta in metadatas:
            recencies = np.append(recencies, (datetime.now() - datetime.strptime(meta.get("created_at", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")).total_seconds())
            importances = np.append(importances, float(meta.get("importance", 1)))  # Default importance to 1 if not specified

        cosine_similarities = 1 - distances  # Convert distances to cosine similarities
        cprint(f"Vector search results (ordered by distance):", "yellow")
        print("Distances:", distances)
        print("Cosine Similarities:", cosine_similarities)
        print("Recencies :", recencies)
        print("Importances:", importances)
        print("Doc Ids:", unique_ids)
        print(f"Documents ({len(documents)}):", documents)

        return documents, distances, cosine_similarities, recencies, importances

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
                
        print(f"Total documents in vector store: {self.count_all()}")
                
    def count_all(self):

        if self.vector_store == "faiss":
            return len(self.memories)

        elif self.vector_store == "chromadb":
            return len(self.collection.peek()["ids"])
            

# Initialize Vector Memory Store
vector_store = VectorMemoryStore(collection_name="docs", reset_on_init=True)

# Step 1: Save (store)
# =====================

documents = [
  {"content": "User loves food.",
   "metadata": {"tags": "preferences", 
                "importance": "5"}},
  {"content": "User went to the park on Monday.",
   "metadata": {"tags": "activities", 
                "importance": "5"}},
  {"content": "User dislikes football.",
   "metadata": {"tags": "preferences",
                "importance": "5"}},
  {"content": "User is a software engineer and works with AI.",
   "metadata": {"tags": "occupation", 
                "importance": "5"}},
  {"content": "User had a cat.",
   "metadata": {"tags": "animals", 
                "importance": "5"}},
  {"content": "User has a dog.",
   "metadata": {"tags": "animals", 
                "importance": "5"}},
]



for i, d in enumerate(documents):
  time.sleep(2)  # To ensure different timestamps
  vector_store.save(
    content=d["content"],
    metadata={**d["metadata"], "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  )
  
vector_store.show_all()


# Step 2: Search (retrieve)
# =========================
query = "What animal does User have?"

# Vector search
contents, distances, cosine_similarities, recencies, importances = vector_store.search(query, k=vector_store.count_all(), include_tags=[])

# Calculate scores based on importance, recency, and similarity
cprint("\nContents reordered by SCORE:\nalpha_importance*importance + alpha_recency*0.995**recency + alpha_similarity*cosine_similarity", "yellow")
alpha_importance = 1
alpha_recency = 1
alpha_similarity = 1
exp_recency = 0.995**recencies
scores = alpha_importance*importances + alpha_recency*exp_recency + alpha_similarity*cosine_similarities

# Sort documents by score
sorted_indices = np.argsort(scores)[::-1]  # Sort in descending order
print(f"Sorted indices: {sorted_indices}")
sorted_contents = [contents[i] for i in sorted_indices]
sorted_distances = [distances[i] for i in sorted_indices]
sorted_cosine_similarities = [cosine_similarities[i] for i in sorted_indices]
sorted_recencies = [recencies[i] for i in sorted_indices]
sorted_exp_recency = [exp_recency[i] for i in sorted_indices]
sorted_importances = [importances[i] for i in sorted_indices]

cprint(f"alpha_importance = {alpha_importance} | alpha_recency = {alpha_recency} | alpha_similarity = {alpha_similarity}", "yellow")
for i, content in enumerate(sorted_contents):
    print(f"\n[{i}] Content: {content}")
    print(f"     Distance: {sorted_distances[i]}")
    print(f"     Cosine Similarity: {sorted_cosine_similarities[i]}")
    print(f"     Recency: {sorted_recencies[i]}")
    print(f"     Exp Recency: {sorted_exp_recency[i]}")
    print(f"     Importance: {sorted_importances[i]}")
    print(f"     SCORE: {scores[sorted_indices[i]]}")
    print("-" * 40)
    
    
# Step 3: Generate
# ================
top_score = 3
# # generate a response combining the prompt and data we retrieved in step 2
generation_prompt = f"Using this data:\n{sorted_contents[:top_score]}.\nRespond to this prompt:\n{query}"

output = ollama.generate(
  model="mistral-small3.2:24b",
  prompt=generation_prompt
)

cprint(f"GENERATION PROMPT: {generation_prompt}", "green")
cprint(f"GENERATION OUTPUT: {output['response']}", "blue")
vector_store.reset()