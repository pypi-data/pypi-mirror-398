from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Hailuo2_3_T2V(BizyAirTrdApiBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model": (
                    ["MiniMax-Hailuo-2.3"],
                    {"default": "MiniMax-Hailuo-2.3"},
                ),
                "duration": ([6, 10], {"default": 6}),
                "resolution": (
                    ["768P", "1080P"],
                    {"default": "1080P"},
                ),
            },
        }

    NODE_DISPLAY_NAME = "Hailuo2.3 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"MiniMax-Hailuo-2.3-t2v": "MiniMax-Hailuo-2.3-t2v"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Hailuo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "MiniMax-Hailuo-2.3")
        duration = kwargs.get("duration", 6)
        prompt = kwargs.get("prompt", "")
        resolution = kwargs.get("resolution", "1080P")
        if resolution == "1080P" and duration == 10:
            raise ValueError(
                "Hailuo2.3 1080P resolution + 10s duration is not supported"
            )
        data = {
            "model": model,
            "duration": duration,
            "prompt": prompt,
            "resolution": resolution,
        }
        return data, "MiniMax-Hailuo-2.3-t2v"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Hailuo2_3_I2V(BizyAirTrdApiBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame_image": ("IMAGE",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model": (
                    ["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-2.3-Fast"],
                    {"default": "MiniMax-Hailuo-2.3"},
                ),
                "duration": ([6, 10], {"default": 6}),
                "resolution": (
                    ["768P", "1080P"],
                    {"default": "1080P"},
                ),
            },
        }

    NODE_DISPLAY_NAME = "Hailuo2.3 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"MiniMax-Hailuo-2.3-i2v": "MiniMax-Hailuo-2.3-i2v"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Hailuo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "MiniMax-Hailuo-2.3")
        duration = kwargs.get("duration", 6)
        prompt = kwargs.get("prompt", "")
        resolution = kwargs.get("resolution", "1080P")
        first_frame_image = kwargs.get("first_frame_image", None)
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        if resolution == "1080P" and duration == 10:
            raise ValueError(
                "Hailuo2.3 1080P resolution + 10s duration is not supported"
            )
        # 上传首帧图片
        first_frame_image_url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}.png",
            headers,
        )

        data = {
            "model": model,
            "duration": duration,
            "prompt": prompt,
            "resolution": resolution,
            "first_frame_image": first_frame_image_url,
        }
        return data, "MiniMax-Hailuo-2.3-i2v"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")
