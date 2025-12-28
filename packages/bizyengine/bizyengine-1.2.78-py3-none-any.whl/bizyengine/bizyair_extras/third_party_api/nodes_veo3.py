from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Veo_V3_1_I2V_API(BizyAirTrdApiBaseNode):
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
                "first_frame_image": ("IMAGE", {"tooltip": "首帧图片"}),
                "model": (["veo3.1-fast", "veo3.1-pro"], {"default": "veo3.1-fast"}),
            },
            "optional": {
                "last_frame_image": ("IMAGE", {"tooltip": "尾帧图片"}),
                "aspect_ratio": (
                    ["9:16", "16:9"],
                    {"default": "16:9"},
                ),
            },
        }

    NODE_DISPLAY_NAME = "Veo3.1 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"veo3.1-fast": "veo3.1","veo3.1-pro": "veo3.1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Veo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        model = kwargs.get("model", "veo3.1-fast")
        prompt = kwargs.get("prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        first_frame_image = kwargs.get("first_frame_image", None)
        last_frame_image = kwargs.get("last_frame_image", None)

        if prompt is None or prompt.strip() == "":
            raise ValueError("Prompt is required")

        # 上传图片
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        first_frame_image_url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}_first.png",
            headers,
        )
        data = {
            "aspect_ratio": aspect_ratio,
            "model": model,
            "prompt": prompt,
            "first_frame_image": first_frame_image_url,
        }
        if last_frame_image is not None:
            last_frame_image_url = self.upload_file(
                tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096),
                f"{prompt_id}_last.png",
                headers,
            )
            data["last_frame_image"] = last_frame_image_url

        return data, "veo3.1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Veo_V3_1_I2V_REF_API(BizyAirTrdApiBaseNode):
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
                "ref_image_1": ("IMAGE", {"tooltip": "参考图片1"}),
                "model": (["veo3.1-fast"], {"default": "veo3.1-fast"}),
            },
            "optional": {
                "ref_image_2": ("IMAGE", {"tooltip": "参考图片2"}),
                "ref_image_3": ("IMAGE", {"tooltip": "参考图片3"}),
                "aspect_ratio": (["16:9"], {"default": "16:9"}),
            },
        }

    NODE_DISPLAY_NAME = "Veo3.1 Image To Video (Reference Images)"
    RETURN_TYPES = ("VIDEO", """{"veo3.1-fast": "veo3.1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Veo"
    FUNCTION = "api_call"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        model = kwargs.get("model", "veo3.1-fast")
        prompt = kwargs.get("prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        ref_image_1 = kwargs.get("ref_image_1", None)
        ref_image_2 = kwargs.get("ref_image_2", None)
        ref_image_3 = kwargs.get("ref_image_3", None)

        if prompt is None or prompt.strip() == "":
            raise ValueError("Prompt is required")

        # 上传图片
        ref_images = []
        if ref_image_1 is not None:
            ref_image_1_url = self.upload_file(
                tensor_to_bytesio(image=ref_image_1, total_pixels=4096 * 4096),
                f"{prompt_id}_ref_1.png",
                headers,
            )
            ref_images.append(ref_image_1_url)
        if ref_image_2 is not None:
            ref_image_2_url = self.upload_file(
                tensor_to_bytesio(image=ref_image_2, total_pixels=4096 * 4096),
                f"{prompt_id}_ref_2.png",
                headers,
            )
            ref_images.append(ref_image_2_url)
        if ref_image_3 is not None:
            ref_image_3_url = self.upload_file(
                tensor_to_bytesio(image=ref_image_3, total_pixels=4096 * 4096),
                f"{prompt_id}_ref_3.png",
                headers,
            )
            ref_images.append(ref_image_3_url)
        if len(ref_images) == 0:
            raise ValueError("At least one reference image is required")
        data = {
            "aspect_ratio": aspect_ratio,
            "model": model,
            "prompt": prompt,
            "urls": ref_images,
        }
        return data, "veo3.1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Veo_V3_1_T2V_API(BizyAirTrdApiBaseNode):
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
                "model": (["veo3.1-fast", "veo3.1-pro"], {"default": "veo3.1-fast"}),
            },
            "optional": {
                "aspect_ratio": (
                    ["9:16", "16:9"],
                    {"default": "16:9"},
                ),
            },
        }

    NODE_DISPLAY_NAME = "Veo3.1 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"veo3.1-fast": "veo3.1","veo3.1-pro": "veo3.1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Veo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "veo3.1-fast")
        prompt = kwargs.get("prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")

        if prompt is None or prompt.strip() == "":
            raise ValueError("Prompt is required")
        data = {
            "aspect_ratio": aspect_ratio,
            "model": model,
            "prompt": prompt,
        }
        return data, "veo3.1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")
