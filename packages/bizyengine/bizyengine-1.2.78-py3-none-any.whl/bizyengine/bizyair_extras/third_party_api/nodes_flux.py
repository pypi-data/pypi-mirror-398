from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Flux_Kontext_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Flux Kontext API"
    RETURN_TYPES = (
        "IMAGE",
        """{"flux-kontext-pro": "flux-kontext","flux-kontext-max": "flux-kontext"}""",
    )
    RETURN_NAMES = ("image", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Flux"

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
                    ["flux-kontext-pro", "flux-kontext-max"],
                    {"default": "flux-kontext-pro"},
                ),
                "aspect_ratio": (
                    ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                    {"default": "16:9"},
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        image = kwargs.get("image", None)
        model = kwargs.get("model", "flux-kontext-pro")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        seed = kwargs.get("seed", 0)
        data = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "seed": seed,
        }
        if image is not None:
            image_url = self.upload_file(
                tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
                f"{prompt_id}.png",
                headers,
            )
            data["image"] = image_url
        return data, "flux-kontext"

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class Flux_2_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Flux 2 API"
    RETURN_TYPES = ("IMAGE", """{"flux-2-pro": "flux-2","flux-2-flex": "flux-2"}""")
    RETURN_NAMES = ("image", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Flux"

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
                    ["flux-2-pro", "flux-2-flex"],
                    {"default": "flux-2-pro"},
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 0,
                        "step": 16,
                        "tooltip": "必须为16的倍数，0代表使用输入图片宽度",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 0,
                        "step": 16,
                        "tooltip": "必须为16的倍数，0代表使用输入图片高度",
                    },
                ),
                "safety_tolerance": (
                    "INT",
                    {"min": 0, "max": 5, "default": 2, "tooltip": "值越大越宽松"},
                ),
                "guidance": (
                    "FLOAT",
                    {"min": 1.5, "max": 10, "default": 4.5, "tooltip": "仅flex支持"},
                ),
                "steps": (
                    "INT",
                    {"min": 1, "max": 50, "default": 50, "tooltip": "仅flex支持"},
                ),
            },
            "optional": {
                "images": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        images = kwargs.get("images", None)
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "flux-2-pro")
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        safety_tolerance = kwargs.get("safety_tolerance", 2)
        guidance = kwargs.get("guidance", 4.5)
        steps = kwargs.get("steps", 50)
        seed = kwargs.get("seed", 0)
        if images is not None and len(images) > 8 and model == "flux-2-pro":
            raise ValueError("Maximum number of images is 8 for flux-2-pro")
        if images is not None and len(images) > 10 and model == "flux-2-flex":
            raise ValueError("Maximum number of images is 10 for flux-2-flex")
        if width < 0 or height < 0:
            raise ValueError(
                "Width and height must be greater than 0, or supply 0 value to use input image's original size"
            )
        if safety_tolerance < 0 or safety_tolerance > 6:
            raise ValueError("Safety tolerance must be between 0 and 6")
        if guidance < 1.5 or guidance > 10:
            raise ValueError("Guidance must be between 1.5 and 10")
        if steps < 1 or steps > 50:
            raise ValueError("Steps must be between 1 and 50")
        parts = []
        for batch_number, img in enumerate(images if images is not None else []):
            if img is not None:
                url = self.upload_file(
                    tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                    f"{prompt_id}_{batch_number}.png",
                    headers,
                )
                parts.append(url)
        data = {
            "prompt": prompt,
            "model": model,
            "safety_tolerance": safety_tolerance,
            "guidance": guidance,
            "steps": steps,
            "seed": seed,
        }
        if width > 0:
            data["width"] = width
        if height > 0:
            data["height"] = height
        if len(parts) > 0:
            data["urls"] = parts
        return data, "flux-2"

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")
