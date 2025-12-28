from enum import Enum

from bizyairsdk import (
    base64_to_tensor,
    decode_base64_to_image,
    decode_base64_to_np,
    decode_comfy_image,
    decode_data,
    encode_comfy_image,
    encode_data,
    encode_image_to_base64,
    numpy_to_base64,
)

# from .common.env_var import BIZYAIR_DEBUG


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
