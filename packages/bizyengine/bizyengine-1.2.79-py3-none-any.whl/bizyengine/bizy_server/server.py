import asyncio
import errno
import json
import logging
import re
import threading
import time
import urllib.parse
import uuid

import aiohttp
import execution
from server import PromptServer

from bizyengine.bizybot.config import Config, LLMConfig, MCPServerConfig
from bizyengine.bizybot.coordinator import Coordinator
from bizyengine.core.common.env_var import BIZYAIR_DEBUG, BIZYAIR_SERVER_MODE

from .api_client import APIClient
from .errno import ErrorNo, errnos
from .error_handler import ErrorHandler
from .profile import user_profile
from .resp import ErrResponse, OKResponse
from .utils import (
    base_model_types,
    check_str_param,
    check_type,
    decrypt_apikey,
    is_string_valid,
    types,
    update_base_model_types,
)

API_PREFIX = "bizyair"
COMMUNITY_API = f"{API_PREFIX}/community"
MODEL_HOST_API = f"{API_PREFIX}/modelhost"
USER_API = f"{API_PREFIX}/user"
INVOICE_API = f"{API_PREFIX}/invoices"
MODEL_API = f"{API_PREFIX}/model"

BIZYAIR_DATA_DICT = {}
BIZYAIR_DATA_DICT_UPDATED_AT = 0.0

logging.basicConfig(level=logging.DEBUG)
# 禁用MCP与OpenAI使用的httpx等相关的DEBUG,INFO日志, 仅在BIZYAIR_DEBUG模式下启用
if not BIZYAIR_DEBUG:
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _get_request_api_key(request_headers):
    if BIZYAIR_SERVER_MODE:
        encrypted_api_key = request_headers.get("Authorization")
        if not encrypted_api_key:
            # 尝试从cookie中读取auth_token
            cookie_str = request_headers.get("Cookie")
            encrypted_api_key = _get_auth_token_from_cookie(cookie_str)
        return decrypt_apikey(encrypted_api_key)
    return None, None


def _get_api_key_from_cookie(cookie_str):
    if not cookie_str:
        return None
    cookies = cookie_str.split("; ")
    for cookie in cookies:
        if cookie.startswith("apiKey="):
            return cookie[7:]
    return None


def _get_auth_token_from_cookie(cookie_str):
    if not cookie_str:
        return None
    cookies = cookie_str.split(";")
    for cookie in cookies:
        cookie = cookie.strip()
        if cookie.startswith("auth_token="):
            return cookie[11:]
    return None


