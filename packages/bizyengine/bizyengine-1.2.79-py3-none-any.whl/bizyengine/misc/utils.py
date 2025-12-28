import asyncio
import base64
import concurrent.futures
import errno
import json
import logging
import os
import pickle
import re
import threading
import time
import urllib.parse
import urllib.request
import zlib
from typing import Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

import numpy as np

from bizyengine.bizy_server.api_client import APIClient
from bizyengine.core import pop_api_key_and_prompt_id
from bizyengine.core.common import client
from bizyengine.core.common.env_var import BIZYAIR_SERVER_ADDRESS

BIZYAIR_DEBUG = os.getenv("BIZYAIR_DEBUG", False)


#
# TODO: Deprecated, delete this
def send_post_request(api_url, payload, headers):
    import warnings

    warnings.warn(message=f"send_post_request is deprecated")
    """
    Sends a POST request to the specified API URL with the given payload and headers.

    Args:
        api_url (str): The URL of the API endpoint.
        payload (dict): The payload to send in the POST request.
        headers (dict): The headers to include in the POST request.

    Raises:
        Exception: If there is an error connecting to the server or the request fails.
    """
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=3600) as response:
            response_data = response.read().decode("utf-8")
        return response_data
    except urllib.error.URLError as e:
        if "Unauthorized" in str(e):
            raise Exception(
                "Key is invalid, please refer to https://cloud.siliconflow.cn to get the API key.\n"
                "If you have the key, please click the 'BizyAir Key' button at the bottom right to set the key."
            )
        else:
            raise Exception(
                f"Failed to connect to the server: {e}, if you have no key, "
            )


def serialize_and_encode(obj: Union[np.ndarray], compress=True) -> Tuple[str, bool]:
    """
    Serializes a Python object, optionally compresses it, and then encodes it in base64.

    Args:
        obj: The Python object to serialize.
        compress (bool): Whether to compress the serialized object using zlib. Default is True.

    Returns:
        str: The base64 encoded string of the serialized (and optionally compressed) object.
    """
    serialized_obj = pickle.dumps(obj)

    if compress:
        serialized_obj = zlib.compress(serialized_obj)

    if BIZYAIR_DEBUG:
        print(
            f"serialize_and_encode: size of bytes is {format_bytes(len(serialized_obj))}"
        )

    encoded_obj = base64.b64encode(serialized_obj).decode("utf-8")

    if BIZYAIR_DEBUG:
        print(
            f"serialize_and_encode: size of base64 text is {format_bytes(len(serialized_obj))}"
        )

    return (encoded_obj, compress)


def decode_and_deserialize(response_text) -> np.ndarray:
    if BIZYAIR_DEBUG:
        print(
            f"decode_and_deserialize: size of text is {format_bytes(len(response_text))}"
        )

    ret = json.loads(response_text)

    if "result" in ret:
        msg = json.loads(ret["result"])
    else:
        msg = ret
    if msg["type"] not in (
        "comfyair",
        "bizyair",
    ):  # DO NOT CHANGE THIS LINE: "comfyair" is the type from the server node
        # TODO: change both server and client "comfyair" to "bizyair"
        raise Exception(f"Unexpected response type: {msg}")

    data = msg["data"]

    tensor_bytes = base64.b64decode(data["payload"])
    if data.get("is_compress", None):
        tensor_bytes = zlib.decompress(tensor_bytes)

    if BIZYAIR_DEBUG:
        print(
            f"decode_and_deserialize: size of bytes is {format_bytes(len(tensor_bytes))}"
        )

    deserialized_object = pickle.loads(tensor_bytes)
    return deserialized_object


def format_bytes(num_bytes: int) -> str:
    """
    Converts a number of bytes to a human-readable string with units (B, KB, or MB).

    :param num_bytes: The number of bytes to convert.
    :return: A string representing the number of bytes in a human-readable format.
    """
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def get_llm_response(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    **kwargs,
):
    api_url = f"{BIZYAIR_SERVER_ADDRESS}/chat/completions"
    extra_data = pop_api_key_and_prompt_id(kwargs)
    headers = client.headers(api_key=extra_data["api_key"])

    # 如果model已不可用，选择第一个可用model
    if _MODELS_CACHE.get("llm_models") is None:
        cache_models(extra_data["api_key"])
    llm_models = _MODELS_CACHE.get("llm_models")
    if llm_models is None:
        logging.warning(f"No LLM models available, keeping the original model {model}")
    elif model not in llm_models:
        logging.warning(
            f"Model {model} is not available, using the first available model {llm_models[0]}"
        )
        model = llm_models[0]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 50,
        "stream": False,
        "n": 1,
    }
    if "prompt_id" in extra_data:
        payload["prompt_id"] = extra_data["prompt_id"]
    data = json.dumps(payload).encode("utf-8")

    response = client.send_request(
        url=api_url,
        data=data,
        headers=headers,
        callback=None,
    )
    return response


