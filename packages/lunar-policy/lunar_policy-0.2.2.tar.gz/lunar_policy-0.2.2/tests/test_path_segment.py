from src.lunar_policy.nodepath import Segment, SegmentKind


class TestSegmentStrings:
    def test_dot_segment(self):
        segment = Segment(kind=SegmentKind.DOT, key='a')
        assert str(segment) == '.a'

    def test_dot_segment_with_index_and_key(self):
        segment = Segment(kind=SegmentKind.DOT, key='a', index=0)
        assert str(segment) == '.a[0]'

    def test_dot_segment_with_empty_key(self):
        segment = Segment(kind=SegmentKind.DOT, key='')
        assert str(segment) == '.'

    def test_lit_segment(self):
        segment = Segment(kind=SegmentKind.LIT, key='a')
        assert str(segment) == "['a']"

    def test_lit_segment_with_empty_key(self):
        segment = Segment(kind=SegmentKind.LIT, key='')
        assert str(segment) == "['']"

    def test_lit_segment_with_index_and_key(self):
        segment = Segment(kind=SegmentKind.LIT, key='a', index=0)
        assert str(segment) == "['a'][0]"
