from src.config import Settings


def test_settings_load_reads_cajas_yaml_and_environment(tmp_path, monkeypatch):
    config_file = tmp_path / "cajas.yaml"
    config_file.write_text(
        "cajas:\n"
        "  - nombre: norte\n"
        "    adaptador: rest_api_key\n"
        "  - nombre: sur\n"
        "    adaptador: rest_bearer_v2\n"
    )
    monkeypatch.setenv("CAJA_NORTE_URL", "http://caja-norte:9001")
    monkeypatch.setenv("CAJA_NORTE_API_KEY", "fake-key-para-test")
    monkeypatch.setenv("CAJA_SUR_ENABLED", "true")
    monkeypatch.setenv("NORTE_TOKEN", "fake-token-para-test")

    settings = Settings.load(config_path=config_file)

    assert settings.norte_url == "http://caja-norte:9001"
    assert settings.norte_api_key == "fake-key-para-test"
    assert settings.sur_enabled is True
    assert settings.tokens["NORTE"] == "fake-token-para-test"
    assert [c.nombre for c in settings.cajas_declaradas] == ["norte", "sur"]
