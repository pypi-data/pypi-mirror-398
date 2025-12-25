import base64
import collections.abc
import contextlib
import re
import unittest.mock

import grpc.aio
import typing_extensions as typing

from sila.framework.binary_transfer import BinaryTransferError
from sila.framework.errors import SiLAError


@contextlib.contextmanager
def raises(
    expected_exception: type["SiLAError"], match: typing.Union[None, str, re.Pattern] = None
) -> collections.abc.Iterator[grpc.aio.ServicerContext]:
    """
    Assert that a grpc handler raises an exception type.

    Examples:
      Use `raises` as a context manager, which will capture the
      exception of the given type, or any of its subclasses:
      >>> from sila import SiLAError
      >>> from sila.testing import raises
      >>> with raises(SiLAError) as context:
      >>>   await my_grpc_handler(request_message, context)

      If the grpc handler does not raise the expected exception, or
      no exception at all, the check will fail instead.

      You can also use the keyword argument match to assert that the
      exception matches a text or regex:
      >>> from sila import SiLAError
      >>> from sila.testing import raises
      >>> with raises(SiLAError, match=r"must be 0 or None") as context:
      >>>   await my_grpc_handler(request_message, context)

    Args:
      expected_exception: The expected exception type. Note that
        subclasses of the passed exceptions will also match.
      match: If specified, a string containing a regular expression,
        or a regular expression object, that is tested against the
        string representation of the exception

    Yields:
      A mocked grpc servicer context passed into the grpc handler.
    """

    abort = unittest.mock.AsyncMock()

    with contextlib.suppress(expected_exception, StopAsyncIteration):
        yield unittest.mock.Mock(
            spec=grpc.aio.ServicerContext, abort=abort, invocation_metadata=unittest.mock.Mock(return_value=())
        )

    if abort.call_count != 1:
        msg = f"Did not raise {expected_exception}"
        raise AssertionError(msg)

    code: grpc.StatusCode = abort.call_args.kwargs["code"]
    if code != grpc.StatusCode.ABORTED:
        msg = f"Expected status code to be 'aborted', received '{code.value[1]}'."
        raise AssertionError(msg)

    if match is None:
        return

    details: str = abort.call_args.kwargs["details"]
    buffer = base64.b64decode(details)

    if issubclass(expected_exception, BinaryTransferError):
        message = BinaryTransferError.decode(buffer)
    elif issubclass(expected_exception, SiLAError):
        message = SiLAError.decode(buffer)

    pattern = re.compile(match)
    if not pattern.match(message.message):
        msg = f"Regex pattern did not match.\n Regex: {match!r}\n Input: {message.message!r}"
        raise AssertionError(msg)
