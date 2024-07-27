user_schema = {
    "type": "object",
    "properties": {
        "google_id": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "display_name": {"type": "string"},
        "interests": {"type": "array", "items": {"type": "string"}},
        "user_description": {"type": "string"},
    },
    "required": [
        "google_id",
        "email",
        "display_name",
        "interests",
    ],
    "additionalProperties": False,
}
