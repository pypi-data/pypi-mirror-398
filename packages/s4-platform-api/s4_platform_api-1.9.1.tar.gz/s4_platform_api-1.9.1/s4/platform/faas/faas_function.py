# Copyright 2023 Semaphore Solutions
# ---------------------------------------------------------------------------
import abc
import gzip
import json
import logging
import os
import base64
import sys

import ddtrace
import ddtrace.auto
import pyjson5
import requests
from pythonjsonlogger import jsonlogger  # type: ignore
from s4.platform.api import Api
from s4.platform.connection import Connection
from s4.platform.faas.custom_errors import ClientError
from s4.platform.faas.faas_utils import FaasUtils
from s4.platform.prospective_task.prospective_task import ProspectiveTaskSchema, ProspectiveTask
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class FaasFunction:
    @staticmethod
    def get_prospective_task(api: Api, input_file_content: str) -> ProspectiveTask:
        prospective_task_id = pyjson5.loads(input_file_content)["taskId"]
        return api.prospective_task_by_id(prospective_task_id)

    @staticmethod
    def pt_to_string(prospective_task: ProspectiveTask) -> str:
        schema = ProspectiveTaskSchema()
        return schema.dumps(prospective_task)

    @abc.abstractmethod
    def main(self, api: Api, input_file_content: str) -> str:
        pass

    # Nomad entrypoint
    def execute(self) -> int:
        working_dir = FaasUtils.get_env_var("NOMAD_TASK_DIR")

        input_file_name = FaasUtils.get_env_var("INPUT_FILE_NAME", "input.gz")
        input_file_path = os.path.join(working_dir, input_file_name)
        data = self._get_file_content(input_file_path)
        
        posix_status, result = self._execute_with_data(data)

        self._write_function_output(result, working_dir)

        self._notify_faas()

        return posix_status

    # Lambda entrypoint
    def get_lambda_handler(self):
        def handler(event: Dict[str, Any], context: Any):
            encoded_data = event.get("data", "").encode("utf-8")
            data_bytes = base64.b64decode(encoded_data)
            data = data_bytes.decode("utf-8")

            for key, val in event.get("environment", {}).items():
                if val is not None:
                    os.environ[key] = val

            for secret in event.get("secrets", {}).values():
                if secret is not None:
                    for key, val in secret.items():
                        if val is not None:
                            os.environ[key] = val

            posix_status, result = self._execute_with_data(data)

            if posix_status == 0:
                status_code = 200
            elif posix_status == 1:
                status_code = 400
            else:
                status_code = 500

            result_bytes = result.encode("utf-8")
            encoded_result = base64.b64encode(result_bytes)
            content = encoded_result.decode("utf-8")

            content_type = "application/json"
            try:
                json.loads(result)
            except ValueError:
                content_type = "text/plain"

            complete_data = {
                "output": {
                    "content": content,
                    "content_type": content_type,
                    "status": status_code
                }
            }
            complete_base_url = FaasUtils.get_env_var("COMPLETE_URL", FaasUtils.get_env_var("GATEWAY_URL"))
            execution_id = FaasUtils.get_env_var("EXECUTION_ID")
            complete_url = f"{complete_base_url}/executions/{execution_id}/complete"

            self._notify_faas(complete_data, complete_url)

            return {
                "statusCode": status_code,
                "message": "Function completed successfully!" if status_code == 200 else result
            }

        return handler

    def _execute_with_data(self, data: str) -> (int, str):
        try:
            self._configure_logging()
            self._activate_tracing()

            gateway_url = FaasUtils.get_env_var("GATEWAY_URL", "http://localhost:8080")
            environment_name = FaasUtils.get_env_var("ENVIRONMENT_NAME")
            auth_bearer_token = FaasUtils.get_env_var("AUTH_BEARER_TOKEN")

            connection = Connection(uri=gateway_url, access_token=auth_bearer_token, environment_name=environment_name)
            api = Api(connection)

            log.info("Starting function")

            result = self.main(api, data)

            return 0, result
        except ClientError as e:
            log.error(e, exc_info=True)

            return 1, str(e)
        except Exception as e:
            log.error(e, exc_info=True)

            return 101, str(e)
    
    @staticmethod
    def _get_file_content(file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError("This function expects a file to be provided at path: %s", file_path)

        if file_path.endswith(".gz"):
            with gzip.open(file_path, mode="rb") as zf:
                log.info("The provided file is an archive. It will be unzipped. %s", file_path)
                file_content = zf.read().decode("utf-8-sig")
        else:
            with open(file_path, mode="r", encoding="utf-8-sig") as f:
                file_content = f.read()

        return file_content

    @staticmethod
    def _configure_logging() -> None:
        logging.addLevelName(logging.NOTSET, "TRACE")

        log_level = FaasUtils.get_env_var("LOG_LEVEL", "INFO")
        json_formatter = jsonlogger.JsonFormatter(timestamp=True)

        logging_handler_out = logging.StreamHandler(sys.stdout)
        logging_handler_out.setFormatter(json_formatter)
        logging_handler_out.setLevel(logging.getLevelName(log_level))

        logging_handler_err = logging.StreamHandler(sys.stderr)
        logging_handler_err.setFormatter(json_formatter)
        logging_handler_err.setLevel(logging.ERROR)

        logging.basicConfig(level=log_level, handlers=[logging_handler_out, logging_handler_err], force=True)

    @staticmethod
    def _write_function_output(output: str, working_dir: str) -> None:
        with open(os.path.join(working_dir, "output.json"), "w", encoding="UTF-8") as f:
            f.write(output)

    @staticmethod
    def _activate_tracing() -> None:
        trace_id = FaasUtils.get_env_var("DATADOG_TRACE_ID", default_value="None")
        parent_id = FaasUtils.get_env_var("DATADOG_PARENT_ID", default_value="None")
        sampling_priority = FaasUtils.get_env_var("DATADOG_SAMPLING_PRIORITY", default_value="1")

        if trace_id != "None" and parent_id != "None":

            context = ddtrace.trace.Context(
                trace_id=int(trace_id),
                span_id=int(parent_id),
                sampling_priority=float(sampling_priority)
            )
            # And then configure it with
            ddtrace.tracer.context_provider.activate(context)
            ddtrace.tracer.trace("function-invoke")

    @staticmethod
    def _notify_faas(complete_data: Optional[dict[str, Any]] = None, complete_url: Optional[str] = None) -> None:
        auth_bearer_token = FaasUtils.get_env_var("AUTH_BEARER_TOKEN", hide_value=True)
        environment = FaasUtils.get_env_var("ENVIRONMENT_NAME")
        headers = {
            "Authorization": "Bearer " + auth_bearer_token,
            "x-s4-env": environment
        }

        if not complete_url:
            complete_url = FaasUtils.get_env_var("COMPLETE_URL")

        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)

        response = http.post(complete_url, json=complete_data, headers=headers)
        log.info(f"Complete signal response status: {response.status_code}")
