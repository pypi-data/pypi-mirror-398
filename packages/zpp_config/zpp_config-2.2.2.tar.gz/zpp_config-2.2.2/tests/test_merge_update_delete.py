from zpp_config import Config
import json

def test_merge(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text(json.dumps({"a": {"b": 1}}))

    cfg = Config(str(file))
    cfg.merge({"a": {"c": 2}})

    assert cfg.a.c == 2
    assert cfg.a.b == 1

def test_update_overload(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text(json.dumps({"a": {"b": 1}}))

    cfg = Config(str(file))
    cfg.update("a", {"b": 3}, overload=True)

    assert cfg.a.b == 3
