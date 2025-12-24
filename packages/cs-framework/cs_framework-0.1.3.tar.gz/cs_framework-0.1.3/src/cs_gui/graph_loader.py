from rdflib import Graph, RDF, URIRef
from cs_framework.logging.ontology import CONCEPT, ACTION, EVENT, SYNCHRONIZATION, HAS_NAME, BELONGS_TO, TRIGGERED_BY, CAUSED_BY, STATUS

def load_graph_data(ttl_file: str):
    g = Graph()
    try:
        g.parse(ttl_file, format="turtle")
    except FileNotFoundError:
        return {"nodes": [], "links": []}
    except Exception as e:
        # It's common to hit a race condition where the file is being written.
        # Just ignore this update cycle.
        # print(f"Error parsing log: {e}") 
        return {"nodes": [], "links": []}

    nodes = []
    links = []
    
    # Helper to get name
    def get_name(uri):
        name = g.value(uri, HAS_NAME)
        return str(name) if name else str(uri).split("/")[-1]

    # 1. Concepts
    for s in g.subjects(RDF.type, CONCEPT):
        nodes.append({
            "id": str(s),
            "name": get_name(s),
            "category": "Concept",
            "symbolSize": 30,
            "itemStyle": {"color": "#5470c6"}
        })

    # 2. Actions
    for s in g.subjects(RDF.type, ACTION):
        concept_uri = g.value(s, BELONGS_TO)
        nodes.append({
            "id": str(s),
            "name": get_name(s),
            "category": "Action",
            "symbolSize": 15,
            "itemStyle": {"color": "#91cc75"}
        })
        # Link Action to Concept
        if concept_uri:
            links.append({
                "source": str(concept_uri),
                "target": str(s),
                "lineStyle": {"type": "dashed"}
            })
        
        # Triggered By (Event -> Action)
        trigger_uri = g.value(s, TRIGGERED_BY)
        if trigger_uri:
            links.append({
                "source": str(trigger_uri),
                "target": str(s),
                "label": {"show": True, "formatter": "TriggeredBy"}
            })

    # 3. Events
    # Limit to last 50 events to prevent graph explosion
    all_events = list(g.subjects(RDF.type, EVENT))
    # Assuming the parser reads in order, or we just take a subset.
    # For a better UX, we should sort by timestamp if available, but for now we slice.
    # Since we append to file, the last ones parsed might be the last ones in file (depending on parser implementation).
    # However, rdflib's default store is not ordered. 
    # But let's try to just show a limited number.
    display_events = all_events[-50:] if len(all_events) > 50 else all_events

    for s in display_events:
        concept_uri = g.value(s, BELONGS_TO)
        status = g.value(s, STATUS)
        color = "#fac858" if str(status) == "Success" else "#ee6666"
        
        nodes.append({
            "id": str(s),
            "name": get_name(s),
            "category": "Event",
            "symbolSize": 15,
            "itemStyle": {"color": color}
        })
        
        # Link Event to Concept
        if concept_uri:
            links.append({
                "source": str(concept_uri),
                "target": str(s),
                "lineStyle": {"type": "dashed"}
            })
            
        # Caused By (Action -> Event)
        cause_uri = g.value(s, CAUSED_BY)
        if cause_uri:
            # Only add link if the Action is also in the graph (Actions are not limited currently, but good to check)
            links.append({
                "source": str(cause_uri),
                "target": str(s),
                "label": {"show": True, "formatter": "CausedBy"}
            })

    return {"nodes": nodes, "links": links}
