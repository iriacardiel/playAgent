"""
Friends KG — Minimal Gradio UI
Two inputs + one map. Minimal controls, with send buttons.
Run: python frontend.py
"""
import gradio as gr
from urllib.parse import quote
from pathlib import Path

# Local QUERY Functions
from query_friends import vector_search_QA, generative_CQL_search_QA

# === Local services
from services.neo4j import Neo4jService

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
MAP_PATH = "data/friends/friends_map_"
CHOSEN_MAP = "folium.html" # "leaflet.html"

# ------------------------ Handlers ------------------------

Neo4jService.initialize()

def handle_vector(v_query, v_index_choice,v_top_k):
    """Run neo4j_KGRAG_search and return (map_html, answer_text, cypher_text)."""
    llm_context = ""
    if not v_query.strip():
        return "",""
    try:
        ans, llm_context = vector_search_QA(
                                query=v_query,
                                index=v_index_choice,
                                source_property="text",
                                main_property="name",
                                top_k=v_top_k
                                )

    except Exception as e:
        # minimal error surface
        return f"Vector search error: {e}", ""
    
    return ans, llm_context

def handle_cql(cql_query):
    """Run GraphCypherQAChain and return (answer_text, cypher_text)."""
    q = (cql_query or "").strip()
    answer, cypher = "", ""
    if not q:
        return "", "", ""
    try:
        answer, cypher, llm_context = generative_CQL_search_QA(q)
    except Exception as e:
        return f"CQL error: {e}", ""

    return answer, cypher, str(llm_context)
    
# def update_maps():

#     return Neo4jService.create_visualizations(directory=F"{HERE / "data/friends/friends_map_"}")


# def load_map_iframe(path=f"{HERE / MAP_PATH / CHOSEN_MAP}", height=600):
#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             html = f.read()
#         # Put the whole HTML into an iframe via data URL so scripts execute safely inside the iframe
#         return f'<iframe src="data:text/html;charset=utf-8,{quote(html)}" style="width:100%;height:{height}px;border:none;"></iframe>'
#     except Exception as e:
#         return f"<div style='color:#f88'>Could not load map: {e}</div>"
    
# # NEW: one function that both rebuilds the HTML files and returns a fresh iframe
# def refresh_map_and_iframe():
#     try:
#         update_maps()  # regenerates the folium html(s)
#     except Exception as e:
#         # Still try to show whatever exists while surfacing the error inline
#         return f"<div style='color:#f88'>Map update error: {e}</div>" 
#     # Now reload the iframe from disk so the UI shows the new map
#     return load_map_iframe()

# ------------------------ Theme & CSS ------------------------
# Use Soft theme as base (no extra kwargs — API changed)
theme = gr.themes.Soft()

# ------------------------ UI ------------------------
with gr.Blocks(theme=theme) as demo:
    gr.Markdown("# Friends KG — Search Console")
    
    # # Map area
    # map_html = gr.HTML(load_map_iframe())  # initial view
    # # AUTO: refresh map and iframe every 30 seconds (adjust as you like)
    # ticker = gr.Timer(value=5.0, active=True)
    # ticker.tick(refresh_map_and_iframe, inputs=None, outputs=map_html)
    
    with gr.Row(equal_height=True):
        # -------- Left Column: Vector Search --------
        with gr.Column(scale=1):
            gr.Markdown("### Vector Search")
            with gr.Row():
                v_query = gr.Textbox(label="Query", lines=2, placeholder="Does any girl have short hair?")
            with gr.Row():
                v_index_choice = gr.Dropdown(
                    choices=["person_node_idx", "company_node_idx", "know_relationship_idx"],
                    value="person_node_idx",
                    label="index"
                )
                v_top_k = gr.Number(label="top_k", value=5, precision=0)
            btn_vec = gr.Button("Run", variant="primary", size="sm")
            v_ans = gr.Textbox(label="Answer", interactive=False, lines=3)
            v_context = gr.Textbox(label="Retrieved Context", interactive=False, lines=3)

        # -------- Right Column: CQL GenAI --------
        with gr.Column(scale=1):
            gr.Markdown("### CQL GenAI")
            cql_query = gr.Textbox(label="Query", lines=2, placeholder="Who are Iria's friends?")
            btn_cql = gr.Button("Run", variant="primary", size="sm")
            cql_ans = gr.Textbox(label="Answer", interactive=False, lines=3)
            cql_cypher = gr.Textbox(label="Generated Cypher", interactive=False, lines=3)
            cql_context = gr.Textbox(label="Retrieved Context", interactive=False, lines=3)
            
    # Wire up buttons
    btn_vec.click(
        handle_vector,
        inputs=[v_query, v_index_choice, v_top_k],
        outputs=[v_ans, v_context]
    )
    btn_cql.click(
        handle_cql,
        inputs=[cql_query],
        outputs=[cql_ans, cql_cypher, cql_context]
    )

demo.launch()