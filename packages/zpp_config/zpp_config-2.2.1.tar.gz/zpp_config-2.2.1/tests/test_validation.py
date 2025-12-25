from zpp_config import Config
import json
import pytest

CONFIG_DATA = {
    "database": {"host": "localhost", "port": 3306},
    "nxs": {"password": "abc", "password2": "superpass"},
}

@pytest.fixture
def cfg(tmp_path):
    file = tmp_path / "conf.json"
    file.write_text(json.dumps(CONFIG_DATA))
    return Config(str(file))

def test_schema_validation_ok(cfg):
    schema = {
        "database": {
            "port": {"_type": int, "_min": 3000}
        }
    }
    cfg.validate(schema=schema)

def test_schema_validation_fail(cfg):
    schema = {
        "database": {
            "port": {"_min": 4000}
        }
    }
    with pytest.raises(Exception):
        cfg.validate(schema=schema)

def test_rules_match_name(cfg):
    rules = {
        r"password": {"_type": str, "_min_len": 5}
    }
    errors = cfg.validate(rules=rules, strict=False)
    assert any("password" in e for e in errors)

def test_rules_match_path(cfg):
    rules = {
        r"password": {"_min_len": 10}
    }
    errors = cfg.validate(rules=rules, strict=False)
    assert any("password" in e for e in errors)

def test_regex_rule(cfg):
    rules = {
        r"password2": {"_regex": r"super.*"}
    }
    cfg.validate(rules=rules)
