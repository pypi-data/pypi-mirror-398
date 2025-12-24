import logging

from .py_hpl_logger import Logger


class RustLogHandler(logging.Handler):
    """
    A Python logging handler that forwards all log records to the
    high-performance Rust logger.
    """

    def __init__(self, rust_logger: Logger):
        """
        Initializes the handler with a configured Rust Logger instance.

        Args:
            rust_logger: An instance of py_hpl_logger.Logger,
                         already configured and built.
        """
        super().__init__()
        self.rust_logger = rust_logger

    def emit(self, record: logging.LogRecord) -> None:
        """
        This method is called by the logging framework for each log record.
        It formats the record and sends it to the Rust backend.
        """
        try:
            msg = self.format(record)

            if record.levelno == logging.ERROR:
                self.rust_logger.error(msg)
            elif record.levelno == logging.INFO:
                self.rust_logger.info(msg)
            elif record.levelno == logging.WARNING:
                self.rust_logger.warning(msg)
            elif record.levelno == logging.DEBUG:
                self.rust_logger.debug(msg)
            else:
                raise NotImplementedError(f"Unsupported log level: {record.levelno}")
        except Exception:
            self.handleError(record)
