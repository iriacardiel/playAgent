from langchain.prompts import PromptTemplate


SIMPLE_QA_PROMPT_TEMPLATE = """
Anser to the query based on the following context retrieved from a Knowledge Graph through Vector Cosine Similarity.
    
Query: `{query}`
Context:\n`{llm_context}`
"""


CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:

# Show people
MATCH (p:Person) 
RETURN p.name as name, p.age as age, p.gender, p.education as education
ORDER BY age

# Show companies
MATCH (c:Company) 
RETURN c.name as name, c.industry as industry
ORDER BY industry

# Show text descriptions of the different nodes
MATCH (n) 
RETURN labels(n), n.name, n.text

# Show who knows who 
MATCH (a:Person)-[:KNOWS]-(b:Person)
WITH a, collect(b.name) AS known_people
RETURN a.name + " knows " + apoc.text.join(known_people, ", ")

# Show who knows Marta
MATCH (a:Person {{name:"Marta"}}))-[:KNOWS]-(b:Person)
WITH a, collect(b.name) AS list_people
RETURN a.name + " knows " + apoc.text.join(list_people, ", ")

# Show who who works where
MATCH (a:Person)-[:WORKS_AT]->(b:Company)
WITH a, collect(b.name) AS list_people
RETURN a.name + " works at " + apoc.text.join(list_people, ", ")

# Show distances between people and Iria
MATCH (p:Person {{name:"Iria"}}), (other:Person)
WITH p, other, point.distance(p.location, other.location) AS distance_m
RETURN p.name, other.name, round(distance_m/1000, 2) + " km" AS distance_km

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)
