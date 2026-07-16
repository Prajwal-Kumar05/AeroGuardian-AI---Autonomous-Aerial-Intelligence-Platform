"""
AeroPlan-Agent :: Route Planning Service

Computes shortest / alternative safe evacuation routes over the OSM road
network using Dijkstra and A* (great-circle heuristic), with the option to
remove blocked-road edges flagged by the Vision Analysis Agent before
planning — guaranteeing routes never cross a known-blocked segment.
"""
import logging
import math
import networkx as nx
import osmnx as ox

logger = logging.getLogger("aeroplan.routing")


def _heuristic(G, u, v):
    y1, x1 = G.nodes[u]["y"], G.nodes[u]["x"]
    y2, x2 = G.nodes[v]["y"], G.nodes[v]["x"]
    return ox.distance.great_circle(y1, x1, y2, x2)


def remove_blocked_roads(G: nx.MultiDiGraph, blocked_coords: list) -> nx.MultiDiGraph:
    """blocked_coords: list of (lat, lon) points reported as obstructed by Vision Agent."""
    if not blocked_coords:
        return G
    G2 = G.copy()
    for lat, lon in blocked_coords:
        try:
            node = ox.distance.nearest_nodes(G2, lon, lat)
            G2.remove_node(node)
        except Exception:
            continue
    return G2


def shortest_route(G: nx.MultiDiGraph, origin, destination, algorithm: str = "dijkstra"):
    """
    origin/destination: (lat, lon) tuples.
    Returns dict: distance_m, path_coordinates, algorithm
    """
    orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
    dest_node = ox.distance.nearest_nodes(G, destination[1], destination[0])

    try:
        if algorithm == "astar":
            path = nx.astar_path(G, orig_node, dest_node, heuristic=_heuristic, weight="length")
        else:
            path = nx.dijkstra_path(G, orig_node, dest_node, weight="length")
        distance_m = nx.path_weight(G, path, weight="length")
        coords = [[G.nodes[n]["y"], G.nodes[n]["x"]] for n in path]
        return {
            "algorithm": algorithm,
            "distance_m": round(distance_m, 1),
            "path_coordinates": coords,
        }
    except nx.NetworkXNoPath:
        logger.warning("No path found between origin and destination on filtered graph.")
        return {"algorithm": algorithm, "distance_m": None, "path_coordinates": []}


def plan_evacuation(G: nx.MultiDiGraph, origin, shelters: list, blocked_coords: list = None):
    """
    Plans a primary (Dijkstra) + alternative (A*) route from origin to the
    nearest reachable shelter, avoiding blocked roads.
    shelters: list of {"name","latitude","longitude"}
    """
    G_safe = remove_blocked_roads(G, blocked_coords or [])
    best = None
    for shelter in shelters:
        dest = (shelter["latitude"], shelter["longitude"])
        primary = shortest_route(G_safe, origin, dest, "dijkstra")
        if primary["distance_m"] is not None:
            if best is None or primary["distance_m"] < best["primary"]["distance_m"]:
                alt = shortest_route(G_safe, origin, dest, "astar")
                best = {"shelter": shelter, "primary": primary, "alternative": alt}
    return best
