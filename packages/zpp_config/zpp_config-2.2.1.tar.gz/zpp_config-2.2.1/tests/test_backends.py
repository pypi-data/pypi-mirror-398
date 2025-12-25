import json
import toml
import pytest
import yaml
from zpp_config import Config

def write_file(path, content):
    path.write_text(content)

@pytest.mark.parametrize("ext,writer,data", [
    (".yaml", yaml.safe_dump, {"a": 1}),
    (".yml", yaml.safe_dump, {"a": 1}),
    (".json", json.dumps, {"a": 1}),
    (".toml", toml.dumps, {"a": 1}),
])
def test_load_backends(tmp_path, ext, writer, data):
    file = tmp_path / ("conf" + ext)
    write_file(file, writer(data))
    cfg = Config(str(file))
    assert cfg.a == 1
