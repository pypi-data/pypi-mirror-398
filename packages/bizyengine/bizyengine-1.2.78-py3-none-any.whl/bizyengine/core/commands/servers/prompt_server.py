import hashlib
import json
import pprint
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List

import comfy
import requests

from bizyengine.core.commands.base import Command, Processor  # type: ignore
from bizyengine.core.common import client
from bizyengine.core.common.caching import BizyAirTaskCache, CacheConfig
from bizyengine.core.common.client import headers, send_request
from bizyengine.core.common.env_var import (
    BIZYAIR_DEBUG,
    BIZYAIR_DEV_GET_TASK_RESULT_SERVER,
    BIZYAIR_SERVER_ADDRESS,
)
from bizyengine.core.common.utils import truncate_long_strings
from bizyengine.core.configs.conf import config_manager
from bizyengine.core.image_utils import decode_data, encode_data


def get_task_result(task_id: str, offset: int = 0, api_key: str = None) -> dict:
    """
    Get the result of a task.
    """
    import requests

    task_api = config_manager.get_task_api()
    if BIZYAIR_DEV_GET_TASK_RESULT_SERVER:
        url = f"{BIZYAIR_DEV_GET_TASK_RESULT_SERVER}{task_api.task_result_endpoint}/{task_id}"
    else:
        url = f"{BIZYAIR_SERVER_ADDRESS}{task_api.task_result_endpoint}/{task_id}"

    if BIZYAIR_DEBUG:
        print(f"Debug: get task result url: {url}")
    _headers = headers(api_key=api_key)
    response_json = send_request(
        method="GET",
        url=url,
        data=json.dumps({"offset": offset}).encode("utf-8"),
        headers=_headers,
    )
    out = response_json
    events = out.get("data", {}).get("events", [])
    new_events = []
    for event in events:
        if (
            "data" in event
            and isinstance(event["data"], str)
            and event["data"].startswith("https://")
        ):
            # event["data"] = requests.get(event["data"]).json()
            event["data"] = send_request(
                method="GET", url=event["data"], headers=_headers
            )
        new_events.append(event)
    out["data"]["events"] = new_events
    return out


@dataclass
class BizyAirTask:
    TASK_DATA_STATUS = ["PENDING", "PROCESSING", "COMPLETED"]
    task_id: str
    data_pool: list[dict] = field(default_factory=list)
    data_status: str = None
    api_key: str = None

    @staticmethod
    def check_inputs(inputs: dict) -> bool:
        return (
            inputs.get("code") == 20000
            and inputs.get("status", False)
            and "task_id" in inputs.get("data", {})
        )

    @classmethod
    def from_data(
        cls, inputs: dict, check_inputs: bool = True, **kwargs
    ) -> "BizyAirTask":
        if check_inputs and not cls.check_inputs(inputs):
            raise ValueError(f"Invalid inputs: {inputs}")
        data = inputs.get("data", {})
        task_id = data.get("task_id", "")
        return cls(
            task_id=task_id,
            data_pool=[],
            data_status="started",
            api_key=kwargs["api_key"],
        )

    def is_finished(self) -> bool:
        if not self.data_pool:
            return False
        if self.data_pool[-1].get("data_status") == self.TASK_DATA_STATUS[-1]:
            return True
        return False

    def send_request(self, offset: int = 0) -> dict:
        if offset >= len(self.data_pool):
            return get_task_result(self.task_id, offset, self.api_key)
        else:
            return self.data_pool[offset]

    def get_data(self, offset: int = 0) -> dict:
        if offset >= len(self.data_pool):
            return {}
        return self.data_pool[offset]

    @staticmethod
    def _fetch_remote_data(url: str) -> dict:
        import requests

        return requests.get(url).json()

    def get_last_data(self) -> dict:
        return self.get_data(len(self.data_pool) - 1)

    def do_task_until_completed(
        self, *, timeout: int = 3600, poll_interval: float = 1
    ) -> list[dict]:
        offset = 0
        start_time = time.time()
        pbar = None
        while not self.is_finished():
            try:
                data = self.send_request(offset)
                data_lst = self._extract_data_list(data)
                self.data_pool.extend(data_lst)
                offset += len(data_lst)
                for data in data_lst:
                    message = data.get("data", {}).get("message", {})
                    if (
                        isinstance(message, dict)
                        and message.get("event", None) == "progress"
                    ):
                        value = message["data"]["value"]
                        total = message["data"]["max"]
                        if pbar is None:
                            pbar = comfy.utils.ProgressBar(total)
                        pbar.update_absolute(value + 1, total, None)
            except Exception as e:
                print(f"Exception: {e}")

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for task {self.task_id} to finish")

            time.sleep(poll_interval)

        return self.data_pool

    def _extract_data_list(self, data):
        data_lst = data.get("data", {}).get("events", [])
        if not data_lst:
            raise ValueError(f"No data found in task {self.task_id}")
        return data_lst


