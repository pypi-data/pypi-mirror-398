import json
import pytest

from src.lunar_policy import Check, Node


class TestCheckPaths:
    def test_path_in_check(self, capsys):
        node = Node.from_component_json(
            {
                'value': True,
            }
        )

        with Check('test', node=node) as c:
            c.assert_true(c.get_value('.value'))

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result['paths'] == ['.value']

    def test_multiple_paths_in_check(self, capsys):
        node = Node.from_component_json({'true_value': True, 'false_value': False})

        with Check('test', node=node) as c:
            v = c.get_value('.false_value')
            c.assert_false(v)
            c.assert_true(c.get_value('.true_value'))

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result['paths'] == ['.false_value', '.true_value']

    def test_paths_not_in_check(self, capsys):
        node = Node.from_component_json({})

        with Check('test', node=node) as c:
            c.assert_true(True)

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result['paths'] == []

    def test_get_invalid_path(self):
        node = Node.from_component_json({})

        with pytest.raises(ValueError):
            with Check('test', node=node) as c:
                c.get_value('@#&*(!%)')
