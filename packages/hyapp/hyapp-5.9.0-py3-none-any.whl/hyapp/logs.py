from __future__ import annotations

import asyncio
import logging
import logging.config
import os
import socket
from typing import TYPE_CHECKING, Any, ClassVar

import coloredlogs
import pythonjsonlogger.json
import yaml

from .traces import LOG_EXTRAS_VAR, TRACE_ID_VAR

if TYPE_CHECKING:
    from collections.abc import Sequence

CL_FMT = "%(asctime)s.%(msecs)03d %(levelname)-5s %(name)s %(message)s%(_extras)s"
EXTRAS_WIDTH: int = 100
EXTRAS_INLINE_INDENT: str = " " * 4
EXTRAS_LINE_INDENT: str = " " * 4

# `socket.getfqdn()` might be more useful, but in some broken setups it might hang.
HOSTNAME = socket.gethostname()
APP_NAME = os.environ.get("APP_NAME") or ""

# http://docs.python.org/library/logging.html#logrecord-attributes
LOGRECORD_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class AnnotatorBase(logging.Filter):
    """A base class for all annotators"""

    def update_record(self, record: logging.LogRecord) -> None:
        raise NotImplementedError

    def filter(self, record: logging.LogRecord) -> bool:
        """“annotate”, actually"""
        self.update_record(record)
        return True


class Annotator(AnnotatorBase):
    """A convenience abstract class for most annotators"""

    default_attribute_name: ClassVar[str | None] = None
    attribute_name: str
    force_overwrite: bool = False

    def __init__(self, *args: Any, attribute_name: str | None = None, **kwargs: Any) -> None:
        if not attribute_name:
            if not self.default_attribute_name:
                raise TypeError("attribute_name should either be on class or always specified")
            attribute_name = self.default_attribute_name
        self.attribute_name = attribute_name
        super().__init__(*args, **kwargs)

    def get_value(self, record: logging.LogRecord) -> Any:
        raise NotImplementedError

    def update_record(self, record: logging.LogRecord) -> None:
        if hasattr(record, self.attribute_name) and not self.force_overwrite:
            return
        value = self.get_value(record)
        setattr(record, self.attribute_name, value)


class HostnameAnnotator(Annotator):
    default_attribute_name: ClassVar[str] = "hostname"

    def get_value(self, record: logging.LogRecord) -> str:
        return HOSTNAME


class AsyncioTaskAnnotator(Annotator):
    default_attribute_name: ClassVar[str] = "aio_task"

    def get_value(self, record: logging.LogRecord) -> str | None:
        try:
            task = asyncio.current_task()
            if task:
                return task.get_name()
        except RuntimeError:
            pass

        return None


class TraceVarAnnotator(Annotator):
    default_attribute_name: ClassVar[str] = "trace_id"

    def get_value(self, record: logging.LogRecord) -> str | None:
        return TRACE_ID_VAR.get()


class LogExtrasVarAnnotator(AnnotatorBase):
    def update_record(self, record: logging.LogRecord) -> None:
        data = LOG_EXTRAS_VAR.get()
        if not data:
            return
        # This could also be `record.__dict__.update(data)`
        # (more performance less compatibility)
        for key, val in data.items():
            setattr(record, key, val)


def serialize_extra(data: dict[str, Any], width: int = EXTRAS_WIDTH) -> str:
    return yaml.dump(
        data,
        Dumper=getattr(yaml, "CDumper", None) or yaml.Dumper,
        default_flow_style=None,
        sort_keys=False,
        allow_unicode=True,
        width=width,
    ).strip("\n")


def postprocess_extra(
    data: str, inline_indent: str = EXTRAS_INLINE_INDENT, line_indent: str = EXTRAS_LINE_INDENT
) -> str:
    data = data.strip()
    if not data:
        return ""
    if "\n" not in data:
        return f"{inline_indent}{data}"
    data_indented = data.strip().replace("\n", f"\n{line_indent}")
    return f"\n{line_indent}{data_indented}"


class ExtrasAnnotator(Annotator):
    """Build a string with readable serialization of non-formatted log fields"""

    default_attribute_name: ClassVar[str] = "_extras"
    width: int = EXTRAS_WIDTH
    inline_indent: str = EXTRAS_INLINE_INDENT
    line_indent: str = EXTRAS_LINE_INDENT

    def serialize_data(self, data: dict[str, Any]) -> str:
        return serialize_extra(data, width=self.width)

    def postprocess_serialized_data(self, data: str) -> str:
        return postprocess_extra(data, inline_indent=self.inline_indent, line_indent=self.line_indent)

    def get_value(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            key: value
            for key, value in record.__dict__.items()
            if key not in LOGRECORD_ATTRS and not (hasattr(key, "startswith") and key.startswith("_"))
        }
        if not data:
            return ""
        data_s = self.serialize_data(data)
        return self.postprocess_serialized_data(data_s)


