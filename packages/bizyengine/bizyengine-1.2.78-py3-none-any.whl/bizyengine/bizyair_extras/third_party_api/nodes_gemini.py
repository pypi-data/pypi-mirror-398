from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


# FROM: https://github.com/ShmuelRonen/ComfyUI-NanoBanano/blob/9eeb8f2411fd0ff08791bdf5e24eec347456c8b8/nano_banano.py#L191
def build_prompt_for_operation(
    prompt,
    operation,
    has_references=False,
    aspect_ratio="auto",
    character_consistency=True,
):
    """Build optimized prompt based on operation type"""

    auto_aspect = (
        "keep the original image aspect ratio"
        if has_references
        else "use an appropriate aspect ratio"
    )
    aspect_instructions = {
        "1:1": "square format",
        "16:9": "widescreen landscape format",
        "9:16": "portrait format",
        "4:3": "standard landscape format",
        "3:4": "standard portrait format",
        "auto": auto_aspect,
    }

    base_quality = "Generate a high-quality, photorealistic image"
    format_instruction = f"in {aspect_instructions.get(aspect_ratio, auto_aspect)}"

    if operation == "generate":
        if has_references:
            final_prompt = f"{base_quality} inspired by the style and elements of the reference images. {prompt}. {format_instruction}."
        else:
            final_prompt = f"{base_quality} of: {prompt}. {format_instruction}."

    elif operation == "edit":
        if not has_references:
            return "Error: Edit operation requires reference images"
        # No aspect ratio for edit - preserve original image dimensions
        final_prompt = f"Edit the provided reference image(s). {prompt}. Maintain the original composition and quality while making the requested changes."

    elif operation == "style_transfer":
        if not has_references:
            return "Error: Style transfer requires reference images"
        final_prompt = f"Apply the style from the reference images to create: {prompt}. Blend the stylistic elements naturally. {format_instruction}."

    elif operation == "object_insertion":
        if not has_references:
            return "Error: Object insertion requires reference images"
        final_prompt = f"Insert or blend the following into the reference image(s): {prompt}. Ensure natural lighting, shadows, and perspective. {format_instruction}."

    if character_consistency and has_references:
        final_prompt += " Maintain character consistency and visual identity from the reference images."

    return final_prompt


class NanoBanana(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "NanoBanana"
    RETURN_TYPES = (
        "IMAGE",
        "STRING",
        """{"gemini-2.5-flash-image": "gemini-2.5-flash-image"}""",
    )
    RETURN_NAMES = ("image", "string", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Gemini"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "operation": (
                    ["generate", "edit", "style_transfer", "object_insertion"],
                    {
                        "default": "generate",
                        "tooltip": "Choose the type of image operation",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "top_p": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "max_tokens": ("INT", {"default": 8192, "min": 1, "max": 8192}),
            },
            "optional": {
                "image": ("IMAGE",),
                "image2": ("IMAGE",),
                "image3": ("IMAGE",),
                "image4": ("IMAGE",),
                "image5": ("IMAGE",),
                "quality": (
                    ["standard", "high"],
                    {"default": "high", "tooltip": "Image generation quality"},
                ),
                "aspect_ratio": (
                    ["1:1", "16:9", "9:16", "4:3", "3:4", "auto"],
                    {"default": "auto", "tooltip": "Output image aspect ratio"},
                ),
                "character_consistency": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Maintain character consistency across edits",
                    },
                ),
            },
            "hidden": {"bizyair_model_name": {"default": "gemini-2.5-flash-image"}},
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        operation = kwargs.get("operation", "generate")
        temperature = kwargs.get("temperature", 1.0)
        top_p = kwargs.get("top_p", 1.0)
        seed = kwargs.get("seed", 0)
        max_tokens = kwargs.get("max_tokens", 8192)
        quality = kwargs.get("quality", "high")
        aspect_ratio = kwargs.get("aspect_ratio", "auto")
        character_consistency = kwargs.get("character_consistency", True)
        prompt = kwargs.get("prompt", "")

        parts = []
        for i, img in enumerate(
            [
                kwargs.get("image", None),
                kwargs.get("image2", None),
                kwargs.get("image3", None),
                kwargs.get("image4", None),
                kwargs.get("image5", None),
            ],
            1,
        ):
            if img is not None:
                url = self.upload_file(
                    tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                    f"{prompt_id}_{i}.png",
                    headers,
                )
                parts.append(url)

        prompt = build_prompt_for_operation(
            prompt,
            operation,
            has_references=len(parts) > 0,
            aspect_ratio=aspect_ratio,
            character_consistency=character_consistency,
        )
        if quality == "high":
            prompt += " Use the highest quality settings available."

        data = {
            "urls": parts,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
            "max_tokens": max_tokens,
        }
        if aspect_ratio != "auto":
            data["aspect_ratio"] = aspect_ratio
        return data, "gemini-2.5-flash-image"

    def handle_outputs(self, outputs):
        text = None
        if len(outputs[1]) > 0:
            image = outputs[1][0]
        else:
            raise ValueError("No image found in response")
        if len(outputs[2]) > 0:
            text = outputs[2][0]
        return (image, text, "")


