from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Sora_V2_I2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Sora2 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"sora-2": "sora-2","sora-2-pro": "sora-2-pro"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Sora"

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
                "image": ("IMAGE", {"tooltip": "首帧图片"}),
                "model": (["sora-2", "sora-2-pro"], {"default": "sora-2"}),
            },
            "optional": {
                "aspect_ratio": (
                    ["9:16", "16:9"],
                    {"default": "16:9"},
                ),
                "duration": ([10, 15], {"default": 10}),
                "size": (["small", "large"], {"default": "small"}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        duration = kwargs.get("duration", 10)
        size = kwargs.get("size", "small")
        model = kwargs.get("model", "sora-2")
        prompt = kwargs.get("prompt", "")
        image = kwargs.get("image", None)
        if image is None:
            raise ValueError("Image is required")
        # 上传图片
        url = self.upload_file(
            tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
            f"{prompt_id}.png",
            headers,
        )

        data = {
            "model": model,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "size": size,
            "prompt": prompt,
            "url": url,
        }
        return data, model

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Sora_V2_T2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Sora2 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"sora-2": "sora-2","sora-2-pro": "sora-2-pro"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Sora"

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
                "model": (["sora-2", "sora-2-pro"], {"default": "sora-2"}),
            },
            "optional": {
                "aspect_ratio": (
                    ["9:16", "16:9"],
                    {"default": "16:9"},
                ),
                "duration": ([10, 15], {"default": 10}),
                "size": (["small", "large"], {"default": "small"}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "sora-2")
        duration = kwargs.get("duration", 10)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        size = kwargs.get("size", "small")
        prompt = kwargs.get("prompt", "")
        data = {
            "model": model,
            "duration": duration,
            "size": size,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }
        return data, model

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


# class Sora_V2_PRO_I2V_API(BizyAirTrdApiBaseNode):
#     NODE_DISPLAY_NAME = "Sora2 Pro Image To Video"
#     RETURN_TYPES = ("VIDEO",)
#     RETURN_NAMES = ("video",)
#     CATEGORY = "☁️BizyAir/External APIs/Sora"

#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "prompt": (
#                     "STRING",
#                     {
#                         "multiline": True,
#                         "default": "",
#                     },
#                 ),
#                 "image": ("IMAGE", {"tooltip": "首帧图片"}),
#                 "model": (["sora-2-pro"], {"default": "sora-2-pro"}),
#             },
#             "optional": {
#                 "aspect_ratio": (
#                     ["9:16", "16:9"],
#                     {"default": "16:9"},
#                 ),
#                 "duration": ([10, 15, 25], {"default": 10}),
#                 "size": (["standard", "high"], {"default": "standard"}),
#             },
#         }

#     def handle_inputs(self, headers, prompt_id, **kwargs):
#         # 参数
#         aspect_ratio = kwargs.get("aspect_ratio", "16:9")
#         duration = kwargs.get("duration", 10)
#         size = kwargs.get("size", "standard")
#         model = kwargs.get("model", "sora-2-pro")
#         prompt = kwargs.get("prompt", "")
#         image = kwargs.get("image", None)
#         if image is None:
#             raise ValueError("Image is required")
#         # 上传图片
#         url = self.upload_file(
#             tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
#             f"{prompt_id}.png",
#             headers,
#         )

#         data = {
#             "model": model,
#             "aspect_ratio": aspect_ratio,
#             "duration": duration,
#             "size": size,
#             "prompt": prompt,
#             "url": url,
#         }
#         return data, model


# class Sora_V2_PRO_T2V_API(BizyAirTrdApiBaseNode):
#     NODE_DISPLAY_NAME = "Sora2 Pro Text To Video"
#     RETURN_TYPES = ("VIDEO",)
#     RETURN_NAMES = ("video",)
#     CATEGORY = "☁️BizyAir/External APIs/Sora"

#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "prompt": (
#                     "STRING",
#                     {
#                         "multiline": True,
#                         "default": "",
#                     },
#                 ),
#                 "model": (["sora-2-pro"], {"default": "sora-2-pro"}),
#             },
#             "optional": {
#                 "aspect_ratio": (
#                     ["9:16", "16:9"],
#                     {"default": "16:9"},
#                 ),
#                 "duration": ([10, 15, 25], {"default": 10}),
#                 "size": (["standard", "high"], {"default": "standard"}),
#             },
#         }

#     def handle_inputs(self, headers, prompt_id, **kwargs):
#         model = kwargs.get("model", "sora-2-pro")
#         duration = kwargs.get("duration", 10)
#         aspect_ratio = kwargs.get("aspect_ratio", "16:9")
#         size = kwargs.get("size", "standard")
#         prompt = kwargs.get("prompt", "")
#         data = {
#             "model": model,
#             "duration": duration,
#             "size": size,
#             "prompt": prompt,
#             "aspect_ratio": aspect_ratio,
#         }
#         return data, model

#     def handle_outputs(self, outputs):
#         return (outputs[0][0],)
