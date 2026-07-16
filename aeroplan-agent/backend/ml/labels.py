"""Target classes for AeroPlan-Agent disaster fine-tuning (Roboflow / Kaggle merged schema)."""

DISASTER_CLASSES = [
    "fire",
    "smoke",
    "flood",
    "road_accident",
    "collapsed_building",
    "fallen_tree",
    "blocked_road",
    "crowd",
    "vehicle",
    "person",
]

# Maps raw label -> emergency_type used across agents/DB
LABEL_TO_EMERGENCY_TYPE = {
    "fire": "fire",
    "smoke": "fire",
    "flood": "flood",
    "road_accident": "road_accident",
    "collapsed_building": "structural_collapse",
    "fallen_tree": "obstruction",
    "blocked_road": "obstruction",
    "crowd": "crowd_hazard",
}
