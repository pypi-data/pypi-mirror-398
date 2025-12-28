import json

from ai_dev_kit import cli


def test_read_plugin_version(tmp_path):
    manifest_dir = tmp_path / ".claude-plugin"
    manifest_dir.mkdir()
    manifest_path = manifest_dir / "plugin.json"
    manifest_path.write_text(json.dumps({"version": "1.2.3"}))

    assert cli.read_plugin_version(tmp_path) == "1.2.3"


def test_resolve_source_explicit(tmp_path):
    manifest_dir = tmp_path / ".claude-plugin"
    manifest_dir.mkdir()
    manifest_path = manifest_dir / "plugin.json"
    manifest_path.write_text(json.dumps({"version": "0.1.0"}))

    resolved = cli.resolve_source(str(tmp_path))
    assert resolved == tmp_path
