import random
import time
from services.neo4j import Neo4jService

def move_all_people_randomly(n_iterations, max_distance_meters=100):
    """
    Move all people randomly for N iterations.
    
    Args:
        n_iterations: Number of times to move each person
        max_distance_meters: Maximum distance to move in any direction per iteration
    """
    R = 6378137.0  # Earth's radius in meters
    
    # Get all person UUIDs
    get_people_query = "MATCH (p:Person) RETURN p.uuid AS uuid"
    people = Neo4jService.get_graph().query(get_people_query)
    person_uuids = [person['uuid'] for person in people]
    
    print(f"Moving {len(person_uuids)} people for {n_iterations} iterations...")
    
    # Update query
    update_query = """
    MATCH (p:Person {uuid: $uuid})
    WITH p, 
         p.location.latitude AS lat,
         p.location.longitude AS lon
    SET p.location = point({
        latitude: lat + degrees($dy / $R),
        longitude: lon + degrees($dx / ($R * cos(radians(lat))))
    })
    RETURN p.location
    """
    
    for iteration in range(n_iterations):
        print(f"Iteration {iteration + 1}/{n_iterations}")
        for person_uuid in person_uuids:
            # Generate random offset
            dx = random.uniform(-max_distance_meters, max_distance_meters)
            dy = random.uniform(-max_distance_meters, max_distance_meters)
            
            # Update location
            Neo4jService.get_graph().query(
                update_query, 
                params={'uuid': person_uuid, 'dx': dx, 'dy': dy, 'R': R}
            )
        
        time.sleep(2)
    
    print(f"Completed {n_iterations} iterations for {len(person_uuids)} people")

if __name__ == "__main__":
    # Example usage:
    Neo4jService.initialize()
    move_all_people_randomly(n_iterations=100, max_distance_meters=300)