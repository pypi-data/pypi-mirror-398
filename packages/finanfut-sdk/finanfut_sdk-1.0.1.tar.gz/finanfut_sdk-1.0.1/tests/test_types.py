"""Regression tests for common typed models."""

from finanfut_sdk.utils.types import InteractionResponse


def _validate(model, payload):
    validator = getattr(model, "model_validate", None)
    if callable(validator):
        return validator(payload)
    return model.parse_obj(payload)


def test_interaction_response_accepts_available_intents_objects():
    payload = {
        "answer": "ok",
        "available_intents": [
            {
                "intent_id": "intent-1",
                "name": "Test Intent",
                "enabled": True,
            }
        ],
    }

    response = _validate(InteractionResponse, payload)

    assert response.available_intents
    intent = response.available_intents[0]
    assert intent.intent_id == "intent-1"
    assert intent.name == "Test Intent"
    assert intent.enabled is True