class NanoBananaPro(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "NanoBananaPro"
    RETURN_TYPES = (
        "IMAGE",
        "STRING",
        """{"gemini-3-pro-image-preview": "gemini-3-pro-image-preview"}""",
    )
    RETURN_NAMES = ("image", "string", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Gemini"
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "operation": (
                    ["generate", "edit", "style_transfer", "object_insertion"],
                    {
                        "default": "generate",
                        "tooltip": "Choose the type of image operation",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "top_p": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "max_tokens": ("INT", {"default": 32768, "min": 1, "max": 32768}),
                "aspect_ratio": (
                    [
                        "1:1",
                        "2:3",
                        "3:2",
                        "3:4",
                        "4:3",
                        "4:5",
                        "5:4",
                        "9:16",
                        "16:9",
                        "21:9",
                        "auto",
                    ],
                    {"default": "auto", "tooltip": "Output image aspect ratio"},
                ),
                "resolution": (["1K", "2K", "4K", "auto"], {"default": "auto"}),
            },
            "optional": {
                "images": ("IMAGE",),
                "quality": (
                    ["standard", "high"],
                    {"default": "high", "tooltip": "Image generation quality"},
                ),
                "character_consistency": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Maintain character consistency across edits",
                    },
                ),
                "inputcount": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 14,
                        "tooltip": "动态控制输入的参考图数量，范围1-14，点击Update inputs按钮刷新",
                    },
                ),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        operation = kwargs.get("operation", ["generate"])[0]
        temperature = kwargs.get("temperature", [1.0])[0]
        top_p = kwargs.get("top_p", [1.0])[0]
        seed = kwargs.get("seed", [0])[0]
        max_tokens = kwargs.get("max_tokens", [32768])[0]
        quality = kwargs.get("quality", ["high"])[0]
        aspect_ratio = kwargs.get("aspect_ratio", ["auto"])[0]
        resolution = kwargs.get("resolution", ["auto"])[0]
        images = kwargs.get("images", [])
        character_consistency = kwargs.get("character_consistency", [True])[0]
        prompt = kwargs.get("prompt", [""])[0]

        # 多图的情况可以认为图片输入都是List[Image Batch]
        total_input_images = 0
        for _, img_batch in enumerate(images if images is not None else []):
            if img_batch is not None:
                total_input_images += img_batch.shape[0]
        extra_images, total_extra_images = self.get_extra_images(**kwargs)
        total_input_images += total_extra_images
        if total_input_images > 14:
            raise ValueError("Maximum number of images is 14")
        parts = []
        index = 1
        for _, img_batch in enumerate(images if images is not None else []):
            for _, img in enumerate(img_batch if img_batch is not None else []):
                if img is not None:
                    url = self.upload_file(
                        tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                        f"{prompt_id}_{index}.png",
                        headers,
                    )
                    parts.append(url)
                    index += 1
        for _, img_batch in enumerate(extra_images):
            for _, img in enumerate(img_batch if img_batch is not None else []):
                if img is not None:
                    url = self.upload_file(
                        tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                        f"{prompt_id}_{index}.png",
                        headers,
                    )
                    parts.append(url)
                    index += 1

        prompt = build_prompt_for_operation(
            prompt,
            operation,
            has_references=len(parts) > 0,
            aspect_ratio=aspect_ratio,
            character_consistency=character_consistency,
        )
        if quality == "high":
            prompt += " Use the highest quality settings available."

        data = {
            "urls": parts,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
            "max_tokens": max_tokens,
        }
        if aspect_ratio != "auto":
            data["aspect_ratio"] = aspect_ratio
        if resolution != "auto":
            data["resolution"] = resolution
        return data, "gemini-3-pro-image-preview"

    def handle_outputs(self, outputs):
        text = None
        if len(outputs[1]) > 0:
            image = outputs[1][0]
        else:
            raise ValueError("No image found in response")
        if len(outputs[2]) > 0:
            text = outputs[2][0]
        return (image, text, "")


