import logging
import os
import tempfile
import traceback
from termcolor import cprint

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import Settings
from services.neo4j import Neo4jService

logger = logging.getLogger(__name__)
router = APIRouter()

def _feature_collection(features):
    return {"type": "FeatureCollection", "features": features}

@router.post("/map_info")
async def get_map_info():
    """Return GeoJSON FeatureCollections for nodes (points) and edges (lines)."""
    try:
        
        graph = Neo4jService.get_graph()
        
        # --- Query your Neo4j (adapt to your driver) ---
        # Nodes with coordinates
        node_query = """
        MATCH (n)
        WHERE n.location.latitude IS NOT NULL AND n.location.longitude IS NOT NULL
        RETURN n.uuid AS id, n.name AS name, labels(n) AS labels,
               n.location.latitude AS lat, n.location.longitude AS lon
        """

        # Relationships where both ends have coordinates
        rel_query = """
        MATCH (a)-[r]-(b)
        WHERE a.location.latitude IS NOT NULL AND a.location.longitude IS NOT NULL
          AND b.location.latitude IS NOT NULL AND b.location.longitude IS NOT NULL
        RETURN a.uuid AS src_id, b.uuid AS dst_id, type(r) AS rel_type,
               a.location.latitude AS a_lat, a.location.longitude AS a_lon,
               b.location.latitude AS b_lat, b.location.longitude AS b_lon
        """

        # Replace `graph.query` with your actual execution:
        nodes = graph.query(node_query)  # -> list[dict]
        rels  = graph.query(rel_query)   # -> list[dict]

        # --- Build GeoJSON for nodes ---
        node_features = []
        node_index = {}  # id -> feature props (or entire feature)
        for n in nodes:
            nid = n.get("id")
            lat, lon = n.get("lat"), n.get("lon")
            if lat is None or lon is None:
                continue
            props = {
                "id": nid,
                "name": n.get("name") or "Unknown",
                "labels": n.get("labels") or [],
            }
            feat = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props,
            }
            node_features.append(feat)
            node_index[nid] = props

        # --- Build GeoJSON for edges (dedupe) ---
        seen = set()
        edge_features = []
        for e in rels:
            src, dst = e.get("src_id"), e.get("dst_id")
            # dedupe (undirected); include rel_type in key so parallel types show
            key = (min(src, dst), max(src, dst), e.get("rel_type"))
            if key in seen:
                continue
            seen.add(key)

            a_lat, a_lon = e.get("a_lat"), e.get("a_lon")
            b_lat, b_lon = e.get("b_lat"), e.get("b_lon")
            if None in (a_lat, a_lon, b_lat, b_lon):
                continue

            feat = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[a_lon, a_lat], [b_lon, b_lat]],
                },
                "properties": {
                    "src_id": src,
                    "dst_id": dst,
                    "rel_type": e.get("rel_type", "RELATED"),
                    "src_name": node_index.get(src, {}).get("name", str(src)),
                    "dst_name": node_index.get(dst, {}).get("name", str(dst)),
                },
            }
            edge_features.append(feat)

        payload = {
            "nodes": _feature_collection(node_features),
            "edges": _feature_collection(edge_features),
            "status": "success",
        }

        return JSONResponse(content=payload)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating geojsons: {str(e)}")
