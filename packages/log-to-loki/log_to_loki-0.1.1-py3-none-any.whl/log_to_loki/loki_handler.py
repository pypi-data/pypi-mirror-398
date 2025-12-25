import logging
import json
import requests
import time
import inspect
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import sys
import threading
from queue import Queue, Empty


class LokiHandler(logging.Handler):
    """
    Кастомный handler для отправки логов в Grafana Loki
    """

    def __init__(
        self,
        loki_url: str,
        username: str,
        password: str,
        labels: Optional[Dict[str, str]] = None,
        batch_size: int = 10,
        flush_interval: int = 5,
    ):
        super().__init__()

        self.loki_url = loki_url.rstrip("/")
        self.push_url = urljoin(self.loki_url + "/", "loki/api/v1/push")
        self.username = username
        self.password = password
        self.labels = labels or {}
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self.log_queue = Queue()

        self.batch_thread = threading.Thread(
            target=self._batch_worker,
            daemon=True,
        )
        self.batch_thread.start()

        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Scope-OrgID": "tenant1",
            }
        )

    def emit(self, record):
        """
        Отправка лог записи в очередь для батчинга
        """
        try:
            caller_info = self._get_real_caller()

            log_entry = {
                "timestamp": str(time.time_ns()),
                "logmsg": record.getMessage(),
                "loglevel": record.levelname.lower(),
                "logger": record.name,
                "function": caller_info["function"],
                "line": caller_info["line"],
                "file": caller_info["file"],
            }

            self.log_queue.put(log_entry)

        except Exception:
            self.handleError(record)

    def _get_real_caller(self) -> Dict[str, Any]:
        frame = inspect.currentframe()
        try:
            while frame:
                frame = frame.f_back
                if not frame:
                    break

                filename = frame.f_code.co_filename
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno

                if (
                    "logging" in filename.lower()
                    or function_name
                    in {
                        "_log",
                        "info",
                        "debug",
                        "warning",
                        "error",
                        "critical",
                        "emit",
                        "_get_real_caller",
                        "format",
                        "_batch_worker",
                        "_send_batch",
                    }
                ):
                    continue

                if function_name == "<module>":
                    module_name = filename.split("/")[-1].split("\\")[-1]
                    function_name = module_name.replace(".py", "") + "_module"

                return {
                    "function": function_name,
                    "line": line_number,
                    "file": filename.split("/")[-1].split("\\")[-1],
                }

            return {"function": "unknown", "line": 0, "file": "unknown"}

        finally:
            del frame

    def _batch_worker(self):
        batch = []
        last_flush = time.time()

        while True:
            try:
                try:
                    log_entry = self.log_queue.get(timeout=1.0)
                    batch.append(log_entry)
                except Empty:
                    pass

                now = time.time()

                if batch and (
                    len(batch) >= self.batch_size
                    or now - last_flush >= self.flush_interval
                ):
                    self._send_batch(batch)
                    batch = []
                    last_flush = now

            except Exception as e:
                print(f"Ошибка в batch worker: {e}", file=sys.stderr)

    def _send_batch(self, batch):
        try:
            streams = {}

            base_labels = {
                "job": "python-app",
                **self.labels,
            }

            for entry in batch:
                labels = {
                    **base_labels,
                    "level": entry["loglevel"],
                    "logger": entry["logger"],
                }

                labels_key = "|".join(
                    f"{k}={v}" for k, v in sorted(labels.items())
                )

                if labels_key not in streams:
                    streams[labels_key] = {
                        "labels": labels,
                        "values": [],
                    }

                streams[labels_key]["values"].append(
                    [
                        entry["timestamp"],
                        json.dumps(entry, ensure_ascii=False),
                    ]
                )

            payload = {
                "streams": [
                    {
                        "stream": s["labels"],
                        "values": s["values"],
                    }
                    for s in streams.values()
                ]
            }

            response = self.session.post(
                self.push_url,
                data=json.dumps(payload, ensure_ascii=False),
                timeout=10,
            )

            if response.status_code not in (200, 204):
                print(
                    f"Ошибка отправки в Loki: {response.status_code} - {response.text}",
                    file=sys.stderr,
                )

        except Exception as e:
            print(f"Ошибка отправки батча в Loki: {e}", file=sys.stderr)

    def close(self):
        time.sleep(self.flush_interval + 1)
        self.session.close()
        super().close()


class LokiLogger:
    """
    Основной класс логгера с поддержкой Loki и консольного вывода
    """

    def __init__(
        self,
        name: str = "app",
        loki_url: str = None,
        username: str = None,
        password: str = None,
        level: int = logging.INFO,
        console_output: bool = True,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        self.logger.propagate = False

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(
                self._create_console_formatter()
            )
            self.logger.addHandler(console_handler)

        if loki_url and username and password:
            loki_handler = LokiHandler(
                loki_url=loki_url,
                username=username,
                password=password,
                labels=labels,
            )
            loki_handler.setLevel(level)
            loki_handler.setFormatter(formatter)
            self.logger.addHandler(loki_handler)

    def _create_console_formatter(self):
        class ConsoleFormatter(logging.Formatter):
            def format(self, record):
                frame = inspect.currentframe()
                try:
                    while frame:
                        frame = frame.f_back
                        if not frame:
                            break
                        if "logging" in frame.f_code.co_filename.lower():
                            continue

                        prefix = f"[{frame.f_code.co_name}:{frame.f_lineno}]"
                        record.msg = f"{prefix} {record.msg}"
                        break
                finally:
                    del frame

                return super().format(record)

        return ConsoleFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
