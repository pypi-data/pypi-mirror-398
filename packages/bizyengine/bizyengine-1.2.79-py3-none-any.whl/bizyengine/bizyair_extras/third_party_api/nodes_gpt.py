from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class GPT_IMAGE_1_T2I_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "GPT Image 1 Text To Image"
    RETURN_TYPES = ("IMAGE", """{"gpt-image-1": "gpt-image-1"}""")
    RETURN_NAMES = ("images", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/OpenAI"

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
                "size": (["1:1", "2:3", "3:2"], {"default": "1:1"}),
                "variants": ([1, 2, 4], {"default": 1}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        size = kwargs.get("size", "1:1")
        variants = kwargs.get("variants", 1)
        data = {
            "prompt": prompt,
            "size": size,
            "variants": variants,
        }
        if variants == 4:
            data["provider"] = "KieAI"
        return data, "gpt-image-1"

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class GPT_IMAGE_EDIT_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "GPT Image Edit"
    RETURN_TYPES = ("IMAGE", """{"gpt-image-1": "gpt-image-1"}""")
    RETURN_NAMES = ("images", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/OpenAI"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "size": (["1:1", "2:3", "3:2"], {"default": "1:1"}),
                "variants": ([1, 2, 4], {"default": 1}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        images = kwargs.get("images", None)
        if images is None:
            raise ValueError("Images are required")
        prompt = kwargs.get("prompt", "")
        size = kwargs.get("size", "1:1")
        variants = kwargs.get("variants", 1)

        urls = []
        for batch_number, img in enumerate(images if images is not None else []):
            if img is not None:
                url = self.upload_file(
                    tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                    f"{prompt_id}_{batch_number}.png",
                    headers,
                )
                urls.append(url)
        if len(urls) == 0:
            raise ValueError("At least one image is required")

        data = {
            "urls": urls,
            "prompt": prompt,
            "size": size,
            "variants": variants,
        }
        if variants == 4:
            data["provider"] = "KieAI"
        return data, "gpt-image-1"

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")
