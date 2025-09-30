"""
Leaflet Maps Operations Module
- Reads nodes with `n.location` (point in WGS-84)
- Generates a GeoJSON FeatureCollection
- Writes a standalone Leaflet HTML file
"""
import json
from pathlib import Path
from termcolor import cprint

# -----------------------------
# 1) CONFIG
# -----------------------------

# Optional: default map center if fitting bounds fails (e.g., no points)
DEFAULT_ZOOM = 12

def rows_to_geojson(rows):
    """
    Convert query rows to a GeoJSON FeatureCollection (as a Python dict).
    """
    features = []
    for row in rows:
        labels = row["labels"] or []
        name = row["name"] or "Unknown"
        lon, lat =row["lon"], row["lat"]

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],  # GeoJSON expects [lon, lat]
            },
            "properties": {
                "name": name,
                "labels": labels,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def build_leaflet_html(geojson_str:str="", center_coordinates:list=[]):
    """
    Returns a complete, standalone HTML document string embedding the GeoJSON.
    """
    # Escape only for closing </script> edge case
    # (Leaflet data is JSON; we embed as a JS string then JSON.parse)
    geojson_js = geojson_str.replace("</script>", "<\\/script>")

    html_doc = f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Neo4j Locations</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Leaflet CSS -->
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  />
  <style>
    html, body, #map {{ height: 100%; margin: 0; }}
    .popup-name {{ font-weight: 600; margin-bottom: 4px; }}
    .legend {{
      position: absolute;
      z-index: 1000;
      bottom: 16px; left: 16px;
      background: white; padding: 8px 10px; border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,.15);
      font: 14px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    }}
    .legend span.badge {{
      display: inline-block; padding: 2px 6px; margin-right: 6px; border-radius: 999px; background: #eee;
    }}
  </style>
</head>
<body>
  <div id="map"></div>

  <!-- Leaflet JS -->
  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin="">
  </script>

  <script>
    // GeoJSON exported from Neo4j (as a JSON string to keep the file standalone)
    const geojson = `{geojson_js}`;
    const data = JSON.parse(geojson);

    // Build map
    const map = L.map('map').setView([{center_coordinates[0]}, {center_coordinates[1]}], {DEFAULT_ZOOM});

    // OSM tiles
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);

    // Simple icon color by label (first label wins). You can refine this.
    const labelColors = {{
      Person: '#2e7d32',
      Company: '#1565c0'
    }};

    function circleMarker(feature, latlng) {{
      const labels = (feature.properties && feature.properties.labels) || [];
      const primary = labels.length ? labels[0] : 'Other';
      const color = labelColors[primary] || '#6d4c41';
      return L.circleMarker(latlng, {{
        radius: 7,
        weight: 2,
        opacity: 1,
        color: color,
        fillOpacity: 0.15,
        fillColor: color
      }});
    }}

    const layer = L.geoJSON(data, {{
      pointToLayer: circleMarker,
      onEachFeature: (feature, layer) => {{
        const p = feature.properties || {{}};
        const name = p.name || 'Unknown';
        const labels = (p.labels || []).join(', ');
        layer.bindPopup(`<div class="popup-name">${{name}}</div>${{labels}}`);
      }}
    }}).addTo(map);

    // Fit bounds if we have features
    try {{
      const bounds = layer.getBounds();
      if (bounds.isValid()) {{
        map.fitBounds(bounds, {{ padding: [24, 24] }});
      }}
    }} catch (e) {{
      // Fall back to default center/zoom
    }}

    // Tiny legend
    const legend = L.control({{position: 'bottomleft'}});
    legend.onAdd = function() {{
      const div = L.DomUtil.create('div', 'legend');
      div.innerHTML = `
        <div><span class="badge" style="background:#2e7d32;"></span>Person</div>
        <div><span class="badge" style="background:#1565c0;"></span>Company</div>
      `;
      return div;
    }};
    legend.addTo(map);
  </script>
</body>
</html>
"""
    return html_doc


def create_map_from_rows(filename:str="",rows:list=[], center_coordinates:list=[]):
  
  try:
    
    # Convert to GeoJSON (Python dict -> JSON string)
    fc = rows_to_geojson(rows) 
    geojson_str = json.dumps(fc, ensure_ascii=False)
    
    # Build Leaflet HTML
    html_out = build_leaflet_html(geojson_str, center_coordinates) 
    
    # Write HTML to file
    Path(filename).write_text(html_out, encoding="utf-8")
    print(f"Map saved to {filename}")
  
  except Exception as e:
    cprint(f"An error occurred creating the leaflet map: {e}.", "red")
    
    return html_out