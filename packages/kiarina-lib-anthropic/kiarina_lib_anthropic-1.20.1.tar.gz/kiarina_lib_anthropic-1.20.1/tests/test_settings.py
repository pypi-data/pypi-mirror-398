from kiarina.lib.anthropic import AnthropicSettings


def test_api_key():
    settings = AnthropicSettings.model_validate({"api_key": "sk-ant-test-key-123"})
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "sk-ant-test-key-123"
