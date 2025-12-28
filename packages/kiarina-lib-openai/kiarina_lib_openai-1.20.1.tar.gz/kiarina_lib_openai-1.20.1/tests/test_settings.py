from kiarina.lib.openai import OpenAISettings


def test_api_key():
    settings = OpenAISettings.model_validate({"api_key": "sk-test-key-123"})
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "sk-test-key-123"
