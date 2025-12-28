from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class VIDU_Q1_T2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Vidu Q1 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"vidu-q1-text2video": "vidu-q1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Vidu"

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
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "style": (["general", "anime"], {"default": "general"}),
                "duration": ([5], {"default": 5}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
                "resolution": (["1080p"], {"default": "1080p"}),
                "movement_amplitude": (
                    ["auto", "small", "medium", "large"],
                    {"default": "auto", "tooltip": "画面中物体的运动幅度。"},
                ),
                "bgm": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "当设置为 true 时，系统将自动添加合适的 BGM。BGM 无时长限制，系统会自动适配。",
                    },
                ),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        seed = kwargs.get("seed", 0)
        style = kwargs.get("style", "general")
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "1080p")
        movement_amplitude = kwargs.get("movement_amplitude", "auto")
        bgm = kwargs.get("bgm", False)
        if len(prompt) > 1500:
            raise ValueError("Prompt must be less than 1500 characters")
        data = {
            "prompt": prompt,
            "seed": seed,
            "style": style,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "movement_amplitude": movement_amplitude,
            "bgm": bgm,
            "model": "vidu-q1-text2video",
        }
        return data, "vidu-q1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class VIDU_Q1_I2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Vidu Q1 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"vidu-q1-img2video": "vidu-q1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Vidu"

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
                "first_frame_image": ("IMAGE",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "duration": ([5], {"default": 5}),
                "resolution": (["1080p"], {"default": "1080p"}),
                "movement_amplitude": (
                    ["auto", "small", "medium", "large"],
                    {"default": "auto", "tooltip": "画面中物体的运动幅度。"},
                ),
                "bgm": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "当设置为 true 时，系统将自动添加合适的 BGM。BGM 无时长限制，系统会自动适配。",
                    },
                ),
            },
            "optional": {
                "last_frame_image": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        seed = kwargs.get("seed", 0)
        duration = kwargs.get("duration", 5)
        resolution = kwargs.get("resolution", "1080p")
        movement_amplitude = kwargs.get("movement_amplitude", "auto")
        bgm = kwargs.get("bgm", False)
        first_frame_image = kwargs.get("first_frame_image", None)
        last_frame_image = kwargs.get("last_frame_image", None)
        if len(prompt) > 1500:
            raise ValueError("Prompt must be less than 1500 characters")
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        images = []
        total_size = 0
        model = "vidu-q1-img2video"
        # 上传首帧图片
        bio = tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096)
        length = bio.getbuffer().nbytes
        total_size += length
        if total_size > 50 * 1024 * 1024:
            raise ValueError(
                "Image size is too large, Vidu Q1 only supports images up to 50MB"
            )
        first_frame_image_url = self.upload_file(
            bio,
            f"{prompt_id}_first.png",
            headers,
        )
        images.append(first_frame_image_url)
        if last_frame_image is not None:
            # 上传末帧图片
            bio = tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096)
            length = bio.getbuffer().nbytes
            total_size += length
            if total_size > 50 * 1024 * 1024:
                raise ValueError(
                    "Image size is too large, Vidu Q1 only supports images up to 50MB"
                )
            last_frame_image_url = self.upload_file(
                bio,
                f"{prompt_id}_last.png",
                headers,
            )
            images.append(last_frame_image_url)
            model = "vidu-q1-startend2video"

        data = {
            "prompt": prompt,
            "seed": seed,
            "duration": duration,
            "resolution": resolution,
            "movement_amplitude": movement_amplitude,
            "bgm": bgm,
            "model": model,
            "images": images,
        }
        return data, "vidu-q1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class VIDU_Q1_I2V_REF_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Vidu Q1 Reference Images To Video"
    RETURN_TYPES = ("VIDEO", """{"vidu-q1-reference2video": "vidu-q1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Vidu"

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
                "ref_image_1": ("IMAGE",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "duration": ([5], {"default": 5}),
                "resolution": (["1080p"], {"default": "1080p"}),
                "movement_amplitude": (
                    ["auto", "small", "medium", "large"],
                    {"default": "auto", "tooltip": "画面中物体的运动幅度。"},
                ),
                "bgm": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "当设置为 true 时，系统将自动添加合适的 BGM。BGM 无时长限制，系统会自动适配。",
                    },
                ),
            },
            "optional": {
                "ref_image_2": ("IMAGE",),
                "ref_image_3": ("IMAGE",),
                "ref_image_4": ("IMAGE",),
                "ref_image_5": ("IMAGE",),
                "ref_image_6": ("IMAGE",),
                "ref_image_7": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        seed = kwargs.get("seed", 0)
        duration = kwargs.get("duration", 5)
        resolution = kwargs.get("resolution", "1080p")
        movement_amplitude = kwargs.get("movement_amplitude", "auto")
        bgm = kwargs.get("bgm", False)
        if len(prompt) > 1500:
            raise ValueError("Prompt must be less than 1500 characters")
        bios = []
        images = []
        total_size = 0
        # 上传图片
        for i, img in enumerate(
            [
                kwargs.get("ref_image_1", None),
                kwargs.get("ref_image_2", None),
                kwargs.get("ref_image_3", None),
                kwargs.get("ref_image_4", None),
                kwargs.get("ref_image_5", None),
                kwargs.get("ref_image_6", None),
                kwargs.get("ref_image_7", None),
            ],
            1,
        ):
            if img is not None:
                bio = tensor_to_bytesio(image=img, total_pixels=4096 * 4096)
                length = bio.getbuffer().nbytes
                total_size += length
                if total_size > 50 * 1024 * 1024:
                    raise ValueError(
                        "Image size is too large, Vidu Q1 only supports images up to 50MB"
                    )
                bios.append(bio)
        for i, bio in enumerate(bios):
            url = self.upload_file(
                bio,
                f"{prompt_id}_ref_{i+1}.png",
                headers,
            )
            images.append(url)

        data = {
            "prompt": prompt,
            "seed": seed,
            "duration": duration,
            "resolution": resolution,
            "movement_amplitude": movement_amplitude,
            "bgm": bgm,
            "model": "vidu-q1-reference2video",
            "images": images,
        }
        return data, "vidu-q1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")
