import pytest
import json
import tempfile
from pathlib import Path as FSPath
from src.lunar_policy import Node, NodePath, NoDataError
from src.lunar_policy.node import NodePathTracker


class TestDataLoading:
    def test_from_component_json(self):
        merged_json = {'string': 'hello world'}
        data = Node.from_component_json(merged_json)
        assert data.get_value('.string') == 'hello world'
        assert data.get_all_values('.string') == ['hello world']

    def test_from_bundle_json(self):
        test_data = {
            'bundle_info': {},
            'metadata_instances': [{'payload': {'string': 'hello world'}}],
            'merged_blob': {'string': 'hello world'},
        }
        data = Node.from_bundle_json(test_data)
        assert data.get_value('.string') == 'hello world'
        assert data.get_all_values('.string') == ['hello world']

    def test_from_bundle_json_missing_bundle_info(self):
        test_data = {'metadata_instances': [], 'merged_blob': {}}
        with pytest.raises(ValueError):
            Node.from_bundle_json(test_data)

    def test_from_bundle_json_missing_metadata_instances(self):
        test_data = {'bundle_info': {}, 'merged_blob': {}}
        with pytest.raises(ValueError):
            Node.from_bundle_json(test_data)

    def test_from_bundle_json_missing_merged_blob(self):
        test_data = {'bundle_info': {}, 'metadata_instances': []}
        with pytest.raises(ValueError):
            Node.from_bundle_json(test_data)

    def test_from_bundle_file(self):
        test_data = {
            'bundle_info': {},
            'metadata_instances': [{'payload': {'string': 'hello world'}}],
            'merged_blob': {'string': 'hello world'},
        }

        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.json') as tmpfile:
            tmpfile.write(json.dumps(test_data))
            tmpfile.flush()
            tmp_path = FSPath(tmpfile.name)

        data = Node.from_bundle_file(FSPath(tmp_path))
        assert data.get_value('.string') == 'hello world'
        assert data.get_all_values('.string') == ['hello world']

    def test_from_file_invalid_path(self):
        with pytest.raises(FileNotFoundError):
            Node.from_bundle_file(FSPath('/my/path/does_not_exist.json'))

    def test_from_file_relative_path(self):
        with pytest.raises(ValueError):
            Node.from_bundle_file(FSPath('relative/path.json'))

    def test_from_file_invalid_json(self):
        test_data = '}'

        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.json') as tmpfile:
            tmpfile.write(test_data)
            tmpfile.flush()
            tmp_path = FSPath(tmpfile.name)

        with pytest.raises(json.JSONDecodeError):
            Node.from_bundle_file(FSPath(tmp_path))


