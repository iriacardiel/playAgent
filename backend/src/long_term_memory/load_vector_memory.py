from long_term_memory.vector_store import ChromaVectorMemoryStore
from datetime import datetime
import time
import ollama
import numpy as np
from termcolor import cprint

MODE = "LOAD"  # "LOAD" / "READ"

if __name__ == "__main__":

    if MODE == "LOAD":
        # Initialize Vector Memory Store
        vector_store = ChromaVectorMemoryStore(collection_name="DORI_memories", reset_on_init=True)

        # Step 1: Save (store)
        # =====================

        documents = [
        {"content": "The name 'DORI' is inspired by the Nemo character Dory, who is known for her short-term memory loss. This is an internal joke and a reminder that DORI is designed to help users with their short-term memories. The idea was originally proposed by Javier Carrera, who is the coworker of the authors of this project.",
        "metadata": {"tags": "DORI_history", 
                    "importance": "4"}},
        {"content": "The authors of this project, and creators of DORI, are Guillermo Escolano (Industrial Engineer) and Iria Cardiel (Physicist). They both work as AI Software Developers in the world of LLMs and AI Agents. This is their first project together.",
        "metadata": {"tags": "DORI_history", 
                        "importance": "5"}},
        {"content": "Iria was born in 1998 in Alcorcon, Spain. She is has experience in AI in consulting firms.",
        "metadata": {"tags": "user_history",
                        "importance": "3"}},
        {"content": "Iria is passionate about yoga and music",
            "metadata": {"tags": "user_preferences",
                            "importance": "3"}},
        {"content": "Guillermo was born in 1998 in Madrid, Spain. He is always up to date with the latest AI news.",
        "metadata": {"tags": "user_history", 
                    "importance": "3"}},
        {"content": "Guillermo is passionate about sports, especially basketball.",
        "metadata": {"tags": "user_preferences", 
                    "importance": "3"}},
        {"content": "Iria has a cat named 'Agata'.",
        "metadata": {"tags": "user_info,animals", 
                        "importance": "2"}},
        {"content": "Guillermo is a dog person.",
        "metadata": {"tags": "user_info,animals", 
                    "importance": "2"}},
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
        query = "Female author's preferences"

        results = vector_store.retrieve(
            query=query,
            alpha_importance=0.0,
            alpha_recency=0.0,
            alpha_similarity=1.0,
            num_results=8
        )
            
            
        # Step 3: Generate
        # ================
        # generate a response combining the prompt and data we retrieved in step 2
        generation_prompt = f"Using this data:\n{results}.\nRespond to this prompt:\n{query}"

        output = ollama.generate(
        model="mistral-small3.2:24b",
        prompt=generation_prompt
        )

        cprint(f"GENERATION PROMPT: {generation_prompt}", "green")
        cprint(f"GENERATION OUTPUT: {output['response']}", "blue")
        
        #vector_store.reset()
        
    elif MODE == "READ":
        # Initialize Vector Memory Store
        vector_store = ChromaVectorMemoryStore(collection_name="DORI_memories", reset_on_init=False)
        
        # List all collections
        cprint("Collections...", "yellow")
        for c in vector_store.client.list_collections():
            print(f"COLLECTION {c.name} has {c.count()} records")

            for i, r in enumerate(c.peek(limit=c.count())["documents"]):
                print(f"  Document {i}: {r}")

    elif MODE == "DELETE_ALL":
        # DELETING EMPTY COLLECTIONS
        # Initialize Vector Memory Store
        vector_store = ChromaVectorMemoryStore(collection_name=None, reset_on_init=False)

        cprint("Deleting empty collections...", "yellow")
        for c in vector_store.client.list_collections():
            print(c.name)
            print(c.count())
            if c.count() == 0:
                cprint(f"Deleting empty collection: {c.name}", "red")
                vector_store.client.delete_collection(name=c.name)
            

        