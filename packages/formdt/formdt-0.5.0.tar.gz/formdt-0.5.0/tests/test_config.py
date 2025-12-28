import json
from formdt import load_config, Config


class TestConfig:
    def test_default_config_values(self):
        config = Config()
        assert config.line_length == 80

    def test_load_config_returns_defaults_when_file_missing(self, tmp_path):
        config = load_config(tmp_path / ".formdt")
        assert config.line_length == 80

    def test_load_config_reads_line_length(self, tmp_path):
        config_file = tmp_path / ".formdt"
        config_file.write_text(json.dumps({"line_length": 120}))

        config = load_config(config_file)
        assert config.line_length == 120

    def test_load_config_uses_default_for_missing_keys(self, tmp_path):
        config_file = tmp_path / ".formdt"
        config_file.write_text(json.dumps({}))

        config = load_config(config_file)
        assert config.line_length == 80