class TestGetMerged:
    @pytest.fixture
    def snippet_data(self):
        test_data = {
            'bundle_info': {},
            'metadata_instances': [],
            'merged_blob': {
                'string': 'hello world',
                'array': ['hello', 'world'],
                'object1': {'hello': 'world'},
                'object2': {'hello': 'moon'},
                'empty_object': {},
                'empty_array': [],
            },
        }
        return Node.from_bundle_json(test_data)

    def test_get_single_value(self, snippet_data):
        assert snippet_data.get_value('.string') == 'hello world'

    def test_get_missing(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.get_value('.missing')

    def test_get_missing_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        with pytest.raises(ValueError):
            snippet_data.get_value('.missing')

    def test_get_array(self, snippet_data):
        assert snippet_data.get_value('.array') == ['hello', 'world']

    def test_get_array_index(self, snippet_data):
        assert snippet_data.get_value('.array[0]') == 'hello'

    def test_get_nested_object(self, snippet_data):
        assert snippet_data.get_value('.object1.hello') == 'world'

    def test_get_nested_object_missing(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.get_value('.object1.missing')

    def test_get_nested_object_missing_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        with pytest.raises(ValueError):
            snippet_data.get_value('.object1.missing')

    def test_get_empty_object(self, snippet_data):
        assert snippet_data.get_value('.empty_object') == {}

    def test_get_empty_array(self, snippet_data):
        assert snippet_data.get_value('.empty_array') == []


class TestGetAll:
    @pytest.fixture
    def snippet_data(self):
        test_data = {
            'bundle_info': {},
            'merged_blob': {},
            'metadata_instances': [
                {
                    'payload': {
                        'single': 'hello world',
                        'double': 'hello1',
                        'single_array': ['hello', 'world'],
                        'double_array': ['goodbye', 'moon'],
                        'single_object': {'hello': 'world'},
                        'double_object': {'hello': 'moon'},
                    }
                },
                {
                    'payload': {
                        'double': 'hello2',
                        'double_array': ['mars', 'i', 'guess'],
                        'double_object': {'hello': 'venus'},
                    }
                },
                {'not_in_any_delta': 'hello pluto'},
            ],
        }
        return Node.from_bundle_json(test_data)

    def test_get_single_key_in_one_delta(self, snippet_data):
        assert snippet_data.get_all_values('.single') == ['hello world']

    def test_get_single_key_in_two_deltas(self, snippet_data):
        assert snippet_data.get_all_values('.double') == ['hello2', 'hello1']

    def test_get_missing(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.get_all_values('.missing')

    def test_get_missing_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        with pytest.raises(ValueError):
            snippet_data.get_all_values('.missing')

    def test_get_single_array(self, snippet_data):
        assert snippet_data.get_all_values('.single_array') == [['hello', 'world']]

    def test_get_single_array_index(self, snippet_data):
        assert snippet_data.get_all_values('.single_array[0]') == ['hello']

    def test_get_double_array(self, snippet_data):
        assert snippet_data.get_all_values('.double_array') == [
            ['mars', 'i', 'guess'],
            ['goodbye', 'moon'],
        ]

    def test_get_double_array_index(self, snippet_data):
        assert snippet_data.get_all_values('.double_array[0]') == ['mars', 'goodbye']

    def test_get_double_array_index_some_out_of_bounds(self, snippet_data):
        assert snippet_data.get_all_values('.double_array[2]') == ['guess']

    def test_get_single_object(self, snippet_data):
        assert snippet_data.get_all_values('.single_object') == [{'hello': 'world'}]

    def test_get_double_object(self, snippet_data):
        assert snippet_data.get_all_values('.double_object') == [
            {'hello': 'venus'},
            {'hello': 'moon'},
        ]

    def test_get_single_object_key(self, snippet_data):
        assert snippet_data.get_all_values('.single_object.hello') == ['world']

    def test_get_double_object_key(self, snippet_data):
        assert snippet_data.get_all_values('.double_object.hello') == ['venus', 'moon']

    def test_get_single_object_key_missing(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.get_all_values('.single_object.missing')

    def test_get_single_object_key_missing_wflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        with pytest.raises(ValueError):
            snippet_data.get_all_values('.single_object.missing')

    def test_get_double_object_key_missing(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.get_all_values('.double_object.missing')

    def test_get_double_object_key_missing_wflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        with pytest.raises(ValueError):
            snippet_data.get_all_values('.double_object.missing')

    def test_get_not_in_any_delta(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.get_all_values('.not_in_any_delta')

    def test_get_not_in_any_delta_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        with pytest.raises(ValueError):
            snippet_data.get_all_values('.not_in_any_delta')


class TestNodeInvalidData:
    def test_none_data(self):
        with pytest.raises(ValueError):
            Node(NodePath.parse('.'), None, NodePathTracker())

    def test_empty_data(self):
        with pytest.raises(ValueError):
            Node(NodePath.parse('.'), {}, NodePathTracker())

    def test_invalid_snippet_data_missing_merged_blob(self):
        with pytest.raises(ValueError):
            Node(NodePath.parse('.'), {'metadata_instances': []}, NodePathTracker())

    def test_invalid_snippet_data_missing_metadata_instances(self):
        with pytest.raises(ValueError):
            Node(NodePath.parse('.'), {'merged_blob': {}}, NodePathTracker())

    def test_no_path_tracker(self):
        with pytest.raises(ValueError):
            Node(NodePath.parse('.'), {'merged_blob': {}, 'metadata_instances': []}, None)


class TestExists:
    @pytest.fixture
    def snippet_data(self):
        test_data = {
            'bundle_info': {},
            'merged_blob': {
                'a': 'hello',
                'b': ['hello', 'world'],
                'c': {'hello': 'world'},
            },
            'metadata_instances': [],
        }
        return Node.from_bundle_json(test_data)

    def test_exists_on_scalar(self, snippet_data):
        assert snippet_data.exists()

    def test_exists_on_object(self, snippet_data):
        assert snippet_data.exists('.a')

    def test_exists_on_array_index(self, snippet_data):
        assert snippet_data.exists('.b[0]')

    def test_exists_on_object_key(self, snippet_data):
        assert snippet_data.exists('.c.hello')

    def test_exists_on_missing(self, snippet_data):
        with pytest.raises(NoDataError):
            snippet_data.exists('.d.hello')

    def test_exists_on_missing_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        assert not snippet_data.exists('.d.hello')

    def test_exists_on_sub_node(self, snippet_data):
        assert snippet_data.get_node('.c').exists()


class TestGetNode:
    @pytest.fixture
    def snippet_data(self):
        test_data = {
            'bundle_info': {},
            'merged_blob': {
                'a': {'b': {'c': 'hello world'}},
                'd': ['hello', ['world', 'mars']],
            },
            'metadata_instances': [
                {'payload': {'a': {'b': {'c': 'data1'}}}},
                {'payload': {'a': {'b': {'c': 'data2'}}}},
            ],
        }
        return Node.from_bundle_json(test_data)

    def test_get_value_from_sub_node(self, snippet_data):
        sub_node = snippet_data.get_node('.a.b')
        assert sub_node.get_value('.c') == 'hello world'

    def test_get_all_values_from_sub_node(self, snippet_data):
        sub_node = snippet_data.get_node('.a.b')
        assert sub_node.get_all_values('.c') == ['data2', 'data1']

    def test_get_value_from_array_sub_node(self, snippet_data):
        sub_node = snippet_data.get_node('.d[0]')
        assert sub_node.get_value() == 'hello'

    def test_get_value_from_array_sub_node_index(self, snippet_data):
        sub_node = snippet_data.get_node('.d[1]')
        assert sub_node.get_value('[0]') == 'world'

    def test_get_node_on_missing(self, snippet_data):
        node = snippet_data.get_node('.missing')
        with pytest.raises(NoDataError):
            node.get_value()

    def test_get_node_on_invalid_path(self, snippet_data):
        with pytest.raises(ValueError):
            snippet_data.get_node('.1]')


class TestNodeIteration:
    @pytest.fixture
    def snippet_data(self):
        test_data = {
            'bundle_info': {},
            'merged_blob': {
                'a': 'hello',
                'b': 'world',
                'c': ['hello', ['world', 'mars']],
                'd': {},
                'e': [],
            },
            'metadata_instances': [],
        }
        return Node.from_bundle_json(test_data)

    def test_iterate_over_object(self, snippet_data):
        assert list(snippet_data) == ['a', 'b', 'c', 'd', 'e']

    def test_iterate_over_array(self, snippet_data):
        items = list(snippet_data.get_node('.c'))
        for item in items:
            assert isinstance(item, Node)

        assert [item.get_value() for item in items] == ['hello', ['world', 'mars']]

    def test_iterate_over_scalar(self, snippet_data):
        with pytest.raises(ValueError):
            list(snippet_data.get_node('.a'))

    def test_iterate_dict_items(self, snippet_data):
        items = list(snippet_data.items())
        for key, node in items:
            assert isinstance(key, str)
            assert isinstance(node, Node)

        assert [node.get_value() for key, node in items] == [
            'hello',
            'world',
            ['hello', ['world', 'mars']],
            {},
            [],
        ]

    def test_iterate_dict_items_on_non_dict(self, snippet_data):
        with pytest.raises(ValueError):
            list(snippet_data.get_node('.a').items())

    def test_iterate_dict_items_on_empty_dict(self, snippet_data):
        items = list(snippet_data.get_node('.d').items())
        assert len(items) == 0

    def test_iterate_on_empty_array(self, snippet_data):
        items = list(snippet_data.get_node('.e'))
        assert len(items) == 0


class TestGetValueOrDefault:
    @pytest.fixture
    def snippet_data(self):
        test_data = {
            'a': 'hello',
        }
        return Node.from_component_json(test_data)

    def test_get_value_or_default_on_existing(self, snippet_data):
        assert snippet_data.get_value_or_default('.a', 'default') == 'hello'

    def test_get_value_or_default_on_existing_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        assert snippet_data.get_value_or_default('.a', 'default') == 'hello'

    def test_get_value_or_default_on_missing(self, snippet_data):
        assert snippet_data.get_value_or_default('.b', 'default') == 'default'

    def test_get_value_or_default_on_missing_workflows_finished(self, snippet_data):
        snippet_data._data['bundle_info']['workflows_finished'] = True
        assert snippet_data.get_value_or_default('.b', 'default') == 'default'

    def test_get_value_or_default_none_default(self, snippet_data):
        assert snippet_data.get_value_or_default('.b') is None
