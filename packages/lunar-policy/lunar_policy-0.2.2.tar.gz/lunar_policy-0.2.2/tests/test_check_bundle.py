import json
import pytest
import tempfile

from src.lunar_policy import Check


class TestCheckBundle:
    @pytest.fixture(autouse=True)
    def setup_lunar_bundle(self, monkeypatch):
        test_data = {
            'bundle_info': {},
            'merged_blob': {
                'merged_true': True,
                'merged_false': False,
                'value_in_both_roots': 'hello world',
                'tricky_value': '.merged_true',
            },
            'metadata_instances': [
                {
                    'payload': {
                        'value_in_both_roots': 'hello moon',
                        'value_in_one_delta': 'one',
                        'value_in_two_deltas': 'two_a',
                    }
                },
                {
                    'payload': {
                        'value_in_both_roots': 'hello moon',
                        'value_in_two_deltas': 'two_b',
                    }
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        monkeypatch.setenv('LUNAR_BUNDLE_PATH', temp_path)

        yield

    def test_value_in_both_roots(self, capsys):
        with Check('test') as c:
            c.assert_equals(c.get_value('.value_in_both_roots'), 'hello world')
            for value in c.get_all_values('.value_in_both_roots'):
                c.assert_equals(value, 'hello moon')

        captured = capsys.readouterr()
        results = json.loads(captured.out)
        assert all(result['result'] == 'pass' for result in results['assertions'])
        assert results['paths'] == ['.value_in_both_roots']

    def test_value_in_single_delta(self, capsys):
        with Check('test') as c:
            for value in c.get_all_values('.value_in_one_delta'):
                c.assert_equals(value, 'one')

        captured = capsys.readouterr()
        results = json.loads(captured.out)
        assert all(result['result'] == 'pass' for result in results['assertions'])
        assert results['paths'] == ['.value_in_one_delta']

    def test_value_in_two_deltas(self, capsys):
        with Check('test') as c:
            for value in c.get_all_values('.value_in_two_deltas'):
                c.assert_contains(value, 'two')

        captured = capsys.readouterr()
        results = json.loads(captured.out)
        assert all(result['result'] == 'pass' for result in results['assertions'])
        assert results['paths'] == ['.value_in_two_deltas']
