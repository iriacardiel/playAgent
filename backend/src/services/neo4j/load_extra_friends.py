"""
Friends KG - Ingestion / Load script
"""

# === Dependencies
import json
from termcolor import cprint
from pathlib import Path

# === Local services
from services.neo4j import Neo4jService

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
HERE = Path(__file__).parent

# -----------------------------------------------------------------------------
# Ingestion
# -----------------------------------------------------------------------------

def ingest() -> None:

    # Data
    with open(HERE / "data/friends/extra_friends.json", "r", encoding="utf-8") as f:
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

    cprint("\nIngestion completed successfully.", "green")


def main() -> None:
    try:
        Neo4jService.initialize()
        Neo4jService.show_schema()
        ingest()
    except Exception as e:
        cprint(f"\nERROR: {e}", "red")
        
if __name__ == "__main__":
    main()
        