class PromptServer(Command):
    MAX_POLLING_TIME = 60 * 60
    POLLING_INTERVAL = 10

    cache_manager: BizyAirTaskCache = BizyAirTaskCache(
        config=CacheConfig.from_config(config_manager.get_cache_config())
    )

    def __init__(self, router: Processor, processor: Processor):
        self.router = router
        self.processor = processor

    def get_task_id(self, result: Dict[str, Any]) -> str:
        return result.get("data", {}).get("task_id", "")

    def is_async_task(self, result: Dict[str, Any]) -> str:
        """Determine if the result indicates an asynchronous task."""
        return (
            result.get("code") == 20000
            and result.get("status", False)
            and "task_id" in result.get("data", {})
        )

    def is_fass_task(self, result: Dict[str, Any]) -> bool:
        return (
            result.get("request_id", None) is not None
            and result.get("query_url", None) is not None
        )

    def _get_fass_result(self, result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        request_id = result.get("request_id", None)
        query_url = f"{BIZYAIR_SERVER_ADDRESS}/supernode/status?request_id={request_id}"
        return self._poll_fass_for_completion(query_url, **kwargs)

    def _poll_fass_for_completion(self, query_url, **kwargs):
        start_time = time.time()
        headers = client.headers(api_key=kwargs.get("api_key", None))
        task_failed, failed_reason = False, None
        while time.time() - start_time < self.MAX_POLLING_TIME and not task_failed:
            try:
                resp_body = client.send_request(
                    method="GET", url=query_url, headers=headers
                )
                data = resp_body.get("data", {})
                if data.get("status") == "Succeed":
                    result_url = data["data_url"]
                    result_resp = requests.get(result_url)
                    out = result_resp.json()
                    return out
                elif data.get("status") == "Failed":
                    task_failed, failed_reason = True, f"Task failed: {data}"
                    raise RuntimeError(f"Task failed: {data}")
                time.sleep(self.POLLING_INTERVAL)
            except Exception as e:
                if BIZYAIR_DEBUG:
                    print(f"Response error: {e}\n{traceback.format_exc()}")
                time.sleep(self.POLLING_INTERVAL)

        if task_failed:
            raise RuntimeError(f"Task failed: {failed_reason}")
        raise TimeoutError("Task processing timeout")

    def _get_result(self, result: Dict[str, Any], *, cache_key: str = None, **kwargs):
        try:
            if self.is_fass_task(result):
                self.cache_manager.set(cache_key, result)
                result = self._get_fass_result(result, **kwargs)
                result = result.get("data", {}).get("payload", None)
                assert result is not None, "Output payload should not be None"
                self.cache_manager.set(cache_key, result, overwrite=True)
                return result

            response_data = result["data"]
            if BizyAirTask.check_inputs(result):
                self.cache_manager.set(cache_key, result)
                bz_task = BizyAirTask.from_data(result, check_inputs=False, **kwargs)
                bz_task.do_task_until_completed(timeout=60 * 60)  # 60 minutes
                last_data = bz_task.get_last_data()
                response_data = last_data.get("data")
            out = response_data["payload"]
            assert out is not None, "Output payload should not be None"
            self.cache_manager.set(cache_key, out, overwrite=True)
            return out
        except Exception as e:
            self.cache_manager.delete(cache_key)
            raise RuntimeError(f"Exception: {e}, response_data: {response_data}") from e

    def execute(
        self,
        prompt: Dict[str, Dict[str, Any]],
        last_node_ids: List[str],
        *args,
        **kwargs,
    ):
        prompt = encode_data(prompt)

        if BIZYAIR_DEBUG:
            debug_info = {
                "prompt": truncate_long_strings(prompt, 50),
                "last_node_ids": last_node_ids,
            }
            pprint.pprint(debug_info, indent=4)

        url = self.router(prompt=prompt, last_node_ids=last_node_ids, **kwargs)

        if BIZYAIR_DEBUG:
            print(f"Generated URL: {url}")

        start_time = time.time()
        sh256 = hashlib.sha256(
            json.dumps({"url": url, "prompt": prompt}).encode("utf-8")
        ).hexdigest()
        end_time = time.time()
        if BIZYAIR_DEBUG:
            print(
                f"Time taken to generate sh256-{sh256}: {end_time - start_time} seconds"
            )

        cached_output = self.cache_manager.get(sh256)
        if cached_output:
            if BIZYAIR_DEBUG:
                print(f"Cache hit for sh256-{sh256}")
            out = cached_output
        else:
            result = self.processor(
                url, prompt=prompt, last_node_ids=last_node_ids, **kwargs
            )
            out = self._get_result(result, cache_key=sh256, **kwargs)

        if BIZYAIR_DEBUG:
            pprint.pprint({"out": truncate_long_strings(out, 50)}, indent=4)

        try:
            real_out = decode_data(out)
            out_lst = []
            for x in real_out:
                if (
                    x is None
                ):  # ref: https://github.com/siliconflow/comfybridge/blob/ecf2e835d4db9816514078f9eed98ab8ba12e23e/custom_plugins/comfy_pipeline/executor.py#L75-L78
                    out_lst.append(None)
                else:
                    # ref: https://github.com/comfyanonymous/ComfyUI/blob/c170fd2db598a0bdce56f80e22e83e10ad731421/execution.py#L312
                    out_lst.append(x[0])
            return out_lst
        except Exception as e:
            print("Exception occurred while decoding data")
            self.cache_manager.delete(sh256)
            traceback.print_exc()
            raise RuntimeError(f"Exception: {e=}") from e
