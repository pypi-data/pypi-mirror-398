import json
import semver

from src.lunar_policy import Check, Node


class TestCheckAssertions:
    def test_simple_value(self, capsys):
        node = Node.from_component_json({})

        with Check('test', node=node) as c:
            c.assert_true(True)

        captured = capsys.readouterr()
        result = json.loads(captured.out)['assertions'][0]

        assert result['op'] == 'true'
        assert result['args'] == ['True']
        assert result['result'] == 'pass'
        assert 'failure_message' not in result

    def test_simple_path(self, capsys):
        node = Node.from_component_json(
            {
                'value': True,
            }
        )

        with Check('test', node=node) as c:
            c.assert_true(c.get_value('.value'))

        captured = capsys.readouterr()
        result = json.loads(captured.out)['assertions'][0]

        assert result['op'] == 'true'
        assert result['args'] == ['True']
        assert result['result'] == 'pass'
        assert 'failure_message' not in result

    def test_multiple_mixed_assertions_in_check(self, capsys):
        node = Node.from_component_json(
            {
                'value': True,
            }
        )

        with Check('test', node=node) as c:
            c.assert_true(True)
            c.assert_true(c.get_value('.value'))

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_true_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': True,
            }
        )

        with Check('test', node=node) as c:
            c.assert_true(True)
            c.assert_true(c.get_value('.value'))

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_false_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': False,
            }
        )

        with Check('test', node=node) as c:
            c.assert_false(False)
            c.assert_false(c.get_value('.value'))

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_equals_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 1,
            }
        )

        with Check('test', node=node) as c:
            c.assert_equals(1, 1)
            c.assert_equals(c.get_value('.value'), 1)

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_greater_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 1,
            }
        )

        with Check('test', node=node) as c:
            c.assert_greater(2, 1)
            c.assert_greater(c.get_value('.value'), 0)

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_greater_or_equal_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 1,
            }
        )

        with Check('test', node=node) as c:
            c.assert_greater_or_equal(2, 1)
            c.assert_greater_or_equal(1, 1)
            c.assert_greater_or_equal(c.get_value('.value'), 0)
            c.assert_greater_or_equal(c.get_value('.value'), 1)

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_less_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 1,
            }
        )

        with Check('test', node=node) as c:
            c.assert_less(1, 2)
            c.assert_less(c.get_value('.value'), 2)

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_less_or_equal_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 1,
            }
        )

        with Check('test', node=node) as c:
            c.assert_less_or_equal(1, 2)
            c.assert_less_or_equal(1, 1)
            c.assert_less_or_equal(c.get_value('.value'), 2)
            c.assert_less_or_equal(c.get_value('.value'), 1)

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_contains_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 'hello',
            }
        )

        with Check('test', node=node) as c:
            c.assert_contains('hello', 'e')
            c.assert_contains('hello', 'hello')
            c.assert_contains('hello', '')
            c.assert_contains(c.get_value('.value'), 'e')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_match_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 'hello',
            }
        )

        with Check('test', node=node) as c:
            c.assert_match('hello', '.*ell.*')
            c.assert_match('hello', '.*hello.*')
            c.assert_match('hello', '.*')
            c.assert_match(c.get_value('.value'), '.*ell.*')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_foreign_type_comparison(self, capsys):
        node = Node.from_component_json({})

        with Check('test', node=node) as c:
            v1 = semver.Version.parse('1.0.0')
            v2 = semver.Version.parse('2.0.0')

            c.assert_greater_or_equal(v2, v1)
            c.assert_less_or_equal(v1, v2)

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)

    def test_exists_assertion(self, capsys):
        node = Node.from_component_json(
            {
                'value': 1,
            }
        )

        with Check('test', node=node) as c:
            c.assert_exists('.value')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert all(result['result'] == 'pass' for result in results)
