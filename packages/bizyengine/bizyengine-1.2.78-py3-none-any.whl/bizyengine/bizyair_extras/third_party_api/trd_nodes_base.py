import abc
import io
import json
import logging
import time
from typing import List, Tuple

import requests
import torch
from bizyairsdk import bytesio_to_image_tensor, common_upscale
from comfy_api.latest._input_impl import VideoFromFile

from bizyengine.core import (
    BizyAirMiscBaseNode,
    pop_api_key_and_prompt_id,
    register_node,
)
from bizyengine.core.common import client
from bizyengine.core.common.client import send_request
from bizyengine.core.common.env_var import BIZYAIR_X_SERVER
from bizyengine.core.nodes_base import PREFIX

from ..utils.aliyun_oss import parse_upload_token, upload_file_without_sdk


class TrdBase(abc.ABC):
    @abc.abstractmethod
    # Return: data, model, prompt
    def handle_inputs(self, headers, prompt_id, **kwargs) -> Tuple[dict, str]:
        pass

    @abc.abstractmethod
    # Return: videos, images, texts
    def handle_outputs(
        self, outputs: Tuple[List[VideoFromFile], List[torch.Tensor], List[str]]
    ) -> Tuple:
        pass


class BizyAirTrdApiBaseNode(BizyAirMiscBaseNode, TrdBase):
    FUNCTION = "api_call"
    OUTPUT_NODE = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        register_node(cls, PREFIX)

    def api_call(self, **kwargs):
        extra_data = pop_api_key_and_prompt_id(kwargs)
        headers = client.headers(api_key=extra_data["api_key"])
        prompt_id = extra_data["prompt_id"]
        headers["X-BIZYAIR-PROMPT-ID"] = prompt_id

        data, model = self.handle_inputs(headers, prompt_id, **kwargs)
        outputs = self.create_task_and_wait_for_completion(data, model, headers)
        return self.handle_outputs(outputs)

    def create_task_and_wait_for_completion(
        self, data, model, headers
    ) -> Tuple[List[VideoFromFile], List[torch.Tensor], List[str]]:
        # 创建任务
        create_task_url = f"{BIZYAIR_X_SERVER}/trd_api/{model}"
        json_payload = json.dumps(data).encode("utf-8")
        logging.debug(f"json_payload: {json_payload}")
        create_api_resp = send_request(
            url=create_task_url,
            data=json_payload,
            headers=headers,
        )
        logging.debug(
            f"{self.NODE_DISPLAY_NAME} create task api resp: {create_api_resp}"
        )

        # 检查任务创建是否成功
        if "data" not in create_api_resp or "request_id" not in create_api_resp["data"]:
            raise ValueError(f"Invalid response: {create_api_resp}")

        # 轮询获取结果，最多等待1小时
        request_id = create_api_resp["data"]["request_id"]
        logging.info(f"{self.NODE_DISPLAY_NAME} task created, request_id: {request_id}")
        start_time = time.time()
        status_url = f"{BIZYAIR_X_SERVER}/trd_api/{request_id}"
        while time.time() - start_time < 3600:
            time.sleep(10)
            try:
                status_api_resp = send_request(
                    method="GET",
                    url=status_url,
                    headers=headers,
                )
            except Exception as e:
                logging.error(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} status api error: {e}"
                )
                continue

            if "data" not in status_api_resp:
                logging.error(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} status api resp no data: {status_api_resp}"
                )
                continue
            if "status" not in status_api_resp["data"]:
                logging.error(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} status api resp no status: {status_api_resp}"
                )
                continue
            status = status_api_resp["data"]["status"]
            if status == "failed":
                raise ValueError(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} failed: {status_api_resp}"
                )
            if status == "running":
                continue

            # 成功，获取输出结果
            if "outputs" not in status_api_resp["data"]:
                raise ValueError(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} no outputs: {status_api_resp}"
                )
            logging.info(
                f"{self.NODE_DISPLAY_NAME} task {request_id} success: {status_api_resp}"
            )
            # 分别处理视频、图片、文本
            videos = []
            images = []
            texts = []
            outputs = status_api_resp["data"]["outputs"]
            try:
                if "videos" in outputs:
                    for video_url in outputs["videos"]:
                        video_resp = requests.get(video_url, stream=True, timeout=3600)
                        video_resp.raise_for_status()  # 非 2xx 会抛异常
                        videos.append(VideoFromFile(io.BytesIO(video_resp.content)))
                if "images" in outputs:
                    for image_url in outputs["images"]:
                        image_resp = requests.get(image_url, stream=True, timeout=3600)
                        image_resp.raise_for_status()  # 非 2xx 会抛异常
                        images.append(
                            bytesio_to_image_tensor(io.BytesIO(image_resp.content))
                        )
                if "texts" in outputs:
                    for text in outputs["texts"]:
                        texts.append(text)
            except Exception as e:
                logging.error(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} handle outputs error: {e}"
                )
                raise ValueError(
                    f"{self.NODE_DISPLAY_NAME} task {request_id} handle outputs error: {e}, please download the outputs manually, outputs: {outputs}"
                )

            return (videos, images, texts)

        raise ValueError(
            f"{self.NODE_DISPLAY_NAME} task timed out, request ID: {request_id}"
        )

    def upload_file(self, bytes, file_name, headers):
        oss_token_url = (
            f"{BIZYAIR_X_SERVER}/upload/token?file_name={file_name}&file_type=inputs"
        )
        token_resp = send_request("GET", oss_token_url, headers=headers)
        auth_info = parse_upload_token(token_resp)
        return upload_file_without_sdk(file_content=bytes, **auth_info)

    def combine_images(self, images: List[torch.Tensor]) -> torch.Tensor:
        s = None
        if images is not None and len(images) > 0:
            for _, image in enumerate(images):
                if s is None:
                    s = image
                else:
                    # ComfyUI BatchImage logic
                    if s.shape[1:] != image.shape[1:]:
                        image = common_upscale(
                            image.movedim(-1, 1),
                            s.shape[2],
                            image.shape[1],
                            "bilinear",
                            "center",
                        ).movedim(1, -1)
                    s = torch.cat((s, image), dim=0)
        return s

    def get_extra_images(self, **kwargs) -> Tuple[List, int]:
        input_is_list = getattr(self, "INPUT_IS_LIST", False)
        if not input_is_list:
            raise ValueError(
                f"{type(self).__name__} get_extra_images only supports INPUT_IS_LIST=True"
            )
        inputcount = kwargs.get("inputcount", [1])[0]
        # List[Tensor]
        extra_images = []
        total = 0
        for i in range(1, inputcount):
            # 可以认为图片输入都是List[Batch]
            images = kwargs.get(f"image_{i + 1}", None)
            for _, img_batch in enumerate(images if images is not None else []):
                if img_batch is not None:
                    total += img_batch.shape[0]
                    extra_images.append(img_batch)
        return (extra_images, total)
