from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Seedream4(BizyAirTrdApiBaseNode):
    RETURN_TYPES = (
        "IMAGE",
        """{"doubao-seedream-4-0-250828": "doubao-seedream-4-0-250828"}""",
    )
    RETURN_NAMES = ("images", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Doubao"
    NODE_DISPLAY_NAME = "Seedream4"

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
                "size": (
                    [
                        "1K Square (1024x1024)",
                        "2K Square (2048x2048)",
                        "4K Square (4096x4096)",
                        "HD 16:9 (1920x1080)",
                        "2K 16:9 (2560x1440)",
                        "4K 16:9 (3840x2160)",
                        "Portrait 9:16 (1080x1920)",
                        "Portrait 3:4 (1536x2048)",
                        "Landscape 4:3 (2048x1536)",
                        "Ultra-wide 21:9 (3440x1440)",
                        "Custom",
                    ],
                    {
                        "default": "HD 16:9 (1920x1080)",
                    },
                ),
                "custom_width": ("INT", {"default": 1920, "min": 1024, "max": 4096}),
                "custom_height": ("INT", {"default": 1080, "min": 1024, "max": 4096}),
                "model": (
                    ["doubao-seedream-4-0-250828"],
                    {"default": "doubao-seedream-4-0-250828"},
                ),
            },
            "optional": {
                "image": ("IMAGE",),
                "image2": ("IMAGE",),
                "image3": ("IMAGE",),
                "image4": ("IMAGE",),
                "image5": ("IMAGE",),
                "image6": ("IMAGE",),
                "image7": ("IMAGE",),
                "image8": ("IMAGE",),
                "image9": ("IMAGE",),
                "image10": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "doubao-seedream-4-0-250828")
        prompt = kwargs.get("prompt", "")
        size = kwargs.get("size", "1K Square (1024x1024)")

        match size:
            case "1K Square (1024x1024)":
                width = 1024
                height = 1024
            case "2K Square (2048x2048)":
                width = 2048
                height = 2048
            case "4K Square (4096x4096)":
                width = 4096
                height = 4096
            case "HD 16:9 (1920x1080)":
                width = 1920
                height = 1080
            case "2K 16:9 (2560x1440)":
                width = 2560
                height = 1440
            case "4K 16:9 (3840x2160)":
                width = 3840
                height = 2160
            case "Portrait 9:16 (1080x1920)":
                width = 1080
                height = 1920
            case "Portrait 3:4 (1536x2048)":
                width = 1536
                height = 2048
            case "Landscape 4:3 (2048x1536)":
                width = 2048
                height = 1536
            case "Ultra-wide 21:9 (3440x1440)":
                width = 3440
                height = 1440
            case "Custom":
                width = kwargs.get("custom_width", 1920)
                height = kwargs.get("custom_height", 1080)

            case _:
                raise ValueError(f"Invalid size: {size}")

        sizeStr = f"{width}x{height}"

        images = []
        total_size = 0
        for i, img in enumerate(
            [
                kwargs.get("image", None),
                kwargs.get("image2", None),
                kwargs.get("image3", None),
                kwargs.get("image4", None),
                kwargs.get("image5", None),
                kwargs.get("image6", None),
                kwargs.get("image7", None),
                kwargs.get("image8", None),
                kwargs.get("image9", None),
                kwargs.get("image10", None),
            ],
            1,
        ):
            if img is not None:
                # 都当作PNG就行
                bio = tensor_to_bytesio(image=img, total_pixels=4096 * 4096)
                length = bio.getbuffer().nbytes
                if length > 10 * 1024 * 1024:
                    raise ValueError(
                        "Image size is too large, Seedream 4.0 only supports up to 10MB"
                    )
                total_size += length
                if total_size > 50 * 1024 * 1024:
                    raise ValueError(
                        "Total size of images is too large, BizyAir only supports up to 50MB"
                    )
                images.append(self.upload_file(bio, f"{prompt_id}_{i}.png", headers))

        data = {
            "prompt": prompt,
            "size": sizeStr,
            "image": images,
            "model": model,
            "watermark": False,
            "response_format": "url",
        }

        return data, model

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class Seedream4_5(BizyAirTrdApiBaseNode):
    RETURN_TYPES = (
        "IMAGE",
        """{"doubao-seedream-4-5-251128": "doubao-seedream-4-5-251128"}""",
    )
    RETURN_NAMES = ("images", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Doubao"
    NODE_DISPLAY_NAME = "Seedream 4.5"
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
                "model": (
                    ["doubao-seedream-4-5-251128"],
                    {"default": "doubao-seedream-4-5-251128"},
                ),
                "size": (
                    [
                        "2K",
                        "4K",
                        "Custom",
                    ],
                    {
                        "default": "2K",
                    },
                ),
                "custom_width": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 480,
                        "max": 4096,
                        "tooltip": "总像素取值范围 [2560x1440=3686400, 4096x4096=16777216], 宽高比取值范围：[1/16, 16]",
                    },
                ),
                "custom_height": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 480,
                        "max": 4096,
                        "tooltip": "总像素取值范围 [2560x1440=3686400, 4096x4096=16777216], 宽高比取值范围：[1/16, 16]",
                    },
                ),
                "max_images": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 15,
                        "tooltip": "实际可生成的图片数量，除受到 max_images 影响外，还受到输入的参考图数量影响。输入的参考图数量+最终生成的图片数量≤15张。",
                    },
                ),
                "optimize_prompt": (
                    ["disabled", "standard"],
                    {
                        "default": "disabled",
                        "tooltip": "提示词优化功能的配置。standard：标准模式，生成内容的质量更高，耗时较长。",
                    },
                ),
            },
            "optional": {
                "images": (
                    "IMAGE",
                    {"tooltip": "参考图，数量不超过14张。会影响组图生成数量"},
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
        # up to 14 ref images
        # 10mb each
        # custom total pixels [3686400, 16777216]
        # custom size ratio [1/16, 16]
        model = kwargs.get("model", ["doubao-seedream-4-0-250828"])[0]
        prompt = kwargs.get("prompt", [""])[0]
        size = kwargs.get("size", ["2K"])[0]
        images = kwargs.get("images", [])
        optimize_prompt = kwargs.get("optimize_prompt", ["disabled"])[0]
        max_images = kwargs.get("max_images", [1])[0]

        # 多图的情况可以认为图片输入都是List[Image Batch]
        total_input_images = 0
        for _, img_batch in enumerate(images if images is not None else []):
            if img_batch is not None:
                total_input_images += img_batch.shape[0]
        extra_images, total_extra_images = self.get_extra_images(**kwargs)
        total_input_images += total_extra_images
        if total_input_images > 14:
            raise ValueError("Total number of input images is too large, maximum is 14")

        if size == "Custom":
            width = kwargs.get("custom_width", [2048])[0]
            height = kwargs.get("custom_height", [2048])[0]
            if width * height < 3686400 or width * height > 16777216:
                raise ValueError("Total pixels must be between 3686400 and 16777216")
            if width / height < 1 / 16 or width / height > 16:
                raise ValueError("Width/height ratio must be between 1/16 and 16")
            size = f"{width}x{height}"

        parts = []
        index = 1
        for _, img_batch in enumerate(images if images is not None else []):
            for _, img in enumerate(img_batch if img_batch is not None else []):
                if img is not None:
                    bio = tensor_to_bytesio(image=img, total_pixels=4096 * 4096)
                    length = bio.getbuffer().nbytes
                    if length > 10 * 1024 * 1024:
                        raise ValueError(
                            "Image size is too large, Seedream 4.5 only supports up to 10MB"
                        )
                    url = self.upload_file(
                        bio,
                        f"{prompt_id}_{index}.png",
                        headers,
                    )
                    parts.append(url)
                    index += 1
        for _, img_batch in enumerate(extra_images):
            for _, img in enumerate(img_batch if img_batch is not None else []):
                if img is not None:
                    bio = tensor_to_bytesio(image=img, total_pixels=4096 * 4096)
                    length = bio.getbuffer().nbytes
                    if length > 10 * 1024 * 1024:
                        raise ValueError(
                            "Image size is too large, Seedream 4.5 only supports up to 10MB"
                        )
                    url = self.upload_file(
                        bio,
                        f"{prompt_id}_{index}.png",
                        headers,
                    )
                    parts.append(url)
                    index += 1

        data = {
            "prompt": prompt,
            "size": size,
            "model": model,
            "max_images": max_images,
        }
        if len(parts) > 0:
            data["image"] = parts
        if optimize_prompt != "disabled":
            data["optimize_prompt"] = optimize_prompt

        return data, model

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class Seededit3(BizyAirTrdApiBaseNode):
    RETURN_TYPES = (
        "IMAGE",
        """{"doubao-seededit-3-0-i2i-250628": "doubao-seededit-3-0-i2i-250628"}""",
    )
    RETURN_NAMES = ("image", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Doubao"
    NODE_DISPLAY_NAME = "Seededit3"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model": (
                    ["doubao-seededit-3-0-i2i-250628"],
                    {"default": "doubao-seededit-3-0-i2i-250628"},
                ),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "guidance_scale": ("FLOAT", {"default": 5.5, "min": 1.0, "max": 10.0}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "doubao-seededit-3-0-i2i-250628")
        prompt = kwargs.get("prompt", "")
        image = kwargs.get("image", None)
        seed = kwargs.get("seed", -1)
        guidance_scale = kwargs.get("guidance_scale", 5.5)
        if image is None:
            raise ValueError("Image is required")
        # 上传图片
        image_url = self.upload_file(
            tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
            f"{prompt_id}.png",
            headers,
        )
        data = {
            "prompt": prompt,
            "model": model,
            "image": image_url,
            "seed": seed,
            "guidance_scale": guidance_scale,
            "size": "adaptive",
            "response_format": "url",
            "watermark": False,
        }
        return data, model

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class Seedance_1_0_T2V_API(BizyAirTrdApiBaseNode):
    RETURN_TYPES = (
        "VIDEO",
        """{"doubao-seedance-1-0-pro-250528": "doubao-seedance-1-0","doubao-seedance-1-0-pro-fast-251015": "doubao-seedance-1-0"}""",
    )
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Doubao"
    NODE_DISPLAY_NAME = "Seedance 1.0 Pro Text To Video"

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
                    [
                        "doubao-seedance-1-0-pro-250528",
                        "doubao-seedance-1-0-pro-fast-251015",
                    ],
                    {"default": "doubao-seedance-1-0-pro-250528"},
                ),
                "resolution": (
                    ["480p", "720p", "1080p"],
                    {
                        "default": "1080p",
                        "tooltip": "分辨率+比例共同决定视频尺寸，具体尺寸请参考官方文档说明",
                    },
                ),
                "ratio": (
                    ["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
                    {
                        "default": "adaptive",
                        "tooltip": "比例+分辨率共同决定视频尺寸，具体尺寸请参考官方文档说明",
                    },
                ),
                "duration": ("INT", {"default": 12, "min": 2, "max": 12}),
                "fps": (
                    [24],
                    {
                        "default": 24,
                        "tooltip": "帧率固定24",
                    },
                ),
                "camerafixed": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "平台可能在提示词中追加固定摄像机指令（效果不保证） ",
                    },
                ),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "doubao-seedance-1-0-pro-250528")
        prompt = kwargs.get("prompt", "")
        resolution = kwargs.get("resolution", "1080p")
        ratio = kwargs.get("ratio", "adaptive")
        duration = kwargs.get("duration", 12)
        camerafixed = kwargs.get("camerafixed", False)
        seed = kwargs.get("seed", -1)
        if prompt is None or prompt.strip() == "":
            raise ValueError("Prompt is required")
        data = {
            "prompt": prompt,
            "model": model,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "camerafixed": camerafixed,
            "seed": seed,
            "watermark": False,
            "fps": 24,
        }
        return data, "doubao-seedance-1-0"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Seedance_1_0_I2V_API(BizyAirTrdApiBaseNode):
    RETURN_TYPES = (
        "VIDEO",
        """{"doubao-seedance-1-0-pro-250528": "doubao-seedance-1-0","doubao-seedance-1-0-pro-fast-251015": "doubao-seedance-1-0"}""",
    )
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Doubao"
    NODE_DISPLAY_NAME = "Seedance 1.0 Pro Image To Video"

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
                    [
                        "doubao-seedance-1-0-pro-250528",
                        "doubao-seedance-1-0-pro-fast-251015",
                    ],
                    {"default": "doubao-seedance-1-0-pro-250528"},
                ),
                "resolution": (
                    ["480p", "720p", "1080p"],
                    {
                        "default": "1080p",
                        "tooltip": "分辨率+比例共同决定视频尺寸，具体尺寸请参考官方文档说明",
                    },
                ),
                "ratio": (
                    ["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
                    {
                        "default": "adaptive",
                        "tooltip": "比例+分辨率共同决定视频尺寸，具体尺寸请参考官方文档说明",
                    },
                ),
                "duration": ("INT", {"default": 12, "min": 2, "max": 12}),
                "fps": (
                    [24],
                    {
                        "default": 24,
                        "tooltip": "帧率固定24",
                    },
                ),
                "camerafixed": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "平台可能在提示词中追加固定摄像机指令（效果不保证） ",
                    },
                ),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
            "optional": {
                "last_frame_image": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model", "doubao-seedance-1-0-pro-250528")
        prompt = kwargs.get("prompt", "")
        resolution = kwargs.get("resolution", "1080p")
        ratio = kwargs.get("ratio", "adaptive")
        duration = kwargs.get("duration", 12)
        camerafixed = kwargs.get("camerafixed", False)
        seed = kwargs.get("seed", -1)
        first_frame_image = kwargs.get("first_frame_image", None)
        last_frame_image = kwargs.get("last_frame_image", None)
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        if (
            last_frame_image is not None
            and model == "doubao-seedance-1-0-pro-fast-251015"
        ):
            raise ValueError(
                "Last frame image is not supported for doubao-seedance-1-0-pro-fast-251015"
            )
        first_frame_image_url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}_first.png",
            headers,
        )
        data = {
            "prompt": prompt,
            "model": model,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "camerafixed": camerafixed,
            "seed": seed,
            "watermark": False,
            "fps": 24,
            "first_frame_image": first_frame_image_url,
        }
        if last_frame_image is not None:
            last_frame_image_url = self.upload_file(
                tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096),
                f"{prompt_id}_last.png",
                headers,
            )
            data["last_frame_image"] = last_frame_image_url
        return data, "doubao-seedance-1-0"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")
