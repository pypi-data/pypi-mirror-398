import json
import pytest

from src.lunar_policy import Check, Node


class TestCheckBasic:
    def test_invalid_check_initialization(self):
        with pytest.raises(ValueError):
            Check('test', node='not a SnippetData object')

    def test_data_error_if_no_env(
        self,
    ):
        with pytest.raises(ValueError):
            Check('test', node=None)

    def test_data_error_if_invalid_path(self, monkeypatch):
        monkeypatch.setenv('LUNAR_BUNDLE_PATH', '/invalid/path')

        with pytest.raises(ValueError):
            Check('test')

    def test_data_is_set(self, capsys):
        dataJson = {'hi': 'there'}
        node = Node.from_component_json(dataJson)

        with Check('test', node=node) as c:
            c.get_value('.hi')

    def test_description_check(self, capsys):
        node = Node.from_component_json({})

        with Check('test', 'description', node=node) as c:
            c.assert_true(True)

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result['description'] == 'description'

    def test_description_not_in_check(self, capsys):
        node = Node.from_component_json({})

        with Check('test', node=node) as c:
            c.assert_true(True)

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert 'description' not in result
