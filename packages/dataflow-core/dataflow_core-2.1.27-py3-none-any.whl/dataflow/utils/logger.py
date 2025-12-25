import logging
import sys
import json
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """
    Emit compact one-line JSON for normal logs (ts, funcName, level, msg).
    Emit full JSON (includes traceback, extras, filename, lineno, logger, module, status_code)
    for ERROR and CRITICAL.
    """
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        # base compact payload
        compact = {
            "ts": ts,
            "funcName": record.funcName,
            "level": record.levelname,
            "status_code": getattr(record, "status_code", "---"),
            "msg": record.getMessage(),
        }

        # For ERROR and CRITICAL include full details
        if record.levelno >= logging.ERROR:
            full = {
                "ts": ts,
                "logger": record.name,
                "level": record.levelname,
                "status_code": getattr(record, "status_code", "---"),
                "msg": record.getMessage(),
                "module": record.module,
                "filename": record.filename,
                "lineno": record.lineno,
                "funcName": record.funcName,
            }

            if record.exc_info:
                full["traceback"] = self.formatException(record.exc_info)

            # Collect non-standard attributes passed via extra=...
            standard_attrs = {
                "name","msg","args","levelname","levelno","pathname","filename","module","exc_info",
                "exc_text","stack_info","lineno","funcName","created","msecs","relativeCreated",
                "thread","threadName","processName","process","message"
            }
            extras = {}
            for k, v in record.__dict__.items():
                if k in standard_attrs:
                    continue
                if k.startswith("_"):
                    continue
                if k == "status_code":
                    continue
                extras[k] = v

            if extras:
                full["extra"] = extras

            return json.dumps(full, default=str)

        # else return compact
        return json.dumps(compact, default=str)
    

class CustomLogger:
    """
    Custom logger class for configuring and using console-based logging functionality.
    """
    def __init__(self):
        self._configure_handler()

    def _configure_handler(self):
        """
        Configure the console handler once.
        """
        self.formatter = JsonFormatter()
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(self.formatter)

    def get_logger(self, name=None):
        """
        Retrieve a configured logger instance with a dynamic name.

        Args:
            name (str): The name of the logger. Defaults to 'dataflow_logger'.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger_name = name or "dataflow_logger"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Prevent duplicate handlers if logger already configured
        if not logger.handlers:
            logger.addHandler(self.console_handler)

        return logger
