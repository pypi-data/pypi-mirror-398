import base64
import json
import os
import time
from pathlib import Path

from bizyengine.core.common.env_var import (
    BIZYAIR_SERVER_MODE,
    BIZYAIR_SERVER_MODE_RSA_PRIVATE_KEY_PATH,
)

if BIZYAIR_SERVER_MODE:
    from Crypto.Cipher import PKCS1_v1_5
    from Crypto.PublicKey import RSA

from .errno import errnos
from .resp import ErrResponse

TYPE_OPTIONS = {
    "LoRA": "LoRA",
    "Controlnet": "Controlnet",
    "Checkpoint": "Checkpoint",
    "VAE": "VAE",
    "UNet": "UNet",
    "CLIP": "CLIP",
    "Upscaler": "Upscaler",
    "Detection": "Detection",
    "Other": "Other",
}

BASE_MODEL_TYPE_OPTIONS = {
    "Flux.1 D": "Flux.1 D",
    "SDXL": "SDXL",
    "SD 1.5": "SD 1.5",
    "SD 3.5": "SD 3.5",
    "Pony": "Pony",
    "Illustrious": "Illustrious",
    "Kolors": "Kolors",
    "Hunyuan 1": "Hunyuan 1",
    "Hunyuan Video": "Hunyuan Video",
    "Wan Video": "Wan Video",
    "Other": "Other",
}

ALLOW_TYPES = list(TYPE_OPTIONS.values())
ALLOW_BASE_MODEL_TYPES = list(BASE_MODEL_TYPE_OPTIONS.values())
ALLOW_UPLOADABLE_EXT_NAMES = [
    ".safetensors",
    ".pth",
    ".bin",
    ".pt",
    ".ckpt",
    ".gguf",
    ".sft",
]

current_path = os.path.abspath(os.path.dirname(__file__))

_RSA_CIPHER = None


def get_html_content(filename: str):
    html_file_path = Path(current_path) / filename
    with open(html_file_path, "r", encoding="utf-8") as htmlfile:
        html_content = htmlfile.read()
    return html_content


def is_string_valid(s):
    # 检查s是否已经被定义（即不是None）且不是空字符串
    if s is not None and s != "":
        return True
    else:
        return False


def to_slash(path):
    return path.replace("\\", "/")


def check_str_param(json_data, param_name: str, err):
    if param_name not in json_data:
        return ErrResponse(err)
    if not is_string_valid(json_data[param_name]):
        return ErrResponse(err)
    return None


def check_type(json_data):
    if "type" not in json_data:
        return ErrResponse(errnos.INVALID_TYPE)
    if not is_string_valid(json_data["type"]) or (
        json_data["type"] not in ALLOW_TYPES and json_data["type"] != "Workflow"
    ):
        return ErrResponse(errnos.INVALID_TYPE)
    return None


def types():
    types = []
    for k, v in TYPE_OPTIONS.items():
        types.append({"label": k, "value": v})
    return types


def update_base_model_types(new_types_from_dict):
    global BASE_MODEL_TYPE_OPTIONS
    BASE_MODEL_TYPE_OPTIONS = {}
    for item in new_types_from_dict:
        BASE_MODEL_TYPE_OPTIONS[item["label"]] = item["value"]


def base_model_types():
    base_model_types = []
    for v in BASE_MODEL_TYPE_OPTIONS.values():
        base_model_types.append({"label": v, "value": v})
    return base_model_types


def is_allow_ext_name(local_file_name):
    if not os.path.isfile(local_file_name):
        return False
    _, ext = os.path.splitext(local_file_name)
    return ext.lower() in ALLOW_UPLOADABLE_EXT_NAMES


def decrypt_apikey(apikey_ciphertext):
    if not BIZYAIR_SERVER_MODE_RSA_PRIVATE_KEY_PATH:
        return apikey_ciphertext, None
    # v4.public开头不用解密
    if apikey_ciphertext.startswith("v4.public"):
        return apikey_ciphertext, None
    global _RSA_CIPHER
    if not _RSA_CIPHER:
        with open(BIZYAIR_SERVER_MODE_RSA_PRIVATE_KEY_PATH, "rb") as f:
            private_key_data = f.read()
            private_key = RSA.import_key(private_key_data)
            _RSA_CIPHER = PKCS1_v1_5.new(private_key)
    plaintext = _RSA_CIPHER.decrypt(base64.b64decode(apikey_ciphertext), None)
    if not plaintext:
        return None, errnos.INVALID_API_KEY
    dict = json.loads(plaintext.decode("utf-8"))
    if "timestamp" in dict and "expiresIn" in dict:
        now = time.time_ns() // 1_000_000
        if now - int(dict["timestamp"]) > int(dict["expiresIn"]):
            return None, errnos.INVALID_API_KEY
    else:
        return None, errnos.INVALID_API_KEY
    return dict["data"], None
