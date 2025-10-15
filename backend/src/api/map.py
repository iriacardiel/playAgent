import asyncio

import logging
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.neo4j import Neo4jService

logger = logging.getLogger(__name__)
router = APIRouter()
_graph_lock = asyncio.Lock()  # serialize access to the shared sync graph

@router.post("/map_features")
async def get_map_info():
    """Return GeoJSON FeatureCollections for nodes (points) and edges (lines)."""
    try:
        async with _graph_lock:          
            node_features, edge_features = await asyncio.to_thread(
                Neo4jService.get_map_features_sync
            )

        payload = {
            "nodes": {"type": "FeatureCollection", "features": node_features},
            "edges": {"type": "FeatureCollection", "features": edge_features},
            "status": "success",
        }

        return JSONResponse(content=payload)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating geojsons: {str(e)}")
