import json

from src.lunar_policy import Check, Node


class TestCheckSkipped:
    def test_skip_no_reason(self, capsys):
        node = Node.from_component_json({})
        with Check('test', node=node) as c:
            c.skip()

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert len(results) == 1
        assert results[0]['result'] == 'skipped'
        assert results[0]['op'] == 'skip'

    def test_skip_with_reason(self, capsys):
        node = Node.from_component_json({})
        with Check('test', node=node) as c:
            c.skip('idk, just skip it bro')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert len(results) == 1
        assert results[0]['result'] == 'skipped'
        assert results[0]['op'] == 'skip'
        assert results[0]['failure_message'] == 'idk, just skip it bro'

    def test_skip_after_assertions(self, capsys):
        node = Node.from_component_json({})
        with Check('test', node=node) as c:
            c.assert_true(True)
            c.skip('idk, just skip it bro')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert len(results) == 1
        assert results[0]['result'] == 'skipped'
        assert results[0]['op'] == 'skip'
        assert results[0]['failure_message'] == 'idk, just skip it bro'

    def test_skip_exits_early(self, capsys):
        node = Node.from_component_json({})
        with Check('test', node=node) as c:
            c.skip('idk, just skip it bro')
            raise Exception('should not run')
