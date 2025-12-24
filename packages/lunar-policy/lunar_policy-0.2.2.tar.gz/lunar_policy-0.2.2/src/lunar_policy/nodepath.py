from dataclasses import dataclass
from typing import Any, Optional, Union
from enum import Enum

from .nodepath_parser import Lark_StandAlone


class SegmentKind(Enum):
    DOT = 'dot'
    LIT = 'lit'
    IDX = 'idx'


@dataclass
class Segment:
    kind: SegmentKind
    key: Optional[str] = None
    index: Optional[int] = None

    def __str__(self) -> str:
        ret = ''

        if self.kind == SegmentKind.DOT:
            ret = f'.{self.key}'
        elif self.kind == SegmentKind.LIT:
            ret = f"['{self.key}']"
        elif self.kind == SegmentKind.IDX:
            ret = ''  # handled below
        else:
            raise ValueError(f'Invalid segment kind: {self.kind}')

        if self.index is not None:
            ret += f'[{self.index}]'

        return ret


class NodePath:
    def __init__(self, segments: list[Segment]):
        self.segments = segments

    @classmethod
    def parse(cls, path: str) -> 'NodePath':
        if not path:
            raise ValueError('Path cannot be empty')

        if path == '.':
            return cls([])

        parser = Lark_StandAlone()

        try:
            tree = parser.parse(path)
            segments = cls._extract_segments_from_tree(tree)
            return cls(segments)
        except Exception as e:
            raise ValueError(f'Invalid path format: {path}') from e

    @staticmethod
    def _extract_segments_from_tree(tree) -> list[Segment]:
        segments = []

        for segment_node in tree.children:
            key = None
            index = None
            kind = None

            for child in segment_node.children:
                if child.data == 'dotsegment':
                    kind = SegmentKind.DOT
                    key = child.children[0].value
                elif child.data == 'litsegment':
                    kind = SegmentKind.LIT
                    key = '' if not child.children else child.children[0].value
                elif child.data == 'index':
                    if kind is None:
                        kind = SegmentKind.IDX
                    index = int(child.children[0].value)

            if key is not None or index is not None:
                segments.append(Segment(kind, key, index))

        return segments

    def concat(self, other: Union['NodePath', str]) -> 'NodePath':
        if isinstance(other, str):
            other = self.parse(other)

        if not isinstance(other, NodePath):
            raise ValueError('Can only concatenate with NodePath or string')

        combined_segments = self.segments + other.segments
        return NodePath(combined_segments)

    def __str__(self) -> str:
        if not self.segments:
            return '.'

        return ''.join(map(str, self.segments))

    def get_value(self, data: dict) -> Optional[Any]:
        if data is None:
            raise ValueError('Data cannot be None')

        if not isinstance(data, dict) and not isinstance(data, list):
            raise ValueError('Data must be a dictionary or list')

        current = data

        for segment in self.segments:
            if segment.kind == SegmentKind.IDX:
                if not isinstance(current, list) or segment.index >= len(current):
                    return None
                current = current[segment.index]
            elif segment.kind == SegmentKind.DOT or segment.kind == SegmentKind.LIT:
                if segment.key not in current:
                    return None

                current = current[segment.key]

                if segment.index is not None:
                    if not isinstance(current, list) or segment.index >= len(current):
                        return None
                    current = current[segment.index]

        return current
