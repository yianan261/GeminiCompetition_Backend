places_schema = {
    "type": "object",
    "properties": {
        "place_id": {"type": "string"},
        "title": {"type": "string"},
        "email": {"type": "string"},
        "note": {"type": "string"},
        "comment": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "place_description": {"type": "string"},
        "types": {"type": "array", "items": {"type": "string"}},
        "location": {
            "type": "object",
            "properties": {
                "longitude": {"type": "string"},
                "latitude": {"type": "string"},
            },
            "required": ["longitude", "latitude"],
        },
        "address": {"type": "string"},
        "photo_url": {"type": "string"},
        "reviews": {"type": "array", "items": {"type": "string"}},
        "bookmarked": {"type": "boolean"},
        "interesting_facts": {"type": "string"},
    },
    "required": ["place_id", "title", "email", "location"],
    "additionalProperties": False,
}