class NanoBananaProOfficial(BizyAirTrdApiBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "top_p": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "max_tokens": ("INT", {"default": 32768, "min": 1, "max": 32768}),
                "aspect_ratio": (
                    [
                        "1:1",
                        "2:3",
                        "3:2",
                        "3:4",
                        "4:3",
                        "4:5",
                        "5:4",
                        "9:16",
                        "16:9",
                        "21:9",
                        "auto",
                    ],
                    {"default": "auto", "tooltip": "Output image aspect ratio"},
                ),
                "resolution": (["1K", "2K", "4K", "auto"], {"default": "auto"}),
            },
            "optional": {
                "images": ("IMAGE",),
                "inputcount": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 14,
                        "tooltip": "动态控制输入的参考图数量，范围1-14，点击Update inputs按钮刷新",
                    },
                ),
            },
        }

    RETURN_TYPES = (
        "IMAGE",
        "STRING",
        """{"gemini-3-pro-image-preview": "gemini-3-pro-image-preview"}""",
    )
    RETURN_NAMES = ("image", "string", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Gemini"
    NODE_DISPLAY_NAME = "NanoBananaPro (Official Parameters)"
    INPUT_IS_LIST = True

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", [""])[0]
        temperature = kwargs.get("temperature", 1.0)[0]
        top_p = kwargs.get("top_p", [1.0])[0]
        seed = kwargs.get("seed", [0])[0]
        max_tokens = kwargs.get("max_tokens", [32768])[0]
        aspect_ratio = kwargs.get("aspect_ratio", ["auto"])[0]
        resolution = kwargs.get("resolution", ["auto"])[0]
        images = kwargs.get("images", [])
        extra_images, total_extra_images = self.get_extra_images(**kwargs)
        # 多图的情况可以认为图片输入都是List[Image Batch]
        total_input_images = 0
        for _, img_batch in enumerate(images if images is not None else []):
            if img_batch is not None:
                total_input_images += img_batch.shape[0]
        total_input_images += total_extra_images
        if total_input_images > 14:
            raise ValueError("Maximum number of images is 14")
        parts = []
        index = 1
        for _, img_batch in enumerate(images if images is not None else []):
            for _, img in enumerate(img_batch if img_batch is not None else []):
                if img is not None:
                    url = self.upload_file(
                        tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                        f"{prompt_id}_{index}.png",
                        headers,
                    )
                    parts.append(url)
                    index += 1
        for _, img_batch in enumerate(extra_images):
            for _, img in enumerate(img_batch if img_batch is not None else []):
                if img is not None:
                    url = self.upload_file(
                        tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                        f"{prompt_id}_{index}.png",
                        headers,
                    )
                    parts.append(url)
                    index += 1
        data = {
            "urls": parts,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
            "max_tokens": max_tokens,
        }
        if aspect_ratio != "auto":
            data["aspect_ratio"] = aspect_ratio
        if resolution != "auto":
            data["resolution"] = resolution
        return data, "gemini-3-pro-image-preview"

    def handle_outputs(self, outputs):
        text = None
        if len(outputs[1]) > 0:
            image = outputs[1][0]
        else:
            raise ValueError("No image found in response")
        if len(outputs[2]) > 0:
            text = outputs[2][0]
        return (image, text, "")