class BizyAirServer:
    def __init__(self):
        BizyAirServer.instance = self
        self.api_client = APIClient()
        self.error_handler = ErrorHandler()
        self.prompt_server = PromptServer.instance
        self.sockets = dict()
        self.loop = asyncio.get_event_loop()

        self.setup_routes()

    def setup_routes(self):
        # 以下路径不论本地模式还是服务器模式都要注册
        @self.prompt_server.routes.get(f"/{API_PREFIX}/server_mode")
        async def get_server_mode(request):
            return OKResponse({"server_mode": BIZYAIR_SERVER_MODE})

        @self.prompt_server.routes.get(f"/{API_PREFIX}/proxy_view")
        async def proxy_view(request):
            filename = request.rel_url.query.get("filename", "")
            if not filename:
                return aiohttp.web.Response(status=400, text="Missing filename")
            host = request.url.host
            port = request.url.port
            view_url = (
                f"http://{host}:{port}/view?filename={urllib.parse.quote(filename)}"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(view_url) as resp:
                    if resp.status != 200:
                        return aiohttp.web.Response(
                            status=resp.status, text="Failed to fetch image"
                        )
                    content = await resp.read()
                    content_type = resp.headers.get(
                        "Content-Type", "application/octet-stream"
                    )
                    return aiohttp.web.Response(body=content, content_type=content_type)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/model_types")
        async def list_model_types(request):
            return OKResponse(types())

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/base_model_types")
        async def list_base_model_types(request):
            return OKResponse(base_model_types())

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/datasets/query")
        async def query_my_datasets(request):
            current = int(request.rel_url.query.get("current", "1"))
            page_size = int(request.rel_url.query.get("page_size", "10"))
            keyword = None
            annotated = None
            if request.body_exists:
                json_data = await request.json()
                keyword = json_data["keyword"]
                annotated = json_data["annotated"]
            resp, err = None, None

            # 调用API查询数据集
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.query_datasets(
                current,
                page_size,
                keyword=keyword,
                annotated=annotated,
                request_api_key=request_api_key,
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(
            f"/{COMMUNITY_API}/datasets/{{dataset_id}}/detail"
        )
        async def get_dataset_detail(request):
            # 获取路径参数中的数据集ID
            dataset_id = int(request.match_info["dataset_id"])

            # 检查dataset_id是否合法
            if not dataset_id or dataset_id <= 0:
                return ErrResponse(errnos.INVALID_DATASET_ID)

            # 调用API获取数据集详情
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.get_dataset_detail(
                dataset_id, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/models/query")
        async def query_my_models(request):
            # 获取查询参数
            mode = request.rel_url.query.get("mode", "")
            if not mode or mode not in ["my", "my_fork", "publicity", "official"]:
                return ErrResponse(errnos.INVALID_QUERY_MODE)

            current = int(request.rel_url.query.get("current", "1"))
            page_size = int(request.rel_url.query.get("page_size", "10"))
            json_data = await request.json()
            keyword = json_data["keyword"]
            model_types = json_data.get("model_types", [])
            base_models = json_data.get("base_models", [])
            sort = json_data.get("sort", "")
            has_draft = json_data.get("has_draft", None)
            if has_draft is not None:
                has_draft = bool(has_draft)

            resp, err = None, None

            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            if mode in ["my", "my_fork"]:
                # 调用API查询模型
                resp, err = await self.api_client.query_models(
                    mode,
                    current,
                    page_size,
                    keyword=keyword,
                    model_types=model_types,
                    base_models=base_models,
                    sort=sort,
                    request_api_key=request_api_key,
                )
            elif mode == "publicity":
                # 调用API查询社区模型
                resp, err = await self.api_client.query_community_models(
                    current,
                    page_size,
                    keyword=keyword,
                    model_types=model_types,
                    base_models=base_models,
                    sort=sort,
                    has_draft=has_draft,
                    request_api_key=request_api_key,
                )
            elif mode == "official":
                resp, err = await self.api_client.query_official_models(
                    current,
                    page_size,
                    keyword=keyword,
                    model_types=model_types,
                    base_models=base_models,
                    sort=sort,
                    request_api_key=request_api_key,
                )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/models/{{model_id}}/detail")
        async def get_model_detail(request):
            # 获取路径参数中的模型ID
            model_id = int(request.match_info["model_id"])

            # 检查model_id是否合法
            if not model_id or model_id <= 0:
                return ErrResponse(errnos.INVALID_MODEL_ID)

            source = request.rel_url.query.get("source", "")

            # 调用API获取模型详情
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.get_model_detail(
                model_id, source, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.delete(f"/{COMMUNITY_API}/models/{{model_id}}")
        async def delete_model(request):
            # 获取路径参数中的模型ID
            model_id = int(request.match_info["model_id"])

            # 检查model_id是否合法
            if not model_id or model_id <= 0:
                return ErrResponse(errnos.INVALID_MODEL_ID)

            # 调用API删除模型
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.delete_bizy_model(
                model_id, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.put(f"/{COMMUNITY_API}/models/{{model_id}}")
        async def update_model(request):
            sid = request.rel_url.query.get("clientId", "")
            if not is_string_valid(sid):
                return ErrResponse(errnos.INVALID_CLIENT_ID)
            # 获取路径参数中的模型ID
            model_id = int(request.match_info["model_id"])

            # 检查model_id是否合法
            if not model_id or model_id <= 0:
                return ErrResponse(errnos.INVALID_MODEL_ID)

            # 获取请求体数据
            json_data = await request.json()

            # 校验name和type
            err = check_str_param(json_data, "name", errnos.INVALID_NAME)
            if err is not None:
                return err

            if "/" in json_data["name"]:
                return ErrResponse(errnos.INVALID_NAME)

            err = check_type(json_data)
            if err is not None:
                return err

            # 校验versions
            if "versions" not in json_data or not isinstance(
                json_data["versions"], list
            ):
                return ErrResponse(errnos.INVALID_VERSIONS)

            versions = json_data["versions"]
            version_names = set()

            for version in versions:
                # 检查version是否重复
                if version.get("version") in version_names:
                    return ErrResponse(errnos.DUPLICATE_VERSION)

                # 检查version字段是否合法
                if not is_string_valid(version.get("version")) or "/" in version.get(
                    "version"
                ):
                    return ErrResponse(errnos.INVALID_VERSION_NAME)

                version_names.add(version.get("version"))

                # 检查base_model, path和sign是否有值
                for field in ["base_model", "path", "sign"]:
                    if not is_string_valid(version.get(field)):
                        err = errnos.INVALID_VERSION_FIELD.copy()
                        err.set_message(err.get_message("en") + ": " + field, "en")
                        err.set_message(err.get_message("zh") + ": " + field, "zh")
                        return ErrResponse(err)

            # 调用API更新模型
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.update_model(
                model_id,
                json_data["name"],
                json_data["type"],
                versions,
                request_api_key=request_api_key,
            )
            if err:
                return ErrResponse(err)

            # 开启线程检查同步状态
            threading.Thread(
                target=self.check_sync_status,
                args=(resp["id"], resp["version_ids"]),
                daemon=True,
            ).start()

            return OKResponse(None)

        @self.prompt_server.routes.post(
            f"/{COMMUNITY_API}/models/fork/{{model_version_id}}"
        )
        async def fork_model_version(request):
            try:
                # 获取version_id参数
                version_id = request.match_info["model_version_id"]
                if not version_id:
                    return ErrResponse(errnos.INVALID_MODEL_VERSION_ID)

                # 调用API fork模型版本
                request_api_key, err = _get_request_api_key(request.headers)
                if err:
                    return ErrResponse(err)
                _, err = await self.api_client.fork_model_version(
                    version_id, request_api_key=request_api_key
                )
                if err:
                    return ErrResponse(err)

                return OKResponse(None)

            except Exception as e:
                print(f"\033[31m[BizyAir]\033[0m Fail to fork model version: {str(e)}")
                return ErrResponse(errnos.FORK_MODEL_VERSION)

        @self.prompt_server.routes.delete(
            f"/{COMMUNITY_API}/models/fork/{{model_version_id}}"
        )
        async def unfork_model_version(request):
            try:
                # 获取version_id参数
                version_id = request.match_info["model_version_id"]
                if not version_id:
                    return ErrResponse(errnos.INVALID_MODEL_VERSION_ID)

                # 调用API fork模型版本
                request_api_key, err = _get_request_api_key(request.headers)
                if err:
                    return ErrResponse(err)
                _, err = await self.api_client.unfork_model_version(
                    version_id, request_api_key=request_api_key
                )
                if err:
                    return ErrResponse(err)

                return OKResponse(None)

            except Exception as e:
                print(
                    f"\033[31m[BizyAir]\033[0m Fail to unfork model version: {str(e)}"
                )
                return ErrResponse(errnos.FORK_MODEL_VERSION)

        @self.prompt_server.routes.post(
            f"/{COMMUNITY_API}/models/like/{{model_version_id}}"
        )
        async def like_model_version(request):
            try:
                # 获取version_id参数
                version_id = request.match_info["model_version_id"]
                if not version_id:
                    return ErrResponse(errnos.INVALID_MODEL_VERSION_ID)

                # 调用API like模型版本
                request_api_key, err = _get_request_api_key(request.headers)
                if err:
                    return ErrResponse(err)
                _, err = await self.api_client.toggle_user_like(
                    "model_version", version_id, request_api_key=request_api_key
                )
                if err:
                    return ErrResponse(err)

                return OKResponse(None)

            except Exception as e:
                print(
                    f"\033[31m[BizyAir]\033[0m Fail to toggle like model version: {str(e)}"
                )
                return ErrResponse(errnos.TOGGLE_USER_LIKE)

        @self.prompt_server.routes.get(
            f"/{COMMUNITY_API}/models/versions/{{model_version_id}}/workflow_json/{{sign}}"
        )
        async def get_workflow_json(request):
            model_version_id = int(request.match_info["model_version_id"])
            # 检查model_version_id是否合法
            if not model_version_id or model_version_id <= 0:
                return ErrResponse(errnos.INVALID_MODEL_VERSION_ID)

            sign = str(request.match_info["sign"])
            if not sign:
                return ErrResponse(errnos.INVALID_SIGN)

            # 获取上传凭证
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            url, err = await self.api_client.get_download_url(
                sign=sign,
                model_version_id=model_version_id,
                request_api_key=request_api_key,
            )
            if err:
                return ErrResponse(err)

            # 请求该url，获取文件内容
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return ErrResponse(errnos.FAILED_TO_FETCH_WORKFLOW_JSON)
                    try:
                        # 先尝试直接解析JSON
                        json_content = await response.json()
                    except aiohttp.client_exceptions.ContentTypeError:
                        # 如果Content-Type不是application/json，则获取文本内容并手动解析
                        text_content = await response.text()
                        try:
                            json_content = json.loads(text_content)
                        except json.JSONDecodeError as e:
                            logging.error(f"Failed to parse JSON from response: {e}")
                            return ErrResponse(errnos.FAILED_TO_FETCH_WORKFLOW_JSON)

            return OKResponse(json_content)

        @self.prompt_server.routes.get(f"/{API_PREFIX}/dict")
        async def get_data_dict(request):
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)

            # 缓存一小时
            global BIZYAIR_DATA_DICT, BIZYAIR_DATA_DICT_UPDATED_AT
            if BIZYAIR_DATA_DICT_UPDATED_AT + 3600 > time.time():
                return OKResponse(BIZYAIR_DATA_DICT)

            data_dict, err = await self.api_client.get_data_dict(
                request_api_key=request_api_key
            )
            if err is not None:
                return ErrResponse(err)

            # Update base model types
            update_base_model_types(data_dict["base_models"])
            BIZYAIR_DATA_DICT = data_dict
            BIZYAIR_DATA_DICT_UPDATED_AT = time.time()

            return OKResponse(data_dict)

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/datasets")
        async def commit_dataset(request):
            sid = request.rel_url.query.get("clientId", "")
            if not is_string_valid(sid):
                return ErrResponse(errnos.INVALID_CLIENT_ID)

            json_data = await request.json()

            # 校验name和type
            err = check_str_param(json_data, "name", errnos.INVALID_DATASET_NAME)
            if err is not None:
                return err

            if "/" in json_data["name"]:
                return ErrResponse(errnos.INVALID_DATASET_NAME)

            # 校验versions
            if "versions" not in json_data or not isinstance(
                json_data["versions"], list
            ):
                return ErrResponse(errnos.INVALID_VERSIONS)

            versions = json_data["versions"]
            version_names = set()

            for version in versions:
                # 检查version是否重复
                if version.get("version") in version_names:
                    return ErrResponse(errnos.DUPLICATE_VERSION)

                # 检查version字段是否合法
                if not is_string_valid(version.get("version")) or "/" in version.get(
                    "version"
                ):
                    return ErrResponse(errnos.INVALID_DATASET_VERSION)

                version_names.add(version.get("version"))

            # 调用API提交数据集
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.commit_dataset(
                payload=json_data, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            # print("resp------------------------------->", json_data, resp)
            # 开启线程检查同步状态
            threading.Thread(
                target=self.check_dataset_sync_status,
                args=(resp["id"], resp["version_ids"], sid),
                daemon=True,
            ).start()

            # enable refresh for lora
            # TODO: enable refresh for other types
            # bizyengine.core.path_utils.path_manager.enable_refresh_options("loras")

            return OKResponse(resp)

        @self.prompt_server.routes.put(f"/{COMMUNITY_API}/datasets/{{dataset_id}}")
        async def update_dataset(request):
            sid = request.rel_url.query.get("clientId", "")
            if not is_string_valid(sid):
                return ErrResponse(errnos.INVALID_CLIENT_ID)
            # 获取路径参数中的数据集ID
            dataset_id = int(request.match_info["dataset_id"])

            # 检查model_id是否合法
            if not dataset_id or dataset_id <= 0:
                return ErrResponse(errnos.INVALID_DATASET_ID)

            # 获取请求体数据
            json_data = await request.json()

            # 校验name和type
            err = check_str_param(json_data, "name", errnos.INVALID_DATASET_NAME)
            if err is not None:
                return err

            if "/" in json_data["name"]:
                return ErrResponse(errnos.INVALID_DATASET_NAME)

            # 校验versions
            if "versions" not in json_data or not isinstance(
                json_data["versions"], list
            ):
                return ErrResponse(errnos.INVALID_VERSIONS)

            versions = json_data["versions"]
            version_names = set()

            for version in versions:
                # 检查version是否重复
                if version.get("version") in version_names:
                    return ErrResponse(errnos.DUPLICATE_VERSION)

                # 检查version字段是否合法
                if not is_string_valid(version.get("version")) or "/" in version.get(
                    "version"
                ):
                    return ErrResponse(errnos.INVALID_VERSION_NAME)

                version_names.add(version.get("version"))

            # 调用API更新数据集
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.update_dataset(
                dataset_id, json_data["name"], versions, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            # 开启线程检查同步状态
            threading.Thread(
                target=self.check_dataset_sync_status,
                args=(resp["id"], resp["version_ids"]),
                daemon=True,
            ).start()

            return OKResponse(None)

        @self.prompt_server.routes.delete(f"/{COMMUNITY_API}/datasets/{{dataset_id}}")
        async def delete_dataset(request):
            # 获取路径参数中的数据集ID
            dataset_id = int(request.match_info["dataset_id"])

            # 检查model_id是否合法
            if not dataset_id or dataset_id <= 0:
                return ErrResponse(errnos.INVALID_DATASET_ID)

            # 调用API删除数据集
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.delete_dataset(
                dataset_id, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/share")
        async def create_share(request):
            json_data = await request.json()
            if "biz_id" not in json_data:
                return ErrResponse(errnos.INVALID_SHARE_BIZ_ID)

            biz_id = int(json_data["biz_id"])
            if not biz_id or biz_id <= 0:
                return ErrResponse(errnos.INVALID_SHARE_BIZ_ID)

            if "type" not in json_data:
                return ErrResponse(errnos.INVALID_SHARE_TYPE)
            if not is_string_valid(json_data["type"]) or (
                json_data["type"] != "bizy_model_version"
            ):
                return ErrResponse(errnos.INVALID_SHARE_TYPE)

            # 调用API提交数据集
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.create_share(
                payload=json_data, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/model_version/{{version_id}}")
        async def get_model_version_detail(request):
            # 获取路径参数中的数据集ID
            version_id = int(request.match_info["version_id"])

            # 检查version_id是否合法
            if not version_id or version_id <= 0:
                return ErrResponse(errnos.INVALID_MODEL_VERSION_ID)

            # 调用API获取数据集详情
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            resp, err = await self.api_client.get_model_version_detail(
                version_id, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/sign")
        async def sign(request):
            sha256sum = request.rel_url.query.get("sha256sum")
            if not is_string_valid(sha256sum):
                return ErrResponse(errnos.EMPTY_SHA256SUM)

            type = request.rel_url.query.get("type")
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            sign_data, err = await self.api_client.sign(
                sha256sum, type, request_api_key=request_api_key
            )
            if err is not None:
                return ErrResponse(err)

            return OKResponse(sign_data)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/upload_token")
        async def upload_token(request):
            filename = request.rel_url.query.get("filename", "")
            # 校验filename
            if not is_string_valid(filename):
                return ErrResponse(errnos.INVALID_FILENAME)

            filename = urllib.parse.quote(filename)
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            token, err = await self.api_client.get_upload_token(
                filename=filename, request_api_key=request_api_key
            )
            if err is not None:
                return ErrResponse(err)
            return OKResponse(token)

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/commit_file")
        async def commit_file(request):
            json_data = await request.json()

            if "sha256sum" not in json_data:
                return ErrResponse(errnos.EMPTY_SHA256SUM)
            sha256sum = json_data.get("sha256sum")

            if "object_key" not in json_data:
                return ErrResponse(errnos.INVALID_OBJECT_KEY)
            object_key = json_data.get("object_key")

            if "type" not in json_data:
                return ErrResponse(errnos.INVALID_TYPE)
            type = json_data.get("type")

            md5_hash = ""
            if "md5_hash" in json_data:
                md5_hash = json_data.get("md5_hash")

            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            commit_data, err = await self.api_client.commit_file(
                signature=sha256sum,
                object_key=object_key,
                md5_hash=md5_hash,
                type=type,
                request_api_key=request_api_key,
            )
            # print("commit_data", commit_data)
            if err is not None:
                return ErrResponse(err)

            return OKResponse(None)

        # 由于历史原因，前端请求body里有apikey所以是post
        @self.prompt_server.routes.post(f"/{API_PREFIX}/get_silicon_cloud_llm_models")
        async def get_silicon_cloud_llm_models_endpoint(request):
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            all_models = await self.api_client.fetch_all_llm_models(
                request_api_key=request_api_key
            )
            llm_models = [
                model
                for model in all_models
                if not (
                    re.search(r"\d+(\.\d+)?v", model.lower()) or "vl" in model.lower()
                )
            ]
            llm_models.append("No LLM Enhancement")
            return aiohttp.web.json_response(llm_models)

        # 由于历史原因，前端请求body里有apikey所以是post
        @self.prompt_server.routes.post(f"/{API_PREFIX}/get_silicon_cloud_vlm_models")
        async def get_silicon_cloud_vlm_models_endpoint(request):
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            all_models = await self.api_client.fetch_all_llm_models(
                request_api_key=request_api_key
            )
            vlm_models = [
                model
                for model in all_models
                if re.search(r"\d+(\.\d+)?v", model.lower()) or "vl" in model.lower()
            ]
            vlm_models.append("No VLM Enhancement")
            return aiohttp.web.json_response(vlm_models)

        @self.prompt_server.routes.post(f"/{API_PREFIX}/validate_prompt")
        async def validate_prompt(request):
            json_data = await request.json()
            if not "prompt" in json_data:
                return ErrResponse(errnos.MISSING_PROMPT)

            valid = execution.validate_prompt(json_data["prompt"])
            if valid[0]:
                return OKResponse(None)
            else:
                err = errnos.INVALID_PROMPT.copy()
                err.data = {"error": valid[1], "node_errors": valid[3]}
                return ErrResponse(err)

        @self.prompt_server.routes.post(f"/{MODEL_API}/chat")
        async def chat(request):
            try:
                # 获取API密钥
                request_api_key, err = _get_request_api_key(request.headers)
                if err:
                    return ErrResponse(err)

                # 解析请求数据
                request_data = await request.json()

                # 提取参数
                current_message = request_data.get("message")
                conversation_history = request_data.get("conversation_history", [])
                model_config = request_data.get("model_config", {})

                # 验证输入
                if not current_message and not conversation_history:
                    return ErrResponse(errnos.MISSING_MESSAGE_OR_HISTORY)

                # 验证对话历史格式
                if conversation_history:
                    from bizyengine.bizybot.models import Conversation

                    if not Conversation.validate_conversation_history(
                        conversation_history
                    ):
                        return ErrResponse(errnos.INVALID_CONVERSATION_HISTORY)

                if request_api_key:
                    api_key = request_api_key
                if not BIZYAIR_SERVER_MODE:
                    from bizyengine.core.common.client import get_api_key

                    api_key = get_api_key()

                if not api_key:
                    return ErrResponse(errnos.INVALID_API_KEY)

                # 创建LLM配置
                llm_config = LLMConfig(api_key=api_key, timeout=30.0)
                config = Config(
                    llm=llm_config,
                    mcp_servers={
                        "bizyair-mcp": MCPServerConfig(
                            transport="streamable_http",
                            url="https://api.bizyair.cn/w/v1/mcp/32",
                            headers={
                                "Authorization": "Bearer " + api_key,
                                "X-BizyBot-Client": "bizybot",
                            },
                        ),
                        "bizyait-image-gen": MCPServerConfig(
                            transport="streamable_http",
                            url="https://api.bizyair.cn/w/v1/mcp/67",
                            headers={
                                "Authorization": "Bearer " + api_key,
                                "X-BizyBot-Client": "bizybot",
                            },
                        ),
                        "bizyait-image-edit": MCPServerConfig(
                            transport="streamable_http",
                            url="https://api.bizyair.cn/w/v1/mcp/68",
                            headers={
                                "Authorization": "Bearer " + api_key,
                                "X-BizyBot-Client": "bizybot",
                            },
                        ),
                    },
                )

                coordinator = Coordinator(config)
                try:
                    await coordinator.initialize()

                    response = aiohttp.web.StreamResponse(
                        status=200,
                        headers={
                            "Content-Type": "text/event-stream",
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                        },
                    )
                    await response.prepare(request)

                    try:
                        import uuid

                        temp_conversation_id = str(uuid.uuid4())
                        conversation_event = {
                            "type": "conversation_started",
                            "conversation_id": temp_conversation_id,
                        }
                        await response.write(
                            f"data: {json.dumps(conversation_event, ensure_ascii=False)}\n\n".encode(
                                "utf-8"
                            )
                        )

                        async for event in coordinator.process_message(
                            message=current_message,
                            conversation_history=conversation_history,
                            llm_config_override=model_config,
                        ):
                            formatted_event = coordinator.format_streaming_event(event)
                            await response.write(
                                f"data: {json.dumps(formatted_event, ensure_ascii=False)}\n\n".encode(
                                    "utf-8"
                                )
                            )

                        await response.write(b"data: [DONE]\n\n")
                    except Exception as e:
                        error_event = {"type": "error", "error": str(e)}
                        try:
                            await response.write(
                                f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n".encode(
                                    "utf-8"
                                )
                            )
                        except Exception:
                            pass

                    return response
                finally:
                    try:
                        await coordinator.cleanup()
                    except Exception:
                        logging.exception("Coordinator cleanup failed")

            except Exception as e:
                print(f"\033[31m[BizyAir]\033[0m Chat request failed: {str(e)}")
                return ErrResponse(errnos.MODEL_API_ERROR)

        @self.prompt_server.routes.post(f"/{API_PREFIX}/trd_api_pricing")
        async def trd_api_pricing(request):
            request_api_key, err = _get_request_api_key(request.headers)
            if err:
                return ErrResponse(err)
            model = request.rel_url.query.get("model", "")
            if not model:
                return ErrResponse(errnos.INVALID_MODEL_ID)
            data = {}
            if request.body_exists:
                data = await request.json()
            pricing, err = await self.api_client.trd_api_pricing(
                model=model, data=data, request_api_key=request_api_key
            )
            if err:
                return ErrResponse(err)
            return OKResponse(pricing)

        # 服务器模式独占
        if BIZYAIR_SERVER_MODE:
            return

        # 服务器模式下以下路径不会注册
        @self.prompt_server.routes.get(f"/{MODEL_HOST_API}" + "/{shareId}/models/files")
        async def list_share_model_files(request):
            shareId = request.match_info["shareId"]
            if not is_string_valid(shareId):
                return ErrResponse(errnos.INVALID_SHARE_ID)
            payload = {}
            query_params = ["type", "name", "ext_name"]
            for param in query_params:
                if param in request.rel_url.query and request.rel_url.query[param]:
                    payload[param] = request.rel_url.query[param]
            model_files, err = await self.api_client.get_share_model_files(
                shareId=shareId, payload=payload
            )
            if err is not None:
                return ErrResponse(err)
            return OKResponse(model_files)

        @self.prompt_server.routes.get(f"/{USER_API}/info")
        async def user_info(request):
            info, err = await self.api_client.user_info()
            if err is not None:
                return ErrResponse(err)

            return OKResponse(info)

        @self.prompt_server.routes.get(f"/{API_PREFIX}/ws")
        async def websocket_handler(request):
            ws = aiohttp.web.WebSocketResponse()
            await ws.prepare(request)
            sid = request.rel_url.query.get("clientId", "")
            if sid:
                # Reusing existing session, remove old
                self.sockets.pop(sid, None)
            else:
                sid = uuid.uuid4().hex

            self.sockets[sid] = ws

            try:
                # Send initial state to the new client
                await self.send_json(
                    event="status", data={"status": "connected"}, sid=sid
                )

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == "ping":
                            await ws.send_str("pong")
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        logging.warning(
                            "ws connection closed with exception %s" % ws.exception()
                        )
            finally:
                self.sockets.pop(sid, None)
            return ws

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/models")
        async def commit_bizy_model(request):
            sid = request.rel_url.query.get("clientId", "")
            if not is_string_valid(sid):
                return ErrResponse(errnos.INVALID_CLIENT_ID)

            json_data = await request.json()

            # 校验name和type
            err = check_str_param(json_data, "name", errnos.INVALID_NAME)
            if err is not None:
                return err

            if "/" in json_data["name"]:
                return ErrResponse(errnos.INVALID_NAME)

            err = check_type(json_data)
            if err is not None:
                return err

            # 校验versions
            if "versions" not in json_data or not isinstance(
                json_data["versions"], list
            ):
                return ErrResponse(errnos.INVALID_VERSIONS)

            versions = json_data["versions"]
            version_names = set()

            for version in versions:
                # 检查version是否重复
                if version.get("version") in version_names:
                    return ErrResponse(errnos.DUPLICATE_VERSION)

                # 检查version字段是否合法
                if not is_string_valid(version.get("version")) or "/" in version.get(
                    "version"
                ):
                    return ErrResponse(errnos.INVALID_VERSION_NAME)

                version_names.add(version.get("version"))

                # 检查base_model, path和sign是否有值
                for field in ["base_model", "path", "sign"]:
                    if not is_string_valid(version.get(field)):
                        err = errnos.INVALID_VERSION_FIELD.copy()
                        err.set_message(err.get_message("en") + ": " + field, "en")
                        err.set_message(err.get_message("zh") + ": " + field, "zh")
                        return ErrResponse(err)

            # 调用API提交模型
            resp, err = await self.api_client.commit_bizy_model(payload=json_data)
            if err:
                return ErrResponse(err)

            # print("resp------------------------------->", json_data, resp)
            # 开启线程检查同步状态
            threading.Thread(
                target=self.check_sync_status,
                args=(resp["id"], resp["version_ids"], sid),
                daemon=True,
            ).start()

            # enable refresh for lora
            # TODO: enable refresh for other types
            # bizyengine.core.path_utils.path_manager.enable_refresh_options("loras")

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/share/{{code}}")
        async def get_share_detail(request):
            # 获取路径参数中的数据集ID
            code = str(request.match_info["code"])

            # 检查code是否合法
            if not is_string_valid(code):
                return ErrResponse(errnos.INVALID_SHARE_CODE)

            # 调用API获取数据集详情
            resp, err = await self.api_client.get_share_detail(code)
            if err:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/notifications/unread_count")
        async def get_notification_unread_count(request):
            # 获取当前用户的未读消息数量
            resp, err = await self.api_client.get_notification_unread_count()
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{COMMUNITY_API}/notifications")
        async def fetch_notifications(request):
            # 获取当前用户的消息列表
            typesStr = request.rel_url.query.get("types", None)
            types = None
            if typesStr:
                types = [int(x) for x in typesStr.split(",")]
            read_status = request.rel_url.query.get("read_status", None)
            page_size = int(request.rel_url.query.get("page_size", "10"))
            last_pm_id = int(request.rel_url.query.get("last_pm_id", "0"))
            last_broadcast_id = int(request.rel_url.query.get("last_broadcast_id", "0"))

            resp, err = await self.api_client.fetch_notifications(
                page_size,
                last_pm_id,
                last_broadcast_id,
                types,
                read_status,
            )
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/notifications/read_all")
        async def read_all_notifications(request):
            # 将当前用户的所有未读消息标记为已读
            type = int(request.rel_url.query.get("type", "0"))
            resp, err = await self.api_client.read_all_notifications(type)
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{COMMUNITY_API}/notifications/read")
        async def read_notifications(request):
            # 将当前用户的未读消息标记为已读
            json_data = await request.json()
            if "ids" not in json_data:
                return ErrResponse(errnos.INVALID_NOTIF_ID)
            ids = json_data.get("ids")
            resp, err = await self.api_client.read_notifications(ids)
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{USER_API}/wallet")
        async def get_wallet(request):
            # 获取用户钱包信息
            resp, err = await self.api_client.get_wallet()
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{USER_API}/coins")
        async def query_coins(request):
            # 获取用户金币记录
            current = int(request.rel_url.query.get("current", "1"))
            page_size = int(request.rel_url.query.get("page_size", "10"))
            coin_type = int(request.rel_url.query.get("coin_type", "0"))
            expire_days = int(request.rel_url.query.get("expire_days", "0"))

            resp, err = await self.api_client.query_coins(
                current, page_size, coin_type, expire_days
            )
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{USER_API}/metadata")
        async def get_user_metadata(request):
            # 获取用户元数据
            resp, err = await self.api_client.get_user_metadata()
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.put(f"/{USER_API}/metadata")
        async def update_user_info(request):
            # 更新用户信息
            json_data = await request.json()
            name = json_data.get("name")
            avatar = json_data.get("avatar")
            introduction = json_data.get("introduction")

            resp, err = await self.api_client.update_user_info(
                name, avatar, introduction
            )
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{USER_API}/real_name")
        async def user_real_name(request):
            # 实名认证
            resp, err = await self.api_client.user_real_name()
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{USER_API}/language")
        async def get_user_profile(request):
            return OKResponse(user_profile.getLang())

        @self.prompt_server.routes.get(f"/{USER_API}/profile")
        async def get_user_profile(request):
            return OKResponse(user_profile.getAll())

        @self.prompt_server.routes.put(f"/{USER_API}/profile")
        async def update_user_profile(request):
            # 更新用户本地配置
            json_data = await request.json()

            err = user_profile.update_profile(json_data)
            if err is not None:
                return ErrResponse(err)
            return OKResponse({})

        @self.prompt_server.routes.get(f"/{USER_API}/products")
        async def list_products(request):
            # 获取产品列表
            resp, err = await self.api_client.list_products()
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{USER_API}/pay/page")
        async def list_pay_orders(request):
            # 获取订单列表
            current = int(request.rel_url.query.get("current", "1"))
            page_size = int(request.rel_url.query.get("page_size", "10"))
            status = request.rel_url.query.get("status", None)
            resp, err = await self.api_client.list_pay_orders(
                current, page_size, status
            )
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{USER_API}/buy")
        async def buy_product(request):
            # 购买商品
            json_data = await request.json()

            if "product_id" not in json_data:
                return ErrResponse(errnos.INVALID_PRODUCT_ID)
            product_id = json_data.get("product_id")

            if "platform" not in json_data:
                return ErrResponse(errnos.INVALID_PAY_PLATFORM)
            platform = json_data.get("platform")

            resp, err = await self.api_client.buy_product(product_id, platform)
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{USER_API}/pay/orders")
        async def list_pay_orders(request):
            # 获取支付订单状态
            order_no = request.rel_url.query.get("order_no", None)
            if order_no == None:
                return ErrResponse(errnos.INVALID_ORDER_NO)
            resp, err = await self.api_client.get_pay_status(order_no)
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.delete(f"/{USER_API}/pay/orders")
        async def cancel_pay_order(request):
            # 取消支付订单
            json_data = await request.json()
            if "order_no" not in json_data:
                return ErrResponse(errnos.INVALID_ORDER_NO)
            order_no = json_data.get("order_no")
            resp, err = await self.api_client.cancel_pay_order(order_no)
            if err:
                return ErrResponse(err)
            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{INVOICE_API}/year_cost")
        async def get_year_cost(request):
            year = request.rel_url.query.get("year", "")
            api_key = request.rel_url.query.get("api_key", "")

            if not year:
                return ErrResponse(errnos.INVALID_YEAR_PARAM)

            resp, err = await self.api_client.get_year_cost(
                year=year, query_api_key=api_key
            )
            if err is not None:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{INVOICE_API}/month_cost")
        async def get_month_cost(request):
            month = request.rel_url.query.get("month", "")
            api_key = request.rel_url.query.get("api_key", "")

            if not month:
                return ErrResponse(errnos.INVALID_MONTH_PARAM)

            resp, err = await self.api_client.get_month_cost(
                month=month, query_api_key=api_key
            )
            if err is not None:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{INVOICE_API}/day_cost")
        async def get_day_cost(request):
            day = request.rel_url.query.get("day", "")
            api_key = request.rel_url.query.get("api_key", "")

            if not day:
                return ErrResponse(errnos.INVALID_DAY_PARAM)

            resp, err = await self.api_client.get_day_cost(
                day=day, query_api_key=api_key
            )
            if err is not None:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.get(f"/{INVOICE_API}/recent_cost")
        async def get_recent_cost(request):

            api_key = request.rel_url.query.get("api_key", "")

            resp, err = await self.api_client.get_recent_cost(query_api_key=api_key)
            if err is not None:
                return ErrResponse(err)

            return OKResponse(resp)

        @self.prompt_server.routes.post(f"/{API_PREFIX}/auth/plugin_tmp_token")
        async def get_plugin_tmp_token(request):
            api_key = request.rel_url.query.get("api_key", "")

            resp, err = await self.api_client.get_plugin_tmp_token(api_key=api_key)
            if err is not None:
                return ErrResponse(err)

            return OKResponse(resp)

    async def send_json(self, event, data, sid=None):
        message = {"type": event, "data": data}

        if sid is None:
            sockets = list(self.sockets.values())
            for ws in sockets:
                await self.send_socket_catch_exception(ws.send_json, message)
        elif sid in self.sockets:
            await self.send_socket_catch_exception(self.sockets[sid].send_json, message)

    async def send_error(self, err: ErrorNo, sid=None):
        await self.send_json(
            event="error",
            data={"message": err.message, "code": err.code, "data": err.data},
            sid=sid,
        )

    async def send_socket_catch_exception(self, function, message):
        try:
            await function(message)
        except (
            aiohttp.ClientError,
            aiohttp.ClientPayloadError,
            ConnectionResetError,
        ) as err:
            logging.warning("send error: {}".format(err))

    def send_sync(self, event, data, sid=None):
        asyncio.run_coroutine_threadsafe(self.send_json(event, data, sid), self.loop)

    def send_sync_error(self, err: ErrorNo, sid=None):
        self.send_sync(
            event="error",
            data={"message": err.message, "code": err.code, "data": err.data},
            sid=sid,
        )

    def check_sync_status(self, bizy_model_id: str, version_ids: list, sid=None):
        removed = []
        while True:
            # 从version_ids中移除removed中的version_id
            version_ids = [
                version_id for version_id in version_ids if version_id not in removed
            ]
            if len(version_ids) == 0:
                return

            for version_id in version_ids:
                future = asyncio.run_coroutine_threadsafe(
                    self.api_client.get_model_version_detail(version_id=version_id),
                    self.loop,
                )

                model_version, err = future.result(timeout=2)

                if err is not None:
                    self.send_sync(
                        event="error",
                        data={
                            "message": err.message,
                            "code": err.code,
                            "data": {
                                "bizy_model_id": bizy_model_id,
                                "version_id": version_id,
                            },
                        },
                        sid=sid,
                    )
                    removed.append(version_id)
                    continue

                if "available" in model_version and model_version["available"]:
                    self.send_sync(
                        event="synced",
                        data={
                            "version_id": model_version["id"],
                            "version": model_version["version"],
                            "model_id": bizy_model_id,
                            "model_name": model_version["bizy_model_name"],
                        },
                        sid=sid,
                    )
                    removed.append(version_id)
            time.sleep(5)

    def check_dataset_sync_status(self, dataset_id: str, version_ids: list, sid=None):
        removed = []
        while True:
            # 从version_ids中移除removed中的version_id
            version_ids = [
                version_id for version_id in version_ids if version_id not in removed
            ]
            if len(version_ids) == 0:
                return

            for version_id in version_ids:
                future = asyncio.run_coroutine_threadsafe(
                    self.api_client.get_dataset_version_detail(version_id=version_id),
                    self.loop,
                )

                dataset_version, err = future.result(timeout=2)

                if err is not None:
                    self.send_sync(
                        event="error",
                        data={
                            "message": err.message,
                            "code": err.code,
                            "data": {
                                "dataset_id": dataset_id,
                                "version_id": version_id,
                            },
                        },
                        sid=sid,
                    )
                    removed.append(version_id)
                    continue

                if "available" in dataset_version and dataset_version["available"]:
                    self.send_sync(
                        event="synced",
                        data={
                            "version_id": dataset_version["id"],
                            "version": dataset_version["version"],
                            "dataset_id": dataset_id,
                            "dataset_name": dataset_version["dataset_name"],
                        },
                        sid=sid,
                    )
                    removed.append(version_id)
            time.sleep(5)
