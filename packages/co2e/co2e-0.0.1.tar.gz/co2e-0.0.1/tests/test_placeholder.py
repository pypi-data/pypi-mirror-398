import importlib


def test_settings_import() -> None:
    module = importlib.import_module("carbon_ops")
    settings = getattr(module, "settings")
    cfg = settings()
    assert cfg.project_id == "dcl-ops"