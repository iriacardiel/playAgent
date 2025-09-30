"""
Folium Maps Operations Module
"""
import folium
from termcolor import cprint

def create_map_from_rows(filename:str="",rows:list=[], center_coordinates:list=[]):
    
    try:
        m = folium.Map(location=center_coordinates, zoom_start=12)
        for r in rows:
            folium.Marker([r.get("lat",0.0), r.get("lon",0.0)],
                            popup=str({k: v for k, v in r.items()})).add_to(m)
        if filename:
            m.save(filename)
            print(f"Map saved to {filename}")
    except Exception as e:
        cprint(f"An error occurred creating the folium map: {e}.", "red")
        
        return m._repr_html_()