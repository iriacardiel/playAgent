
"""
First run:
> bash start_ollama.sh
> ollama pull nomic-embed-text (if not pulled yet)
> ollama list (to check if it is installed pulled)
"""

from datetime import datetime
import uuid
import chromadb
import numpy as np
import requests
from pathlib import Path
from termcolor import cprint
import os

def get_embedding_ollama(text: str, model="nomic-embed-text") -> list[float]:
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434") # IN DOCKER IT IS "http://ollama:11434"
    url = f"{ollama_host}/api/embed"
    print(url)
    payload = {
        "model": model,
        "input": text
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("embeddings", [])[0]

# Testing this is the same
#get_embedding_ollama("This is a sample text") == ollama.embed("nomic-embed-text", "This is a sample text").get("embeddings", [])[0]


class ChromaVectorMemoryStore:
    def __init__(self, dim=768, collection_name: str = "docs", reset_on_init: bool = False, path: str = f"./src/mem_stores/"):  # 768 is correct for nomic
        vector_store = "chromadb_store"
        print(f"Using: {vector_store}")

        self.dim = dim
        self.path = Path(path + vector_store)
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Vector Store
        self.client = chromadb.PersistentClient(path=self.path, settings=chromadb.config.Settings(allow_reset=True))
        
        if collection_name is not None:
            self.collection = self.client.get_or_create_collection(name=collection_name)

            if reset_on_init:
                cprint("Resetting vector store...", "yellow")
                self.reset()


    def save(self, content:str, metadata=None):
        vec = np.array(get_embedding_ollama(content), dtype="float32")
        #print("Embedding length:", len(vec))
        unique_id = str(uuid.uuid4())
        cprint(f"Saved document with ID: {unique_id}. Content: {content}", "yellow")

        self.collection.add(
            ids=[unique_id],
            embeddings=np.array([vec]),
            documents=[content],
            metadatas=[metadata or {}]
        )

    def search(self, query:str, k:int=3, include_tags:list=[]):
        # generate an embedding for the input and retrieve the most relevant doc
        cprint(f"Vector search for query: {query}", "yellow")
        if self.count_all() == 0:
            cprint("No documents found in vector store.", "red")
            distances, unique_ids, metadatas, documents = [], [], [], []
        else:
            q_vec = np.array(get_embedding_ollama(query), dtype="float32")

            # Get the top k results from the collection                
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


            distances, unique_ids, metadatas, documents = results['distances'][0], results['ids'][0], results['metadatas'][0], results['documents'][0]
                

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
    
    def retrieve(self, query: str, alpha_importance:float =0.0, alpha_recency:float=0.0, alpha_similarity:float=1.0, num_results:int = 3):
        # Vector search
        contents, distances, cosine_similarities, recencies, importances = self.search(query, k=self.count_all(), include_tags=[])

        # Calculate scores based on importance, recency, and similarity
        cprint("\nContents reordered by SCORE:\nalpha_importance*importance + alpha_recency*0.995**recency + alpha_similarity*cosine_similarity", "yellow")

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
            
        results = sorted_contents[:num_results] if num_results < len(sorted_contents) else sorted_contents
        return results

    def reset(self):
        # Get all document IDs from the collection
        all_ids = self.collection.peek()["ids"]
    
        if all_ids:  # only delete if there are documents
            self.collection.delete(ids=all_ids)
            
        cprint("Vector store reset.", "yellow")
        
    def show_all(self):
        cprint("Vector store contents:", "yellow")
        if self.count_all() == 0:
            cprint("No documents found in vector store.", "red")
            return

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
        return len(self.collection.peek()["ids"])

