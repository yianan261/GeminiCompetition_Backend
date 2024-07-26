user_schema = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string"},
        "google_id": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "display_name": {"type": "string"},
        "interests": {"type": "array", "items": {"type": "string"}},
        "user_description": {"type": "string"},
    },
    "required": [
        "user_id",
        "google_id",
        "email",
        "display_name",
        "interests",
    ],
    "additionalProperties": False,
}
