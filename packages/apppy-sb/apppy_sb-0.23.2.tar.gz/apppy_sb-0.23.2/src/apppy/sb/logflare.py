import json
import logging
import traceback
from dataclasses import dataclass
from typing import Any

import requests
from fastapi_lifespan_manager import LifespanManager
from pydantic import Field

from apppy.env import Env, EnvSettings
from apppy.logger import WithLogger
from apppy.logger.parser import LogRecordParser
from apppy.queues import Queue, QueueHandler


@dataclass
class LogflareRecord:
    """
    Dataclass which helps to translate between the native
    logging.LogRecord and the Logflare schema
    """

    fileline: str
    level: str
    message: str
    logger: str
    extra: dict[str, Any] | None = None
    state: dict[str, Any] | None = None
    traceback: list[str] | None = None

    def to_logflare_json(self) -> str:
        logflare_dict: dict[str, Any] = {
            "message": self.message,
            "metadata": {
                "extra": self.extra,
                "fileline": self.fileline,
                "level": self.level,
                "logger": self.logger,
                "traceback": self.traceback,
            },
        }

        logflare_metadata = logflare_dict["metadata"]
        if self.state is not None:
            for key, value in self.state.items():
                logflare_metadata[key] = value  # type: ignore[index]

        return json.dumps(logflare_dict)

    @classmethod
    def from_log_record(cls, log_record: logging.LogRecord):
        logflare_record = cls(
            fileline=f"{log_record.pathname}/{log_record.filename}:{log_record.lineno}",
            level=log_record.levelname,
            logger=log_record.name,
            message=log_record.getMessage(),
        )

        state_info = LogRecordParser.get_global().parse_state_info(log_record)
        if state_info:
            logflare_record.state = state_info

        extra_info = LogRecordParser.get_global().parse_extra_info(log_record)
        if extra_info:
            logflare_record.extra = extra_info

        if log_record.levelno > logging.INFO and log_record.exc_info:
            exc_type, exc_value, exc_tb = log_record.exc_info
            traceback_flat = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logflare_record.traceback = traceback_flat.splitlines()

        return logflare_record


class LogflareClientSettings(EnvSettings):
    # LOGFLARE_LOGGING_API_KEY
    api_key: str = Field(exclude=True)
    # LOGFLARE_LOGGING_API_URL
    api_url: str = Field()
    # LOGFLARE_LOGGING_API_TIMEOUT
    api_timeout: int = Field(default=2)
    # LOGFLARE_LOGGING_QUEUE_MAX_SIZE
    queue_max_size: int = Field(default=1000)
    # LOGFLARE_LOGGING_QUEUE_SHUTDOWN_TIMEOUT"
    queue_shutdown_timeout: int = Field(default=2)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="LOGFLARE_LOGGING")


class LogflareClient(WithLogger):
    def __init__(
        self, env: Env, settings: LogflareClientSettings, lifespan: LifespanManager
    ) -> None:
        self._application_logs_source_name: str | None = None
        # For tests, we're not going to attempt to configure
        # a logging source. Only for legit environments (e.g.
        # local, staging, production, etc).
        if not env.is_ci and not env.is_test:
            self._application_logs_source_name = f"application.logs.{env.name}"

        self._headers = {"Content-Type": "application/json"}
        self._settings: LogflareClientSettings = settings
        lifespan.add(self._configure_application_logs_source)

    async def _configure_application_logs_source(self):
        application_logs_source = None
        if self._application_logs_source_name is not None:
            for source in self.list_sources():
                if source["name"] == self._application_logs_source_name:
                    application_logs_source = source
                    break

            # Create the application logs source if we cannot
            # find the name already in Logflare
            if application_logs_source is None:
                application_logs_source = self.create_source(self._application_logs_source_name)

        yield {"application_logs_source": application_logs_source}

    def create_source(self, source_name: str) -> dict[Any, Any]:
        resp = requests.post(
            f"{self._settings.api_url}/api/sources?api_key={self._settings.api_key}",
            headers=self._headers,
            data=json.dumps({"name": source_name}),
            timeout=self._settings.api_timeout,
        )

        return resp.json()

    async def emit_application_log(self, record: LogflareRecord) -> None:
        # In some select cases (e.g. tests), there is no
        # application logs source so we'll just skip it.
        #
        # NOTE: We need to be careful here that this is
        # set correctly for legitimate cases or else logging
        # may silently fail.
        if self._application_logs_source_name is None:
            return None

        await self._emit_log(self._application_logs_source_name, record)

    async def _emit_log(self, source_name: str, record: LogflareRecord) -> None:
        requests.post(
            f"{self._settings.api_url}/api/logs?source_name={source_name}&api_key={self._settings.api_key}",
            headers=self._headers,
            data=record.to_logflare_json(),
            timeout=self._settings.api_timeout,
        )

    def list_sources(self) -> list[dict]:
        resp = requests.get(
            f"{self._settings.api_url}/api/sources?api_key={self._settings.api_key}",
            headers=self._headers,
            timeout=self._settings.api_timeout,
        )

        return resp.json()


class LogflareLoggingHandler(logging.Handler, QueueHandler, WithLogger):
    def __init__(
        self,
        logflare_client: LogflareClient,
        logflare_queue: Queue,
    ) -> None:
        super().__init__(level=logging.root.level)
        self._logflare_client = logflare_client
        self._logflare_queue = logflare_queue
        self._logflare_queue.register_handler(self)

    def addTo(self, logger: logging.Logger) -> None:
        # This is an interesting case. The logflare client
        # uses urllib3 under the covers. If the log level
        # is turned up too high on this particular logger
        # and we've added the logflare handler, we get into
        # an infinite loop:
        #
        # 1. Emit a log line with urllib3
        # 2. The urllib3 library creates debugging logs
        # 3. The urllib3 debugging logs are in turn
        #    emitted with urllib3 (i.e. back to #1)
        #
        # So here, we'll make sure that we never attach the
        # logflare handler to urllib3 logs
        #
        # Also, as a safety measure, we'll skip Logflare specifically
        # for loggers in this module as well as the queue module to
        # preent possible infinite loops.
        if (
            logger.name == "urllib3.connectionpool"
            or logger.name.startswith("application.logger")
            or logger.name.startswith("application.queue")
        ):
            logger.setLevel(logging.INFO)
            return

        logger.addHandler(self)

    def addToAll(self) -> None:
        logger_dict = logging.Logger.manager.loggerDict
        for logger_name in logger_dict:
            logger = logger_dict.get(logger_name)
            if isinstance(logger, logging.Logger):
                self.addTo(logger)

    def emit(self, record: logging.LogRecord) -> None:
        logflare_record = LogflareRecord.from_log_record(record)
        self._logflare_queue.publish(logflare_record)

    async def handle_exception(self, message: LogflareRecord, exception: BaseException):
        self._logger.error(
            "Failed to emit log to Logflare", extra={"record": message}, exc_info=exception
        )

    async def handle_message(self, message: LogflareRecord):
        await self._logflare_client.emit_application_log(message)
