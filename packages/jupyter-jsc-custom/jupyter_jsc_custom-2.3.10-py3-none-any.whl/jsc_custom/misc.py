import asyncio
import copy
import json
import logging
import os
import socket
import sys
import threading

import yaml
from jsonformatter import JsonFormatter
from jupyterhub.app import app_log

_global_sse = asyncio.Event()


def get_global_sse():
    global _global_sse
    return _global_sse


logged_logger_name = os.environ.get("LOGGER_NAME", "JupyterHub")
logger_name = "JupyterHub"

_custom_config_cache = {}
_custom_config_last_update = 0
_custom_config_file = os.environ.get("CUSTOM_CONFIG_PATH")
_custom_config_force_init_n_times = 10

_logging_cache = {}

log = logging.getLogger("JupyterHub")
background_tasks = []


def get_logging_config():
    global _logging_cache
    return _logging_cache


# Custom Config comes from a ConfigMap in Kubernetes
def get_custom_config():
    global _custom_config_cache
    global _custom_config_last_update
    global _custom_config_force_init_n_times
    global _logging_cache

    # Only update custom_config, if it has changed on disk
    try:
        last_change = os.path.getmtime(_custom_config_file)
        if (
            last_change > _custom_config_last_update
            or _custom_config_force_init_n_times > 0
        ):
            app_log.debug("Load custom config file.")
            with open(_custom_config_file, "r") as f:
                ret = yaml.full_load(f)
            _custom_config_last_update = last_change
            _custom_config_cache = ret

            if (
                _custom_config_cache.get("logging", {}) != _logging_cache
                or _custom_config_force_init_n_times > 0
            ):
                _logging_cache = _custom_config_cache.get("logging", {})
                app_log.debug("Update Logger")
                update_extra_handlers()
            _custom_config_force_init_n_times -= 1

    except:
        app_log.exception("Could not load custom config file")
    else:
        return _custom_config_cache


_incidents_path = os.environ.get("INCIDENTS_PATH", "/mnt/shared-data/incidents.json")
_reservations_path = os.environ.get(
    "RESERVATIONS_PATH", "/mnt/shared-data/reservations.json"
)

_reservations_cache = {}
_last_change_reservation = 0


def get_last_reservation_change():
    global _last_change_reservation
    return _last_change_reservation


def get_reservations(user=None):
    global _last_change_reservation
    global _reservations_cache

    bkp = _reservations_cache.copy()
    try:
        last_change = os.path.getmtime(_reservations_path)
        if last_change > _last_change_reservation:
            _last_change_reservation = last_change
            try:
                with open(_reservations_path, "r") as f:
                    _reservations_cache = json.load(f)
                get_global_sse().set()
            except:
                log.exception("Reservation check failed. Use backup")
                _reservations_cache = bkp
    except:
        log.exception("Reservation check failed. Use backup")
        _reservations_cache = bkp
    return _reservations_cache


_incidents_cache = {}
_last_change_incidents = 0


def get_last_incidents_change():
    global _last_change_incidents
    return _last_change_incidents


def get_incidents(user=None):
    global _last_change_incidents
    global _incidents_cache

    bkp = _incidents_cache.copy()
    try:
        last_change = os.path.getmtime(_incidents_path)
        if last_change > _last_change_incidents:
            _last_change_incidents = last_change
            try:
                with open(_incidents_path, "r") as f:
                    _incidents_cache = json.load(f)
                get_global_sse().set()
            except:
                log.exception("Incident check failed. Use backup")
                _incidents_cache = bkp
    except:
        log.exception("Incident check failed. Use backup")
        _incidents_cache = bkp

    return _incidents_cache


async def regular_updates():
    # We're checking for reservations / incidents updates every 30 seconds
    # That way SSE can forward updates to the frontend
    while True:
        try:
            get_reservations()
        except:
            pass
        try:
            get_incidents()
        except:
            pass
        await asyncio.sleep(30)


background_tasks.append(asyncio.create_task(regular_updates()))


async def create_ns(user):
    ns = dict(user=user)
    if user:
        auth_state = await user.get_auth_state()
        if "refresh_token" in auth_state.keys():
            del auth_state["refresh_token"]
        ns["auth_state"] = auth_state
    return ns


class ExtraFormatter(logging.Formatter):
    dummy = logging.LogRecord(None, None, None, None, None, None, None)
    ignored_extras = [
        "args",
        "asctime",
        "created",
        "color",
        "end_color",
        "exc_info",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    ]

    def format(self, record):
        extra_txt = ""
        for k, v in record.__dict__.items():
            if k not in self.dummy.__dict__ and k not in self.ignored_extras:
                extra_txt += " --- {}={}".format(k, v)
        message = super().format(record)
        return message + extra_txt


