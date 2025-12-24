import contextlib
import io
import typing


@contextlib.contextmanager
def as_text(
    input_file: typing.TextIO | typing.BinaryIO,
    newline: str | None = None,
    encoding: str = "utf8",
) -> typing.ContextManager[typing.TextIO]:
    """Wrap the given input file object as a text io object if it's binary, pass through the input file object
    if it's already a text file

    :param input_file: the input file object to wrap
    :param newline: the newline chars to use when we need to wrap a binary input file
    :param encoding: the encoding to use when we need to wrap a binary input file
    :return:
    """
    if isinstance(input_file, io.TextIOBase):
        yield input_file
    else:
        text_file = io.TextIOWrapper(input_file, newline=newline, encoding=encoding)
        try:
            yield text_file
        finally:
            # always detach the underlying binary file so that it can be reused again
            text_file.detach()
