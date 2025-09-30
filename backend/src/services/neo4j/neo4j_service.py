import asyncio
import logging
import traceback
from typing import Any
from typing import Literal, Optional, List, Dict, Any, Union, Callable, Mapping, Iterable

from termcolor import cprint
from pprint import pprint

from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
import ollama

from config import Settings
from services.neo4j.prompts import CYPHER_GENERATION_PROMPT
from helpers import helper_leaflet, helper_folium, helper_ollama

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
NEO4J_URI ="bolt://localhost:"+Settings.NEO4J_URI_PORT

class Neo4jService:
    """Neo4j service
    """

    _initialized = False
    _graph: Neo4jGraph = None
    _cypherChain: GraphCypherQAChain = None
    _llm: Any = None

    @classmethod
    def initialize(cls):
        """Initialize the Neo4j service."""
        if cls._initialized:
            logger.warning("TrackService already initialized")
            return

        try:
            cprint(f"Initializing graph at {NEO4J_URI}", "green")
            cls._graph = Neo4jGraph(
                url=NEO4J_URI,
                username=Settings.NEO4J_USER,
                password=Settings.NEO4J_PASSWORD,
            )
            cls._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize TrackService: {e}")
            traceback.print_exc()
            raise

    @classmethod
    def get_cypher_chain(cls) -> GraphCypherQAChain:
        """Get the Cypher QA chain for querying the Neo4j graph."""
        if not cls._cypherChain:
            if not cls._llm:
                raise ValueError("LLM not set for Cypher QA chain")

            cls._cypherChain = GraphCypherQAChain.from_llm(
                cls._llm,
                graph=cls.get_graph(),
                verbose=True,
                cypher_prompt=CYPHER_GENERATION_PROMPT,
                allow_dangerous_requests=True,
                return_direct=False,
                top_k=100,
                return_intermediate_steps=True,
            )

        return cls._cypherChain

    @classmethod
    def get_graph(cls):
        """Get the Neo4j graph instance."""
        if not cls._initialized or not cls._graph:
            cls.initialize()

        return cls._graph

    @classmethod
    def set_llm(cls, llm) -> None:
        """Set the LLM for the Cypher QA chain."""
        cls._llm = llm
        cls._cypherChain = None
        
        
    @classmethod
    def reset_graph(cls) -> None:
        
        try:
            cls._graph.query("CALL apoc.schema.assert({}, {})")
            cls._graph.query("MATCH (n) DETACH DELETE n")
        except Exception as e:
            cprint(f"An error occurred restoring graph: {e}.", "red")
            
    @classmethod
    def show_schema(cls) -> None:
        # Refresh and print the LLM-friendly schema summary
        cls._graph.refresh_schema()
        print(cls._graph.schema) # readable string: labels, rel-types, properties

    
    @classmethod  
    def create_constraint(cls, node_label:str="", node_unique_key:str=""):
        
        try:
            
            constraint_name = node_label.lower() + "_unique"
            query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (p:{node_label}) REQUIRE p.{node_unique_key} IS UNIQUE
            """
            cls._graph.query(query)
        
        except Exception as e:
            cprint(f"An error occurred creating constraint: {e}.", "red")    
    
    @classmethod  
    def vectorize_property(
        cls,
        element: Literal["node", "relationship"]="node",
        node_label: Optional[str]="",
        rel_type: Optional[str]="",
        source_property: str=""
    ) -> None:
        """
        Generate and store vector embeddings for specified property of nodes or relationships.
        
        This function processes all nodes or relationships of a given label or type that have
        non-empty values for the specified property and generates embeddings for them.
        Only processes items that don't already have embeddings.
        
        Args:
            element: Type of graph element - either "node" or "relationship"
            node_label: Label of the node to process
            rel_type: Type of the relationship to process
            source_property: Name of the property to vectorize
            
        Note:
            Only one of 'node_label' or 'rel_type' must be provided.
        """
        
        # Input control
        try:
            if node_label and rel_type:
                raise ValueError("Only one of 'node_label' or 'rel_type' must be provided.")
            elif element == "node" and not node_label:
                raise ValueError("Provide 'node_label' for element 'node'.")
            elif element == "relationship" and not rel_type:
                raise ValueError("Provide 'rel_type' for element 'relationship'.")

            # Vectorize node property
            if element == "node":

                cprint(f"\nGenerating embeddings for (n:{node_label}) on n.{source_property}", "green")
                
                # Query for nodes without embeddings
                query = f"""
                    MATCH (n:{node_label})
                    WHERE 
                        n.{source_property} IS NOT NULL AND 
                        n.{source_property} <> '' AND 
                        n.embedding IS NULL
                    RETURN 
                        n.uuid AS uuid,
                        n.{source_property} AS txt
                """
                
                records = list(cls._graph.query(query))
                
                # Set embedding property for each record
                count = 0
                for record in records:
                    
                    # Create embedding vector
                    vec = helper_ollama.create_embedding(input_text=record["txt"])
                    
                    # Update node with embedding
                    update_query = f"""
                        MATCH (n:{node_label} {{uuid: $uuid}})
                        SET n.embedding = $vec
                    """
                    cls._graph.query(update_query, {"uuid": record["uuid"], "vec": vec})
                    
                    # Debug output
                    count+=1
                    print(f" Updated {count} embeddings")

            # Vectorize relationship property 
            elif element == "relationship":

                cprint(f"\nGenerating embeddings for [r:{rel_type}] on r.{source_property}", "green")
                
                # Query for relationships without embeddings
                query = f"""
                    MATCH ()-[r:{rel_type}]-()
                    WHERE 
                        r.{source_property} IS NOT NULL AND 
                        r.{source_property} <> '' AND 
                        r.embedding IS NULL
                    RETURN 
                        r.uuid AS uuid, 
                        r.{source_property} AS txt
                """
                
                records = list(cls._graph.query(query))
                
                # Set embedding property for each record
                count = 0
                for record in records:
                    
                    # Create embedding vector
                    vec = helper_ollama.create_embedding(input_text=record["txt"])
                    
                    # Update relationship with embedding
                    update_query = f"""
                        MATCH ()-[r:{rel_type} {{uuid: $uuid}}]-()
                        SET r.embedding = $vec
                    """
                    cls._graph.query(update_query, {"uuid": record["uuid"], "vec": vec})
                    
                    # Debug output
                    count+=1
                    print(f" Updated {count} embeddings")
        
        except Exception as e:
            cprint(f"An error occurred vectorizing properties {e}.", "red")

    @classmethod  
    def create_vector_index(cls, index_name: str = '',
                            node_label: Optional[str] = '',
                            relation_type: Optional[str] = '',
                            emb_property: Optional[str] = Settings.EMB_PROPERTY,
                            dim: Optional[int] = Settings.EMB_DIMENSION,
                            similarity: Optional[str] = Settings.EMB_SIMILARITY):
        cprint(Settings.EMB_SIMILARITY, "magenta")
        try:
            if relation_type:
                # For relationship index
                query = f"""
                CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                FOR ()-[r:{relation_type}]-() ON (r.{emb_property})
                OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dim}, `vector.similarity_function`: '{similarity}' }} }}
                """
            elif node_label:
                # For node index
                query = f"""
                CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                FOR (n:{node_label}) ON (n.{emb_property})
                OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dim}, `vector.similarity_function`: '{similarity}' }} }}
                """
            else:
                raise ValueError("Either node_label or relation_type must be provided")
            
            cls._graph.query(query)
            print(f"Successfully created index {index_name}.")
            
        except Exception as e:
            cprint(f"An error occurred creating vector index {e}.","red")
    
    @classmethod
    def show_vector_indexes(cls):
        # Show created vector indexes
        results = cls._graph.query("SHOW VECTOR INDEXES")
        idx = list(results)
        cprint(f"\nFound {len(idx)} vector index entries.", "green")
        for r in idx:
            cprint("-"*20,"green")
            pprint(r)  
            
    @classmethod
    def create_node(
        cls,
        label: str,
        props: dict,
        text_template: str | None = None,   # e.g. "{name} is a {age} of {gender} years old..."
        text_key: str = "text",
        location_keys: tuple[str, str] | None = None,  # e.g. ("latitude","longitude") in props
        uuid_key: str = "uuid",
        vectorize: bool = True,
        source_property: str = "text",
    ):
        """
        Generic node creator:
        - label: Neo4j label to create (string, validated).
        - props: dict of properties to set (name, age, gender, education, etc.).
        - text_template: optional Python format string to compute a 'text' property from props.
        - text_key: name of the property to store the rendered text in.
        - location_keys: optional (lat_key, lon_key) in props to turn into point().
        - uuid_key: property to store UUID; generated in Cypher if missing.
        - vectorize: whether to call your embedding helper afterward.
        - source_property: property to vectorize (default "text").
        """
        # 1) Compute derived 'text' if requested
        computed_props = dict(props)  # shallow copy
        if text_template:
            try:
                computed_props[text_key] = text_template.format(**props)
            except KeyError as e:
                missing = e.args[0]
                raise KeyError(f"Missing key {missing!r} required by text_template") from e

        # 2) Pull out location if asked, so we can call point($location) in Cypher
        location_param = None
        if location_keys:
            lat_key, lon_key = location_keys
            if lat_key in computed_props and lon_key in computed_props:
                location_param = {
                    "latitude": computed_props.pop(lat_key),
                    "longitude": computed_props.pop(lon_key),
                }

        # 3) Build Cypher
        cypher_lines = [
            f"CREATE (n:{label})",
            "SET n += $props",
            f"SET n.{uuid_key} = coalesce(n.{uuid_key}, randomUUID())",
        ]
        if location_param is not None:
            cypher_lines.append("SET n.location = point($location)")
        cypher_lines.append("RETURN n")

        query = "\n".join(cypher_lines)

        # 4) Params
        params = {"props": computed_props}
        if location_param is not None:
            params["location"] = location_param

        # 5) Execute
        try:
            cls._graph.query(query, params)
            print(f"Successfully created {label}: {computed_props}")
        except Exception as e:
            cprint(f"An error occurred creating node: {e}.", "red")
            return

        # 6) Optional vectorization
        if vectorize:
            cls.vectorize_property(
                element="node",      # "node"
                node_label= label,
                source_property=source_property,
            )
        
    
    @classmethod
    def create_relationship(
        cls,
        start_label: str,
        end_label: str,
        rel_type: str,
        start_key: str = "name",
        end_key: str = "name",
        start_value=None,
        end_value=None,
        rel_props: dict | None = None,
        uuid_key: str = "uuid",
        vectorize: bool = False,
        source_property: str = "text",
    ):
        """
        Generic relationship creator between two matched nodes, idempotent via MERGE.
        - Matches each node by a single key=val (fast & index-friendly).
        - Sets any provided rel_props on CREATE (via r += $rel_props) and ensures r.uuid.
        - Optional embedding/vectorization for relationship text, etc.
        """

        query_lines = [
            f"MATCH (a:{start_label} {{{start_key}: $start_value}})",
            f"MATCH (b:{end_label} {{{end_key}: $end_value}})",
            f"MERGE (a)-[r:{rel_type}]->(b)",
            f"ON CREATE SET r.{uuid_key} = coalesce(r.{uuid_key}, randomUUID())",
        ]
        if rel_props:
            query_lines.append("ON CREATE SET r += $rel_props")
        
        query_lines.append("RETURN a, r, b")

        params = {
            "start_value": start_value,
            "end_value": end_value,
        }
        if rel_props:
            params["rel_props"] = rel_props

        try:
            cls._graph.query("\n".join(query_lines), params)
            print(f"Successfully created {rel_type}: {{start: {start_value}, end: {end_value}, rel_props: {rel_props or {}}}}")
        except Exception as e:
            cprint(f"An error occurred creatin relationship: {e}.", "red")
            return

        if vectorize:
            # Generic embedding over relationships
            cls.vectorize_property(
                element="relationship",
                rel_type=rel_type,
                source_property=source_property,
            )
        
    @classmethod
    def create_visualizations(cls, directory:str=""):
        
        try:
            query = """
            MATCH (n)
            RETURN 
            n.name AS name, labels(n) AS labels,
            n.location.latitude AS lat, 
            n.location.longitude AS lon
            """
            
            records = cls._graph.query(query) # ["name":"","lat":..,"lon":..,"labels":[".."]},...]
        except Exception as e:
            cprint(f"An error occurred creating visualizations: {e}.", "red")
        
        # Follium map
        html_out = helper_folium.create_map_from_rows(filename=directory+"folium.html",rows=records,center_coordinates=[40.4168, -3.7038])
        # Leaflet map
        helper_leaflet.create_map_from_rows(filename=directory+"leaflet.html", rows=records, center_coordinates=[40.4168, -3.7038])

        return html_out
    
    @classmethod
    def neo4j_KGRAG_search(
        cls,
        query: str,
        index: str, 
        source_property : str,
        main_property : str,
        top_k: int,
    ) -> Dict[str, Any]:
        """
        Perform KG RAG retrieval: vector search + context preparation for agent consumption
        
        - Combines vector search with context formatting specifically for RAG (Retrieval-Augmented Generation) use cases.
        - Searches for the most similar nodes or relationships to a given query using Neo4j's vector index capabilities.
        
        Args:
            element: Type of element to search - "node" or "relationship"
            node_label: Label of the node to process
            rel_type: Type of the relationship to process
            query: Query text to find similar items for
            index: Name of the vector index to use for search
            source_property: Property containing the text content to retrieve
            main_property: Property that best represents the a node (name, title, etc.). It is used to build the context for the LLM.
            top_k: Number of most similar results to return
            
        Returns:
            Dictionary containing structured RAG context ready for agent consumption

        """
        
        if "node" in index:
            element = "node"
        elif "relationship" in index:
            element = "relationship"
        else:
            raise ValueError("Index name does not provide enough information about element type.")
            
        
        # (1) Generate embedding for the search query
        query_embedding = helper_ollama.create_embedding(query)
        
        # (2) Build default retrieval query based on element type
        if element == "node":
            default_vector_search_query = f"""
                CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding) 
                YIELD node, score
                
                WITH node, score
                
                RETURN 
                    score,
                    labels(node) AS label,
                    node {{.*}} AS properties_dict
                    
                ORDER BY score DESC
            """
            
            vector_search_query = f"""
                CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
                YIELD node, score
                WITH node, score, ['embedding','uuid'] as drop
                WITH node, score, drop,
                    [(node)-[r]->(neighbour) |
                        node[$main_property] +
                        " -[" + type(r) + " " + coalesce(apoc.convert.toJson(apoc.map.removeKeys(properties(r),  drop)), "") + "]-> " +
                        neighbour[$main_property]
                    ] +
                    [(neighbour)-[r]->(node) |
                        neighbour[$main_property] + 
                        " -[" + type(r) + " " + coalesce(apoc.convert.toJson(apoc.map.removeKeys(properties(r),  drop)), "") + "]-> " + 
                        node[$main_property]
                    ] AS f
                    
                RETURN
                    score,
                    labels(node) AS label,
                    apoc.map.removeKeys(node {{.*}}, drop) AS properties_dict,
                    f as facts
                    
                ORDER BY score DESC
            """
            
        elif element == "relationship":
            
            default_vector_search_query = f"""
                CALL db.index.vector.queryRelationships($index_name, $top_k, $query_embedding) 
                YIELD relationship AS r, score
                WITH r, score
                RETURN 
                    score, 
                    type(r) as type,
                    r {{.*}} AS properties_dict
                ORDER BY score DESC
            """

            vector_search_query = f"""
            CALL db.index.vector.queryRelationships($index_name, $top_k, $query_embedding)
            YIELD relationship AS r, score
            WITH r, score, ['embedding','uuid'] as drop
            WITH r, score, drop,
                [
                startNode(r)[$main_property] +
                " -[" + type(r) + " " + coalesce(apoc.convert.toJson(apoc.map.removeKeys(properties(r),  drop)), "") + "]-> " + 
                endNode(r)[$main_property]
                ] AS f
            
            RETURN
                score,
                type(r) as type,
                apoc.map.removeKeys(r {{.*}}, drop) AS properties_dict,
                f as facts
            ORDER BY score DESC
            """
        else:
            raise ValueError(f"Invalid element type: {element}. Must be 'node' or 'relationship'")
        
        # (3) Execute search query
        
        search_parameters = {
            "element" : element, # not used
            "source_property": source_property, # not used
            "main_property": main_property,
            "index_name": index, 
            "top_k": top_k,
            "query_embedding": query_embedding
        }
        
        cprint(f"\nRunning vector search query to retrieve context.", "blue")
        raw_results = cls._graph.query(vector_search_query, search_parameters)
        
        if isinstance(raw_results, list):
            raw_search_results = raw_results
        else:
            raw_search_results = []
            for r in raw_results:
                raw_search_results.append(dict(r))
            
        # (4) Process results for RAG consumption into a combined_context for the LLM

        processed_search_results = []
        combined_context = ""
        
        for i, result in enumerate(list(raw_results)):
            
            result_dict = dict(result)
            
            score = round(result_dict.get('score', 0.0), 3)
            node_label = result_dict.get('label','')
            rel_type = result_dict.get('type','')
            properties = result_dict.get('properties_dict',{})
            properties_str = ''.join(f"\n-{k}: {v}" for k, v in properties.items() if k not in [source_property])
            text_content = properties.get(source_property,'')
            facts = result_dict.get('facts', '')
            facts_str = ''.join(f"\n-{f}" for f in facts)
            
            if element == "node":
                processed_result = {
                    "index": i,
                    "score": score,
                    "node_label": node_label,
                    "properties": properties,
                    "facts" : facts
                }
                combined_context += f"RESULT #{i+1}: {node_label[0]} node\nSCORE: {score}\nSOURCE TEXT: {text_content}\nPROPERTIES:{properties_str}\nFACTS:{facts_str}\n{'-'*40}\n"

            elif element == "relationship":

                processed_result = {
                    "index": i,
                    "score": score,
                    "relationship_type": rel_type,
                    "properties": properties,
                    "facts" : facts
                }
                combined_context += f"RESULT #{i+1}: {rel_type} relationship\nSCORE: {score}\nSOURCE TEXT: {text_content}\nPROPERTIES:{properties_str}\nFACTS:{facts_str}\n{'-'*40}\n"

            
            processed_search_results.append(processed_result)
        
        # Return structured context for agent
        output = {
            "query": query,
            "total_results": len(processed_search_results),
            "raw_search_results" : raw_search_results,
            "processed_search_results": processed_search_results,
            "combined_context": combined_context, # <<<<< LLM Context
            "search_metadata": {
                "element": element,
                "source_property": source_property,
                "index_used": index,
                "top_k": top_k,
            }
        }

        return output


async def main() -> None:
    from config import Settings
    print("yuhy")
    await Neo4jService.initialize()

    while True:
        try:
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())