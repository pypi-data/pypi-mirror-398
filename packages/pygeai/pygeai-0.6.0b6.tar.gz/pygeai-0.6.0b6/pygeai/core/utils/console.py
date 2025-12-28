import sys
from abc import ABC, abstractmethod


class StreamWriter(ABC):
    """
    Abstract base class for custom stream writers.
    """

    @abstractmethod
    def write_stdout(self, message: str = "", end: str = "\n"):
        pass

    @abstractmethod
    def write_stderr(self, message: str = "", end: str = "\n"):
        pass

class ConsoleMeta(type):
    def __getattr__(cls, name):
        writer = cls._writer
        attr = getattr(writer, name, None)
        if callable(attr):
            return attr
        
        def noop(*args, **kwargs):
            pass
        return noop

class Console(metaclass=ConsoleMeta):
    """
    A utility class for writing messages to standard output and standard error streams.

    This class provides static methods to write messages to `sys.stdout` and `sys.stderr`
    with customizable end characters. It serves as a simple abstraction for console output
    operations, ensuring consistent handling of messages in command-line applications.

    Additionally, it allows setting a custom stream writer to override the default behavior,
    enabling redirection of output to alternative targets such as loggers, files, or testing sinks.
    """
    class DefaultStreamWriter(StreamWriter):
        """
        Default StreamWriter that writes to sys.stdout and sys.stderr.
        """
        def write_stdout(self, message: str = "", end: str = "\n"):
            sys.stdout.write(f"{message}{end}")
            sys.stdout.flush()

        def write_stderr(self, message: str = "", end: str = "\n"):
            sys.stderr.write(f"{message}{end}")
            sys.stderr.flush()

    _writer: StreamWriter = DefaultStreamWriter()

    @staticmethod
    def write_stdout(message: str = "", end: str = "\n"):
        """
        Writes a message to the standard output stream (sys.stdout).

        :param message: str - The message to write. Defaults to an empty string.
        :param end: str - The string to append after the message. Defaults to a newline ('\n').
        :return: None - No return value; output is written to sys.stdout.
        """
        Console._writer.write_stdout(message, end)

    @staticmethod
    def write_stderr(message: str = "", end: str = "\n"):
        """
        Writes a message to the standard error stream (sys.stderr).

        :param message: str - The message to write. Defaults to an empty string.
        :param end: str - The string to append after the message. Defaults to a newline ('\n').
        :return: None - No return value; output is written to sys.stderr.
        """
        Console._writer.write_stderr(message, end)

    @staticmethod
    def set_writer(writer: StreamWriter):
        """
        Sets a custom StreamWriter to handle console output.

        :param writer: StreamWriter - Implementation of the StreamWriter interface.
        """
        Console._writer = writer