class TunedJSONFormatter(pythonjsonlogger.json.JsonFormatter):
    DEFAULT_FIELDS: ClassVar[Sequence[str]] = (
        "created",
        "asctime",
        "levelname",
        "name",
        "message",
        "pid",
    )
    DEFAULT_RENAME_FIELDS: ClassVar[dict[str, str]] = {
        "asctime": "time",
        "created": "ts",
    }
    DEFALT_BEGINNING_FIELDS: ClassVar[Sequence[str]] = (
        "time",
        "ts",
        "levelname",
        "name",
        "message",
        "hostname",
        "pid",
        "aio_task",
        "trace_id",
    )

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03dZ"

    def __init__(
        self,
        fmt: str | None = None,
        *,
        fields: Sequence[str] | None = None,
        rename_fields: dict[str, str] | None = None,
        beginning_fields: Sequence[str] | None = None,
        **kwargs,
    ) -> None:
        if fmt is not None:
            raise ValueError("Avoid specifying `fmt` here.")

        self.fields = fields or self.DEFAULT_FIELDS
        fmt = " ".join(f"%({fld})s" for fld in self.fields)

        super().__init__(
            fmt, rename_fields=self.DEFAULT_RENAME_FIELDS if rename_fields is None else rename_fields, **kwargs
        )
        self.beginning_fields = beginning_fields if beginning_fields is not None else self.DEFALT_BEGINNING_FIELDS

    def process_log_record(self, log_record: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key in self.beginning_fields:
            # Note: mutating the log_record for performance reasons.
            result[key] = log_record.pop(key)
        result.update(log_record)
        return result


COMMON_LOGGING_ANNOTATORS = ["asyncio_task_annotator", "trace_var_annotator"]
LOGGING_COMMON: logging.config._DictConfigArgs = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "hostname_annotator": {"()": "hyapp.logs.HostnameAnnotator"},
        "asyncio_task_annotator": {"()": "hyapp.logs.AsyncioTaskAnnotator"},
        "trace_var_annotator": {"()": "hyapp.logs.TraceVarAnnotator"},
        "log_extras_var_annotator": {"()": "hyapp.logs.LogExtrasVarAnnotator"},
    },
    "formatters": {
        "ndjson": {"()": "hyapp.logs.TunedJSONFormatter"},
    },
    "handlers": {
        "stderr_ndjson": {
            "class": "logging.StreamHandler",
            "filters": ["hostname_annotator", *COMMON_LOGGING_ANNOTATORS],
            "formatter": "ndjson",
            "level": "DEBUG",
        },
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        # Reduce the amount of logs of some known too-much-logging libraries.
        "pytest_blockage": {"level": "INFO"},
        "urllib3.connectionpool": {"level": "INFO"},
    },
    "root": {
        "level": "DEBUG",
        "handlers": [],
    },
}
LOGGING_DEPLOYED: logging.config._DictConfigArgs = {
    **LOGGING_COMMON,
    "root": {
        **LOGGING_COMMON["root"],
        "handlers": [*LOGGING_COMMON["root"]["handlers"], "stderr_ndjson"],
    },
}
LOGGING_DEV: logging.config._DictConfigArgs = {
    **LOGGING_COMMON,
    "filters": {
        **LOGGING_COMMON["filters"],
        "extras_annotator": {"()": "hyapp.logs.ExtrasAnnotator"},
    },
    "formatters": {
        **LOGGING_COMMON["formatters"],
        "coloredlogs": {
            "class": "coloredlogs.ColoredFormatter",
            "format": CL_FMT,
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        **LOGGING_COMMON["handlers"],
        "stderr_coloredlogs": {
            "class": "logging.StreamHandler",
            "filters": [*COMMON_LOGGING_ANNOTATORS, "extras_annotator"],
            "formatter": "coloredlogs",
            "level": "DEBUG",
        },
    },
    "root": {
        **LOGGING_COMMON["root"],
        "handlers": [*LOGGING_COMMON["root"]["handlers"], "stderr_coloredlogs"],
    },
}


def init_dev_logs(fmt: str = CL_FMT) -> None:
    coloredlogs.install(fmt=fmt, level="DEBUG", milliseconds=True)
    logger = logging.getLogger()

    for handler in logger.handlers:
        handler.addFilter(AsyncioTaskAnnotator())
        handler.addFilter(TraceVarAnnotator())
        handler.addFilter(LogExtrasVarAnnotator())
        handler.addFilter(ExtrasAnnotator())


def init_dev_logs_pure() -> None:
    logging.config.dictConfig(LOGGING_DEV)


def init_logs() -> None:
    logging.config.dictConfig(LOGGING_DEPLOYED)
