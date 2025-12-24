import json

from src.lunar_policy import Check, Node


class TestCheckGet:
    def test_one_check_output_with_prefix(self, capsys, monkeypatch):
        node = Node.from_component_json({'hi': 'there'})
        prefix = 'LUNAR_SNIPPETS: '

        monkeypatch.setenv('LUNAR_LOG_PREFIX', prefix)

        with Check('test', node=node) as c:
            c.get_value('.hi')

        captured = capsys.readouterr()
        assert captured.out.startswith(prefix), f'Missing prefix: {captured}'

        json_part = captured.out[len(prefix) :]
        try:
            json.loads(json_part)
        except Exception as e:
            raise AssertionError(f'Invalid JSON: {json_part!r}') from e

    def test_multiple_checks_output_with_prefix(self, capsys, monkeypatch):
        node = Node.from_component_json({'hi': 'there'})
        prefix = 'LUNAR_SNIPPETS: '

        monkeypatch.setenv('LUNAR_LOG_PREFIX', prefix)

        with Check('test', node=node) as c:
            c.get_value('.hi')

        with Check('test', node=node) as c:
            c.get_value('.hi')

        captured = capsys.readouterr()
        lines = captured.out.splitlines()
        assert len(lines) == 2, f'Expected 2 lines, got {len(lines)}'

        for line in captured.out.splitlines():
            assert line.startswith(prefix), f'Missing prefix: {line!r}'
            json_part = line[len(prefix) :]
            try:
                json.loads(json_part)
            except Exception as e:
                raise AssertionError(f'Invalid JSON: {json_part!r}') from e
