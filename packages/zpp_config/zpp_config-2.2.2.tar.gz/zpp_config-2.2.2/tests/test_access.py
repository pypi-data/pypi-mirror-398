from zpp_config import Config
import json

def test_attribute_and_path_access(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text(json.dumps({"db": {"host": "localhost"}}))

    cfg = Config(str(file))

    assert cfg.db.host == "localhost"
    assert cfg["db.host"] == "localhost"
    assert "db.host" in cfg

def test_set_and_get(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text("{}")

    cfg = Config(str(file))

    cfg.set("api.token", "abc")
    assert cfg.api.token == "abc"
    assert cfg.get("api.token") == "abc"

def test_delete(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text('{"x": {"y": 1}}')

    cfg = Config(str(file))
    del cfg.x.y

    assert cfg.x.y is None

def test_to_dict_and_eq(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text('{"a": {"b": 2}}')

    cfg = Config(str(file))
    assert cfg.to_dict() == {"a": {"b": 2}}
    assert cfg == {"a": {"b": 2}}
