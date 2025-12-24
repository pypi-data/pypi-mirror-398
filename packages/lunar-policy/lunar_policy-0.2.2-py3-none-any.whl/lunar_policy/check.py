import json
import os
import re
from typing import Any, Callable, List, Optional
from pathlib import Path as FSPath

from .node import Node
from .result import AssertionResult, Op, CheckStatus, NoDataError, SkippedError


class Check:
    def __init__(self, name: str, description: Optional[str] = None, node: Optional[Node] = None):
        self._name = name
        self._description = description
        self._used_vars = []
        self._results = []
        self._submitted = False

        if node is None:
            try:
                path = os.environ['LUNAR_BUNDLE_PATH']
            except KeyError:
                raise ValueError('LUNAR_BUNDLE_PATH is not set')

            try:
                node = Node.from_bundle_file(FSPath(path))
            except ValueError as e:
                raise ValueError('invalid LUNAR_BUNDLE_PATH') from e
            except FileNotFoundError:
                raise ValueError(f'LUNAR_BUNDLE_PATH does not exist: {path}')

        if not isinstance(node, Node):
            raise ValueError(f'Data must be a Node instance, got {node}')

        self._path_tracker = node._path_tracker  # Reusing the Node's path tracker to avoid weird injection
        self._node = node

    # Context Manager

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        is_no_data_error = isinstance(exc_value, NoDataError)
        is_skipped_error = isinstance(exc_value, SkippedError)

        is_suppressable_no_data = is_no_data_error and not self._node._workflows_finished()
        is_suppressable_error = is_suppressable_no_data or is_skipped_error

        if exc_value is not None:
            if is_skipped_error:
                # Clear all previous results and replace with a single skipped result
                self._results = [
                    AssertionResult(
                        op=Op.SKIP,
                        args=[],
                        result=CheckStatus.SKIPPED,
                        failure_message=str(exc_value),
                    )
                ]
            elif is_suppressable_no_data:
                self._results.append(
                    AssertionResult(
                        op=Op.FAIL,
                        args=[],
                        result=CheckStatus.PENDING,
                        failure_message=str(exc_value),
                    )
                )
            elif is_no_data_error:
                self._results.append(
                    AssertionResult(
                        op=Op.FAIL,
                        args=[],
                        result=CheckStatus.ERROR,
                        failure_message=f'Unexpected error: {exc_value}',
                    )
                )
            else:
                self._results.append(
                    AssertionResult(
                        op=Op.FAIL,
                        args=[],
                        result=CheckStatus.ERROR,
                        failure_message=str(exc_value),
                    )
                )

        self._submit()
        # Suppress SkippedError and suppressable NoDataError, let others propagate
        return is_suppressable_error

    # Properties

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> CheckStatus:
        if not self._results:
            return CheckStatus.PASS

        has_no_data = False
        has_fail = False
        has_error = False

        for result in self._results:
            if result.result == CheckStatus.ERROR:
                has_error = True
            if result.result == CheckStatus.PENDING:
                has_no_data = True
            if result.result == CheckStatus.FAIL:
                has_fail = True

        if has_error:
            return CheckStatus.ERROR
        if has_no_data:
            return CheckStatus.PENDING
        elif has_fail:
            return CheckStatus.FAIL

        return CheckStatus.PASS

    @property
    def failure_reasons(self) -> list:
        failure_messages = [
            result.failure_message
            for result in self._results
            if (result.result == CheckStatus.FAIL and result.failure_message is not None)
        ]
        return failure_messages

    # Root node wrappers

    def get_value(self, path: str = '.') -> Any:
        return self._node.get_value(path)

    def get_node(self, path: str) -> Node:
        return self._node.get_node(path)

    def get_all_values(self, path: str = '.') -> List[Any]:
        return self._node.get_all_values(path)

    def get_value_or_default(self, path: str = '.', default: Any = None) -> Any:
        return self._node.get_value_or_default(path, default)

    def exists(self, path: str = '.') -> bool:
        return self._node.exists(path)

    # Iteration

    def __iter__(self):
        return iter(self._node)

    def items(self):
        return self._node.items()

    # Flow control

    def fail(self, failure_message: Optional[str] = None) -> None:
        self._make_assertion(
            Op.FAIL,
            lambda v: False,
            False,
            failure_message or 'Policy Forced Failure',
        )

    def skip(self, reason: Optional[str] = None) -> None:
        raise SkippedError(reason or 'Check skipped')

    # Assertions

    def assert_true(
        self,
        value: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.TRUE,
            lambda v: v is True,
            value,
            failure_message or f'{value} is not true',
        )

    def assert_false(
        self,
        value: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.FALSE,
            lambda v: v is False,
            value,
            failure_message or f'{value} is not false',
        )

    def assert_equals(
        self,
        value: Any,
        expected: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.EQUALS,
            lambda v: v == expected,
            value,
            failure_message or f'{value} is not equal to {expected}',
        )

    def assert_contains(
        self,
        value: Any,
        expected: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.CONTAINS,
            lambda v: expected in v,
            value,
            failure_message or f'{value} does not contain {expected}',
        )

    def assert_greater(
        self,
        value: Any,
        expected: Any,
        failure_message: Optional[str] = None,
    ):
        self._make_assertion(
            Op.GREATER,
            lambda v: v > expected,
            value,
            failure_message or f'{value} is not greater than {expected}',
        )

    def assert_greater_or_equal(
        self,
        value: Any,
        expected: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.GREATER_OR_EQUAL,
            lambda v: v >= expected,
            value,
            failure_message or f'{value} is not greater than or equal to {expected}',
        )

    def assert_less(
        self,
        value: Any,
        expected: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.LESS,
            lambda v: v < expected,
            value,
            failure_message or f'{value} is not less than {expected}',
        )

    def assert_less_or_equal(
        self,
        value: Any,
        expected: Any,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.LESS_OR_EQUAL,
            lambda v: v <= expected,
            value,
            failure_message or f'{value} is not less than or equal to {expected}',
        )

    def assert_match(
        self,
        value: Any,
        pattern: str,
        failure_message: Optional[str] = None,
    ) -> None:
        self._make_assertion(
            Op.MATCH,
            lambda v: re.match(pattern, v) is not None,
            value,
            failure_message or f'{value} does not match {pattern}',
        )

    def assert_exists(self, path: str, failure_message: Optional[str] = None) -> None:
        # This assertion behaves differently than the others, so it gets its
        # own implementation. Normal no-data behavior before workflows completed, fail afterward.

        try:
            self._make_assertion(
                Op.EXISTS,
                lambda v: v is not None,
                self.get_value(path),
                failure_message or f'{path} does not exist',
            )
        except ValueError:
            self._results.append(
                AssertionResult(
                    op=Op.FAIL,
                    args=[],
                    result=CheckStatus.FAIL,
                    failure_message=(failure_message or f'{path} does not exist'),
                )
            )

    # Private methods

    def _submit(self):
        if not self._submitted:
            output = {
                'name': self._name,
                'assertions': [result.toJson() for result in self._results],
            }

            output['paths'] = list(
                dict.fromkeys(p if p.startswith('.') else f'.{p}' for p in self._path_tracker.get_paths())
            )

            if self._description is not None:
                output['description'] = self._description

            prefix = os.environ.get('LUNAR_LOG_PREFIX', '')
            print(f'{prefix}{json.dumps(output)}')

            self._submitted = True

    def _make_assertion(
        self,
        op: Op,
        check_fn: Callable[[Any], bool],
        value: Any,
        failure_message: str,
    ):
        if value is None:
            raise NoDataError('Value was None')

        ok = check_fn(value)

        try:
            # We don't care about the actual value,
            # we just want to make sure its serializable at submission time
            serialized_value = str(value)
        except Exception as e:
            type_name = type(value).__name__
            serialized_value = f'<typename {type_name}: {e}>'

        self._results.append(
            AssertionResult(
                op=op,
                args=[serialized_value],
                result=CheckStatus.PASS if ok else CheckStatus.FAIL,
                failure_message=failure_message if not ok else None,
            )
        )
