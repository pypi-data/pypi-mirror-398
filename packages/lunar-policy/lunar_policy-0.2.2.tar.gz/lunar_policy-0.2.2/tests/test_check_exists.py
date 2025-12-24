import json

from src.lunar_policy import Check, Node


class TestCheckExists:
    def test_exists_valid_path_workflows_finished(self):
        node = Node.from_component_json({'hi': 'there'}, bundle_info={'workflows_finished': True})

        with Check('test', node=node) as c:
            assert c.exists('.hi')

    def test_exists_valid_path_workflows_not_finished(self):
        node = Node.from_component_json({'hi': 'there'}, bundle_info={'workflows_finished': False})

        with Check('test', node=node) as c:
            assert c.exists('.hi')

    def test_exists_missing_path_workflows_finished(self):
        node = Node.from_component_json({}, bundle_info={'workflows_finished': True})

        with Check('test', node=node) as c:
            assert not c.exists('.missing')

    def test_exists_missing_path_workflows_not_finished(self, capsys):
        node = Node.from_component_json({}, bundle_info={'workflows_finished': False})

        with Check('test', node=node) as c:
            c.exists('.missing')
            c.assert_equals('should not run', 'should not run')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert len(results) == 1
        assert results[0]['result'] == 'no-data'
        assert '.missing' in results[0]['failure_message']
        assert results[0]['op'] == 'fail'
