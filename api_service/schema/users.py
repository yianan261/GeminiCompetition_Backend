user_schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string", "format": "email"},
        "uid": {"type": "string"},
        "displayName": {"type": "string"},
        "accessLocationAllowed": {"type": "boolean"},
        "notificationAllowed": {"type": "boolean"},
        "onboardingCompleted": {"type": "boolean"},
        "onboarding_step3": {"type": "boolean"},
        "onboarding_step4": {"type": "boolean"},
        "photoURL": {"type": "string"},
        "createdAt": {"type": "string", "format": "date-time"},
        "interests": {"type": "array", "items": {"type": "string"}},
        "userDescription": {"type": "string"},
        "geminiDescription": {"type": "string"},
    },
    "required": [
        "email",
        "displayName",
        "interests",
    ],
    "additionalProperties": True,
}
