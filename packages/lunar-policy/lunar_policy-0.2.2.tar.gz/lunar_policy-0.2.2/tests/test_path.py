from src.lunar_policy.nodepath import NodePath, Segment, SegmentKind
import pytest


class TestNodePathValidSyntax:
    def test_simple_path(self):
        path = NodePath.parse('.a.b.c')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.DOT, key='b'),
            Segment(kind=SegmentKind.DOT, key='c'),
        ]

    def test_path_with_numbers_in_key(self):
        path = NodePath.parse('.a1.b2.c3')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a1'),
            Segment(kind=SegmentKind.DOT, key='b2'),
            Segment(kind=SegmentKind.DOT, key='c3'),
        ]

    def test_path_with_longer_names(self):
        path = NodePath.parse('.these.are.not.the.droids.you.are.looking.for')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='these'),
            Segment(kind=SegmentKind.DOT, key='are'),
            Segment(kind=SegmentKind.DOT, key='not'),
            Segment(kind=SegmentKind.DOT, key='the'),
            Segment(kind=SegmentKind.DOT, key='droids'),
            Segment(kind=SegmentKind.DOT, key='you'),
            Segment(kind=SegmentKind.DOT, key='are'),
            Segment(kind=SegmentKind.DOT, key='looking'),
            Segment(kind=SegmentKind.DOT, key='for'),
        ]

    def test_path_with_trailing_index(self):
        path = NodePath.parse('.a.b[0]')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.DOT, key='b', index=0),
        ]

    def test_path_with_inner_index(self):
        path = NodePath.parse('.a.b[0].c')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.DOT, key='b', index=0),
            Segment(kind=SegmentKind.DOT, key='c'),
        ]

    def test_path_with_multiple_indexes(self):
        path = NodePath.parse('.a.b[0].c[1]')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.DOT, key='b', index=0),
            Segment(kind=SegmentKind.DOT, key='c', index=1),
        ]

    def test_path_with_multiple_consecutive_indexes(self):
        path = NodePath.parse('.a.b[0].c[1][2]')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.DOT, key='b', index=0),
            Segment(kind=SegmentKind.DOT, key='c', index=1),
            Segment(kind=SegmentKind.IDX, index=2),
        ]

    def test_root_path(self):
        path = NodePath.parse('.')
        assert path.segments == []

    def test_literal_segment(self):
        path = NodePath.parse(".a['!#$ %&'].c")
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.LIT, key='!#$ %&'),
            Segment(kind=SegmentKind.DOT, key='c'),
        ]

    def test_literal_segment_with_index(self):
        path = NodePath.parse(".a['~'][0].c")
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.LIT, key='~', index=0),
            Segment(kind=SegmentKind.DOT, key='c'),
        ]

    def test_literal_multiple_segments(self):
        path = NodePath.parse("['a']['b']['c']")
        assert path.segments == [
            Segment(kind=SegmentKind.LIT, key='a'),
            Segment(kind=SegmentKind.LIT, key='b'),
            Segment(kind=SegmentKind.LIT, key='c'),
        ]

    def test_underscore_allowed_in_key(self):
        path = NodePath.parse('.a._b.c')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='a'),
            Segment(kind=SegmentKind.DOT, key='_b'),
            Segment(kind=SegmentKind.DOT, key='c'),
        ]

    def test_underscore_allowed_start_of_key(self):
        path = NodePath.parse('._a.b')
        assert path.segments == [
            Segment(kind=SegmentKind.DOT, key='_a'),
            Segment(kind=SegmentKind.DOT, key='b'),
        ]

    def test_path_with_escaped_quotes_in_literal(self):
        path = NodePath.parse("['a\\'b']")
        assert path.segments == [Segment(kind=SegmentKind.LIT, key="a\\'b")]

    def test_path_with_backslash_in_literal(self):
        path = NodePath.parse("['a\\\\b']")
        assert path.segments == [Segment(kind=SegmentKind.LIT, key='a\\\\b')]

    def test_path_with_empty_literal(self):
        path = NodePath.parse("['']")
        assert path.segments == [Segment(kind=SegmentKind.LIT, key='')]

    def test_path_with_very_long_index(self):
        path = NodePath.parse('.a[999999999]')
        assert path.segments == [Segment(kind=SegmentKind.DOT, key='a', index=999999999)]

    def test_path_with_unicode_characters(self):
        path = NodePath.parse("['café']['ñoño']")
        assert path.segments == [
            Segment(kind=SegmentKind.LIT, key='café'),
            Segment(kind=SegmentKind.LIT, key='ñoño'),
        ]

    def test_path_with_array_root(self):
        path = NodePath.parse('[0]')
        assert path.segments == [Segment(kind=SegmentKind.IDX, index=0)]

    def test_nested_rooted_arrays(self):
        path = NodePath.parse('[0][1]')
        assert path.segments == [
            Segment(kind=SegmentKind.IDX, index=0),
            Segment(kind=SegmentKind.IDX, index=1),
        ]