# Translate level to int
def get_level(level_str):
    if type(level_str) == int:
        return level_str
    elif level_str.upper() in logging._nameToLevel.keys():
        return logging._nameToLevel[level_str.upper()]
    elif level_str.upper() == "TRACE":
        return 5
    elif level_str.upper().startswith("DEACTIVATE"):
        return 99
    else:
        try:
            return int(level_str)
        except ValueError:
            pass
    raise NotImplementedError(f"{level_str} as level not supported.")


# supported classes
supported_handler_classes = {
    "stream": logging.StreamHandler,
    "file": logging.handlers.TimedRotatingFileHandler,
    "smtp": logging.handlers.SMTPHandler,
    "syslog": logging.handlers.SysLogHandler,
}

# supported formatters and their arguments
supported_formatter_classes = {"json": JsonFormatter, "simple": ExtraFormatter}
json_fmt = {
    "asctime": "asctime",
    "levelno": "levelno",
    "levelname": "levelname",
    "logger": logged_logger_name,
    "file": "pathname",
    "line": "lineno",
    "function": "funcName",
    "Message": "message",
}
simple_fmt = f"%(asctime)s logger={logged_logger_name} levelno=%(levelno)s levelname=%(levelname)s file=%(pathname)s line=%(lineno)d function=%(funcName)s : %(message)s"
supported_formatter_kwargs = {
    "json": {"fmt": json_fmt, "mix_extra": True},
    "simple": {"fmt": simple_fmt},
}


def update_extra_handlers():
    global _logging_cache
    logging_config = copy.deepcopy(_logging_cache)
    logger = logging.getLogger(logger_name)

    if logging.getLevelName(5) != "TRACE":
        # First call
        # Remove default StreamHandler
        if len(logger.handlers) > 0:
            logger.removeHandler(logger.handlers[0])

        # In trace will be sensitive information like tokens
        logging.addLevelName(5, "TRACE")

        def trace_func(self, message, *args, **kws):
            if self.isEnabledFor(5):
                # Yes, logger takes its '*args' as 'args'.
                self._log(5, message, args, **kws)

        logging.Logger.trace = trace_func
        logger.setLevel(5)

    logger_handlers = logger.handlers
    handler_names = [x.name for x in logger_handlers]
    if len(logger.handlers) > 0 and logger.handlers[0].name == "console":
        # Remove default handler, which will be added after the initial call in here
        logger.removeHandler(logger.handlers[0])

    for handler_name, handler_config in logging_config.items():
        if (not handler_config.get("enabled", False)) and handler_name in handler_names:
            # Handler was disabled, remove it
            logger.handlers = [x for x in logger_handlers if x.name != handler_name]
            logger.debug(f"Logging handler removed ({handler_name})")
        elif handler_config.get("enabled", False):
            # Recreate handlers which has changed their config
            configuration = copy.deepcopy(handler_config)

            # map some special values
            if handler_name == "stream":
                if configuration["stream"] == "ext://sys.stdout":
                    configuration["stream"] = sys.stdout
                elif configuration["stream"] == "ext://sys.stderr":
                    configuration["stream"] = sys.stderr
            elif handler_name == "syslog":
                if configuration["socktype"] == "ext://socket.SOCK_STREAM":
                    configuration["socktype"] = socket.SOCK_STREAM
                elif configuration["socktype"] == "ext://socket.SOCK_DGRAM":
                    configuration["socktype"] = socket.SOCK_DGRAM

            _ = configuration.pop("enabled")
            formatter_name = configuration.pop("formatter")
            level = get_level(configuration.pop("level"))
            none_keys = []
            for key, value in configuration.items():
                if value is None:
                    none_keys.append(key)
            for x in none_keys:
                _ = configuration.pop(x)

            # Create handler, formatter, and add it
            handler = supported_handler_classes[handler_name](**configuration)
            formatter = supported_formatter_classes[formatter_name](
                **supported_formatter_kwargs[formatter_name]
            )
            handler.name = handler_name
            handler.setLevel(level)
            handler.setFormatter(formatter)
            if handler_name in handler_names:
                # Remove previously added handler
                logger.handlers = [x for x in logger_handlers if x.name != handler_name]
            logger.addHandler(handler)

            if "filename" in configuration:
                # filename is already used in log.x(extra)
                configuration["file_name"] = configuration["filename"]
                del configuration["filename"]
            logger.debug(f"Logging handler added ({handler_name})", extra=configuration)


class Thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None

    def run(self):
        if self._target is None:
            return
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.result
