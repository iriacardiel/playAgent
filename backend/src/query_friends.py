"""
Friends KG - Search & Retrieval Script
"""
# === Dependencies
from termcolor import cprint
from pathlib import Path

# === Neo4j / LangChain
from langchain_google_vertexai import ChatVertexAI
from langchain_ollama import ChatOllama

# === Local services
from services.neo4j import Neo4jService, prompts

# == Local settings
from config.settings import Settings

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
MODEL_SERVER = Settings.MODEL_SERVER
MODEL_NAME = Settings.MODEL_NAME

cprint(f"\nUsing LLM {MODEL_NAME} through {MODEL_SERVER}.", "green")
if MODEL_SERVER == "OLLAMA":
  llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0.2,
        num_ctx=16000,
        n_seq_max=1,
        extract_reasoning=False,
    )
  
if MODEL_SERVER == "VERTEX":
  
  llm = ChatVertexAI(
    model=MODEL_NAME,   # or "gemini-2.5-pro"
    temperature=0.2,
    max_output_tokens=1000,
    location="us-central1",     # or "europe-west1"
  )
  


Neo4jService.initialize()

# ----------------------------------------------------
# Vector Search with predefined queries:
#  user query -> predefined CQL query -> context -> LLM -> answer
# ----------------------------------------------------
def vector_search_QA(
    query: str,
    index: str, 
    source_property : str,
    main_property : str,
    top_k: int) -> str:

    # Query KG 
    # --------
    result = Neo4jService.neo4j_KGRAG_search(
                                query = query, 
                                index = index,
                                source_property = source_property,
                                main_property =main_property,
                                top_k = top_k
                                )
    
    # Build prompt
    # ------------
    llm_context = result.get("combined_context", "")
    prompt = prompts.SIMPLE_QA_PROMPT_TEMPLATE.format(query=query, llm_context=llm_context)
    cprint(prompt, "magenta")

    # Call LLM
    # --------
    llm_output = llm.invoke(prompt)
    response = llm_output.content
    cprint(response, "cyan")
    print("#"*60)
    print()
    return response, llm_context
      
  
# -----------------------------------------------------------------------------
# CQL Search with LLM Generated queries
#  user query -> LLM -> Generated CQL query -> context -> LLM -> answer
# -----------------------------------------------------------------------------

def generative_CQL_search_QA(query):

    # Langchain Chain: user query -> LLM -> Generated CQL query -> context -> LLM -> answer
    # -------------------------------------------------------------------------------------
    Neo4jService.set_llm(llm)
    cypher_chain = Neo4jService.get_cypher_chain()
    cprint(query, "magenta")
    
    # Call LLM Chain
    # --------------
    out = cypher_chain.invoke(query)
    response = out.get("result","")
    steps = out.get("intermediate_steps") or []
    if steps:
      cypher = steps[0].get("query") 
      context = steps[1].get("context")
    cprint(response, "cyan")
    print("#"*60)
    print()

    return response, cypher, context

  
# KG RAG Search
if __name__ == "__main__":
  
  vector_search_QA(query = "Does any girl have short hair?", 
                   index = "person_node_idx", 
                   source_property = "text", 
                   main_property = "name", 
                   top_k = 3)
  
  vector_search_QA(query = "Which company has more employes belonging to the graph?", 
                   index = "company_node_idx", 
                   source_property = "text",  
                   main_property = "name", 
                   top_k = 3)
  
  vector_search_QA(query = "Who's Iria's best friend?", 
                   index = "know_relationship_idx", 
                   source_property = "text",  
                   main_property = "name", 
                   top_k = 3)

  generative_CQL_search_QA(query = "Who are Iria's friends?")
  generative_CQL_search_QA(query = "List people that work at Lumon but do not know Paula?")
  generative_CQL_search_QA(query = "Who is closest to Marina and by how much distance?")