class TestNodePathInvalidSyntax:
    def test_empty_path(self):
        with pytest.raises(ValueError):
            NodePath.parse('')

    def test_path_without_leading_period(self):
        with pytest.raises(ValueError):
            NodePath.parse('a.b.c')

    def test_path_with_empty_segment(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a..b')

    def test_path_with_open_bracket(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.b[')

    def test_path_with_close_bracket(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.b]')

    def test_path_with_invalid_index(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.b[notanindex]')

    def test_path_with_invalid_characters(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.b-')

    def test_path_with_extra_opening_bracket(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.b[[0]')

    def test_path_with_extra_closing_bracket(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.b[0]]')

    def test_path_with_whitespace(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a.be cool')

    def test_path_with_numbers_only_in_key(self):
        with pytest.raises(ValueError):
            NodePath.parse('.1.2.3')

    def test_path_start_with_numbers(self):
        with pytest.raises(ValueError):
            NodePath.parse('.1a.2b.3c')

    def test_path_with_unicode_characters(self):
        with pytest.raises(ValueError):
            NodePath.parse('.café.ñoño')

    def test_path_index_wildcard(self):
        with pytest.raises(ValueError):
            NodePath.parse('.a[*]')


class TestNodePathGetValueInvalidValue:
    def test_none_value(self):
        with pytest.raises(ValueError):
            NodePath.parse(None)


class TestNodePathConcat:
    def test_concat_simple_paths(self):
        path1 = NodePath.parse('.a.b')
        path2 = NodePath.parse('.c.d')
        combined = path1.concat(path2)
        assert str(combined) == '.a.b.c.d'

    def test_concat_path_with_trailing_index(self):
        path1 = NodePath.parse('.a.b[0]')
        path2 = NodePath.parse('.c.d')
        combined = path1.concat(path2)
        assert str(combined) == '.a.b[0].c.d'

    def test_concat_path_with_inner_index(self):
        path1 = NodePath.parse('.a.b[0].c')
        path2 = NodePath.parse('.d.e')
        combined = path1.concat(path2)
        assert str(combined) == '.a.b[0].c.d.e'

    def test_concat_path_both_with_indexes(self):
        path1 = NodePath.parse('.a.b[0].c[1]')
        path2 = NodePath.parse('.d.e[2]')
        combined = path1.concat(path2)
        assert str(combined) == '.a.b[0].c[1].d.e[2]'

    def test_concat_path_with_string(self):
        path1 = NodePath.parse('.a.b')
        path2 = '.c.d'
        combined = path1.concat(path2)
        assert str(combined) == '.a.b.c.d'

    def test_concat_path_with_literal_string(self):
        path1 = NodePath.parse('.a.b')
        path2 = "['c'].d"
        combined = path1.concat(path2)
        assert str(combined) == ".a.b['c'].d"

    def test_concat_path_with_right_literal(self):
        path1 = NodePath.parse('.a.b')
        path2 = NodePath.parse("['c'].d")
        combined = path1.concat(path2)
        assert str(combined) == ".a.b['c'].d"

    def test_concat_path_with_left_literal(self):
        path1 = NodePath.parse("['a'].b")
        path2 = NodePath.parse('.c.d')
        combined = path1.concat(path2)
        assert str(combined) == "['a'].b.c.d"

    def test_concat_path_with_both_literals(self):
        path1 = NodePath.parse("['a'].b")
        path2 = NodePath.parse("['c'].d")
        combined = path1.concat(path2)
        assert str(combined) == "['a'].b['c'].d"

    def test_concat_path_only_literals(self):
        path1 = NodePath.parse("['a']")
        path2 = NodePath.parse("['b']")
        combined = path1.concat(path2)
        assert str(combined) == "['a']['b']"

    def test_concat_root_path_left(self):
        path1 = NodePath.parse('.')
        path2 = NodePath.parse('.a.b')
        combined = path1.concat(path2)
        assert str(combined) == '.a.b'

    def test_concat_root_path_right(self):
        path1 = NodePath.parse('.a.b')
        path2 = NodePath.parse('.')
        combined = path1.concat(path2)
        assert str(combined) == '.a.b'

    def test_concat_root_path_both(self):
        path1 = NodePath.parse('.')
        path2 = NodePath.parse('.')
        combined = path1.concat(path2)
        assert str(combined) == '.'

    def test_concat_path_with_array_root(self):
        path1 = NodePath.parse('[0]')
        path2 = NodePath.parse('.a.b')
        combined = path1.concat(path2)
        assert str(combined) == '[0].a.b'

    def test_concat_path_with_array_root_and_literal(self):
        path1 = NodePath.parse('[0]')
        path2 = NodePath.parse("['a'].b")
        combined = path1.concat(path2)
        assert str(combined) == "[0]['a'].b"

    def test_concat_two_array_roots(self):
        path1 = NodePath.parse('[0]')
        path2 = NodePath.parse('[1]')
        combined = path1.concat(path2)
        assert str(combined) == '[0][1]'

    def test_concat_literal_with_index_and_array_root(self):
        path1 = NodePath.parse("['a'][0]")
        path2 = NodePath.parse('[1]')
        combined = path1.concat(path2)
        assert str(combined) == "['a'][0][1]"


class TestNodePathConcatInvalidValue:
    def test_concat_none_value(self):
        path1 = NodePath.parse('.')
        with pytest.raises(ValueError):
            path1.concat(None)

    def test_concat_invalid_path(self):
        path1 = NodePath.parse('.')
        with pytest.raises(ValueError):
            path1.concat('invalid path')

    def test_concat_invalid_type(self):
        path1 = NodePath.parse('.')
        with pytest.raises(ValueError):
            path1.concat(123)


getValueTestObject = {
    'root_value': 'root_value',
    'nested': {'value': 'nested_value'},
    'array_string': ['a', 'b', 'c'],
    'array_object': [{'obj1': 'obj1_value'}, {'obj2': 'obj2_value'}],
    '!@#_ $*[]': 'special_value',
    '****': {'****': 'nested_special_value'},
    '': 'empty_string_value',
    'nested_array': [
        'hello',
        ['nested_array_value', {'d': 'nested_array_object_value'}],
    ],
}

getValueTestArray = [1, 'hello', {'a': 'b', 'c': [1, 'hello']}]


class TestNodePathGetValue:
    def test_get_value_simple_path(self):
        path = NodePath.parse('.root_value')
        assert path.get_value(getValueTestObject) == 'root_value'

    def test_get_value_nested_path(self):
        path = NodePath.parse('.nested.value')
        assert path.get_value(getValueTestObject) == 'nested_value'

    def test_get_value_missing_path(self):
        path = NodePath.parse('.missing')
        assert path.get_value(getValueTestObject) is None

    def test_get_value_array_string_path(self):
        path = NodePath.parse('.array_string[0]')
        assert path.get_value(getValueTestObject) == 'a'

    def test_get_value_array_string_path_out_of_bounds(self):
        path = NodePath.parse('.array_string[3]')
        assert path.get_value(getValueTestObject) is None

    def test_get_value_array_object_path(self):
        path = NodePath.parse('.array_object[1].obj2')
        assert path.get_value(getValueTestObject) == 'obj2_value'

    def test_get_value_special_characters_path(self):
        path = NodePath.parse("['!@#_ $*[]']")
        assert path.get_value(getValueTestObject) == 'special_value'

    def test_get_value_nested_special_characters_path(self):
        path = NodePath.parse("['****']['****']")
        assert path.get_value(getValueTestObject) == 'nested_special_value'

    def test_get_value_empty_string_path(self):
        path = NodePath.parse("['']")
        assert path.get_value(getValueTestObject) == 'empty_string_value'

    def test_get_value_nested_array_path(self):
        path = NodePath.parse('.nested_array[1][0]')
        assert path.get_value(getValueTestObject) == 'nested_array_value'

    def test_get_value_nested_array_object_path(self):
        path = NodePath.parse('.nested_array[1][1].d')
        assert path.get_value(getValueTestObject) == 'nested_array_object_value'

    def test_get_value_array_path(self):
        path = NodePath.parse('[0]')
        assert path.get_value(getValueTestArray) == 1

    def test_get_value_array_path_out_of_bounds(self):
        path = NodePath.parse('[3]')
        assert path.get_value(getValueTestArray) is None

    def test_get_value_array_path_nested_object_path(self):
        path = NodePath.parse('[2].c[0]')
        assert path.get_value(getValueTestArray) == 1


class TestNodePathGetValueInvalidData:
    def test_get_value_none_value(self):
        with pytest.raises(ValueError):
            NodePath.parse('.').get_value(None)

    def test_get_value_non_dict_value(self):
        with pytest.raises(ValueError):
            NodePath.parse('.').get_value('not a dict')
