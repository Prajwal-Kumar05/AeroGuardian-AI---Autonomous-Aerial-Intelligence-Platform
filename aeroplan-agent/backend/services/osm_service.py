"""
AeroPlan-Agent :: Geospatial (OpenStreetMap) Service

Uses OSMnx to pull the drivable road network and nearby critical
infrastructure (hospitals, fire stations, police stations) around an
emergency location. Network graphs are cached per-session to avoid
repeated heavy downloads during a demo run.
"""
import logging
import osmnx as ox
import networkx as nx

from backend.core.config import get_settings

logger = logging.getLogger("aeroplan.osm")
settings = get_settings()

_graph_cache: dict = {}

ox.settings.log_console = False
ox.settings.use_cache = True


def get_road_network(lat: float, lon: float, radius_m: int = None) -> nx.MultiDiGraph:
    radius_m = radius_m or settings.OSM_NETWORK_RADIUS_M
    key = (round(lat, 3), round(lon, 3), radius_m)
    if key in _graph_cache:
        return _graph_cache[key]
    try:
        G = ox.graph_from_point((lat, lon), dist=radius_m, network_type="drive")
        _graph_cache[key] = G
        return G
    except Exception as e:
        logger.error(f"OSM road network fetch failed: {e}")
        raise


def find_nearby_amenities(lat: float, lon: float, amenity: str, radius_m: int = 5000, limit: int = 5):
    """
    amenity: 'hospital' | 'fire_station' | 'police' (OSM amenity tag values)
    """
    tags = {"amenity": amenity}
    try:
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=radius_m)
        gdf = gdf[gdf.geometry.notnull()]
        results = []
        for _, row in gdf.head(limit).iterrows():
            centroid = row.geometry.centroid
            results.append({
                "name": row.get("name", f"Unnamed {amenity}"),
                "latitude": centroid.y,
                "longitude": centroid.x,
            })
        return results
    except Exception as e:
        logger.warning(f"No {amenity} found near ({lat},{lon}): {e}")
        return []


def identify_safe_zones(lat: float, lon: float, radius_m: int = 5000, limit: int = 5):
    """Open spaces (parks, sports grounds) used as candidate evacuation shelters."""
    tags = {"leisure": ["park", "pitch", "sports_centre"]}
    try:
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=radius_m)
        gdf = gdf[gdf.geometry.notnull()]
        results = []
        for _, row in gdf.head(limit).iterrows():
            centroid = row.geometry.centroid
            results.append({
                "name": row.get("name", "Open Ground / Safe Zone"),
                "latitude": centroid.y,
                "longitude": centroid.x,
            })
        return results
    except Exception as e:
        logger.warning(f"No safe zones found near ({lat},{lon}): {e}")
        return []