def get_vlm_response(
    model: str,
    system_prompt: str,
    user_prompt: str,
    base64_images: List[str],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    detail: str = "auto",
    **kwargs,
):
    api_url = f"{BIZYAIR_SERVER_ADDRESS}/chat/completions"
    extra_data = pop_api_key_and_prompt_id(kwargs)
    headers = client.headers(api_key=extra_data["api_key"])

    # 如果model已不可用，选择第一个可用model
    if _MODELS_CACHE.get("vlm_models") is None:
        cache_models(extra_data["api_key"])
    vlm_models = _MODELS_CACHE.get("vlm_models")
    if vlm_models is None:
        logging.warning(f"No VLM models available, keeping the original model {model}")
    elif model not in vlm_models:
        logging.warning(
            f"Model {model} is not available, using the first available model {vlm_models[0]}"
        )
        model = vlm_models[0]

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}],
        },  # 此方法皆适用于两种 VL 模型
        # {
        #     "role": "system",
        #     "content": system_prompt,
        # },  # role 为 "system" 的这种方式只适用于 QwenVL 系列模型,并不适用于 InternVL 系列模型
    ]

    user_content = []
    for base64_image in base64_images:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/webp;base64,{base64_image}",
                    "detail": detail,
                },
            }
        )
    user_content.append({"type": "text", "text": user_prompt})

    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 50,
        "stream": False,
        "n": 1,
    }
    if "prompt_id" in extra_data:
        payload["prompt_id"] = extra_data["prompt_id"]
    data = json.dumps(payload).encode("utf-8")

    response = client.send_request(
        url=api_url,
        headers=headers,
        data=data,
        callback=None,
    )
    return response


K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


class TTLCache(Generic[K, V]):
    """线程安全 TTL 内存缓存（仅依赖标准库）"""

    def __init__(self, ttl_sec: float):
        self.ttl = ttl_sec
        self._data: Dict[K, tuple[V, float]] = {}
        self._lock = threading.RLock()
        self._stop_evt = threading.Event()
        # 后台清扫线程
        self._cleaner = threading.Thread(target=self._cleanup, daemon=True)
        self._cleaner.start()

    # ---------- 公共 API ----------
    def set(self, key: K, value: V) -> None:
        """写入/刷新键值"""
        with self._lock:
            self._data[key] = (value, time.time() + self.ttl)

    def get(self, key: K) -> Optional[V]:
        """读取键值；不存在或已过期返回 None"""
        with self._lock:
            val, expire = self._data.get(key, (None, 0))
            if val is None or time.time() > expire:
                self._data.pop(key, None)
                return None
            return val

    def delete(self, key: K) -> None:
        """手动删除"""
        with self._lock:
            self._data.pop(key, None)

    def stop(self):
        """停止后台线程（程序退出前调用）"""
        self._stop_evt.set()
        self._cleaner.join(timeout=self.ttl + 1)

    # ---------- 内部 ----------
    def _cleanup(self):
        """周期清扫过期键"""
        while not self._stop_evt.wait(self.ttl / 2):
            with self._lock:
                now = time.time()
                for key, (_, expire) in list(self._data.items()):
                    if now > expire:
                        self._data.pop(key, None)


class SingleFlight(Generic[R]):
    """Python 版 singleflight.Group（线程安全）"""

    def __init__(self):
        self._lock = threading.Lock()
        self._call_map: dict[str, SingleFlight._Call[R]] = {}

    class _Call(Generic[R]):
        __slots__ = ("mu", "done", "result", "err", "waiters")

        def __init__(self):
            self.mu = threading.Lock()
            self.done = False
            self.result: Optional[R] = None
            self.err: Optional[BaseException] = None
            self.waiters = 0

    def do(
        self, key: str, fn: Callable[[], R]
    ) -> tuple[R, bool, Optional[BaseException]]:
        """
        返回值: (result, shared?, exception)
        shared=True 表示本次未真正执行 fn，复用了别人结果
        """
        with self._lock:
            call = self._call_map.get(key)
            if call is None:  # 我是第一个
                call = self._Call[R]()
                call.waiters = 1
                self._call_map[key] = call
                first = True
            else:  # 已有并发请求
                call.waiters += 1
                first = False

        if first:  # 只有第一个真正执行
            try:
                result = fn()
                with call.mu:
                    call.result = result
                    call.done = True
            except BaseException as e:
                with call.mu:
                    call.err = e
                    call.done = True
                raise
            finally:  # 把自己从 map 摘掉
                with self._lock:
                    if call.waiters == 0:
                        self._call_map.pop(key, None)
        else:  # 其它人阻塞等待
            with call.mu:
                while not call.done:
                    call.mu.wait()
        # 读取结果
        with call.mu:
            if call.err is not None:
                return call.result, not first, call.err
            return call.result, not first, None


_MODELS_CACHE = TTLCache[str, list[str]](ttl_sec=600)
_SF = SingleFlight[None]()


def cache_models(request_api_key: str):
    # TODO: 效果待验证，目前节点只会被ComfyUI串行执行，所以不会出现竞争
    # 重试最多五次
    max_retries = 5
    for i in range(max_retries):
        try:
            _, shared, e = _SF.do(
                "_cache_models", lambda: _cache_models(request_api_key)
            )
            if e is not None:
                raise e
            return
        except Exception:
            logging.error(f"Failed to cache models on try #{i+1}")
            if i < max_retries - 1:
                time.sleep(5)


def _cache_models(request_api_key: str):
    # ① 开一条新线程专门跑协程 - 应该不需要在prompt那层上锁，因为并发只有1
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        api_client = APIClient()
        all_models = pool.submit(
            asyncio.run, api_client.fetch_all_llm_models(request_api_key)
        ).result()
        if len(all_models) == 0:
            raise errno.NO_MODEL_FOUND
        llm_models = [
            model
            for model in all_models
            if not (re.search(r"\d+(\.\d+)?v", model.lower()) or "vl" in model.lower())
        ]
        vlm_models = [
            model
            for model in all_models
            if re.search(r"\d+(\.\d+)?v", model.lower()) or "vl" in model.lower()
        ]
        _MODELS_CACHE.set("llm_models", llm_models)
        _MODELS_CACHE.set("vlm_models", vlm_models)
