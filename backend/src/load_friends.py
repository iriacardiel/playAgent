"""
Friends KG - Ingestion / Load script
"""

# === Dependencies
import json
from termcolor import cprint
from pathlib import Path

from services.neo4j import Neo4jService

Neo4jService.initialize()
HERE = Path(__file__).parent
# -----------------------------------------------------------------------------
# Ingestion
# -----------------------------------------------------------------------------
def ingest() -> None:

    # Constraints
    Neo4jService.create_constraint(node_label="Person",node_unique_key="uuid")
    Neo4jService.create_constraint(node_label="Company",node_unique_key="uuid")
        
    # Clean up graph
    Neo4jService.reset_graph()  
        
    # Vector indexes
    Neo4jService.create_vector_index(index_name="person_node_idx", node_label="Person")
    Neo4jService.create_vector_index(index_name="company_node_idx", node_label="Company")
    Neo4jService.create_vector_index(index_name="know_relationship_idx", relation_type="KNOWS")
    Neo4jService.show_vector_indexes()

    # Data
    
    with open(HERE / "data/friends/friends.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # People
    for p in data["people"]:
        
        Neo4jService.create_node(
            label="Person",
            props={
                "name": p.get("name",""),
                "age": p.get("age",0),
                "gender": p.get("gender",""),
                "education": p.get("education",""),
                "latitude": p.get("latitude",0.0),
                "longitude":p.get("longitude",0.0),
            },
            text_template=f"{p.get("name","")} is a {p.get("age",0)} of {p.get("gender","")} years old and studied {p.get("education","")}. {p.get("extra_text", "")}",
            location_keys=("latitude", "longitude"),
            vectorize=True,
            source_property="text",
        )

    # Companies
    for c in data["companies"]:

        Neo4jService.create_node(
            label="Company",
            props={
                "name": c.get("name",""),
                "industry": c.get("industry",0),
                "latitude": c.get("latitude",0.0),
                "longitude":c.get("longitude",0.0),
            },
            text_template=f"{c.get("name","")} operates in the {c.get("industry",0)} Industry. {c.get("extra_text", "")}",
            location_keys=("latitude", "longitude"),
            vectorize=True,
            source_property="text",
        )


    # Person ↔ Person relationships
    for r in data["person_person_relations"]:

        Neo4jService.create_relationship(
            start_label="Person",
            end_label="Person",
            rel_type="KNOWS",
            start_value=r.get("start_person",""),
            end_value=r.get("end_person",""),
            rel_props={"knows_from": r.get("knows_from",""), "text": r.get("text","")},
            vectorize=True,
            source_property="text",
        )
        

    # Person ↔ Company relationships
    for r in data["person_company_relations"]:
        
        Neo4jService.create_relationship(
            start_label="Person",
            end_label="Company",
            rel_type="WORKS_AT",
            start_key="name",
            end_key="name",
            start_value=r.get("person",""),
            end_value=r.get("company",""),
            rel_props={"since": r.get("since",0)},
        )

    # Plot nodes into maps
    Neo4jService.create_visualizations(directory=F"{HERE / "data/friends/friends_map_"}")

    cprint("\nIngestion completed successfully.", "green")


def main() -> None:
    try:
        ingest()
    except Exception as e:
        cprint(f"\nERROR: {e}", "red")
        
if __name__ == "__main__":
    main()
        