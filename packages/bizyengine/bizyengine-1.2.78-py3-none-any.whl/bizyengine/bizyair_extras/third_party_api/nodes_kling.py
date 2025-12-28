import io

from bizyairsdk import tensor_to_bytesio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Kling_2_1_T2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2.1 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-v2-1-master": "kling-v2-1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model_name": (["kling-v2-1-master"], {"default": "kling-v2-1-master"}),
                "duration": ([5, 10], {"default": 5}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
            }
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2-1-master")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        if prompt is None or prompt.strip() == "":
            raise ValueError("Prompt is required")
        if len(prompt) > 2500 or len(negative_prompt) > 2500:
            raise ValueError(
                "Prompt and negative prompt must be less than 2500 characters"
            )
        data = {
            "model_name": model,
            "negative_prompt": negative_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "prompt": prompt,
        }
        return data, "kling-v2-1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_2_1_I2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2.1 Image To Video"
    RETURN_TYPES = (
        "VIDEO",
        """{"kling-v2-1-std": "kling-v2-1","kling-v2-1-pro": "kling-v2-1","kling-v2-1-master": "kling-v2-1"}""",
    )
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame_image": ("IMAGE", {"tooltip": "首帧图片"}),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model_name": (
                    ["kling-v2-1-std", "kling-v2-1-pro", "kling-v2-1-master"],
                    {"default": "kling-v2-1-std"},
                ),
                "duration": ([5, 10], {"default": 5}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
            },
            "optional": {
                "last_frame_image": ("IMAGE", {"tooltip": "末帧图片，只有pro支持"}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2-1-std")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        first_frame_image = kwargs.get("first_frame_image", None)
        last_frame_image = kwargs.get("last_frame_image", None)
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        if len(prompt) > 2500 or len(negative_prompt) > 2500:
            raise ValueError(
                "Prompt and negative prompt must be less than 2500 characters"
            )
        # 上传图片
        url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}_first.png",
            headers,
        )
        data = {
            "model_name": model,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "first_frame_image": url,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        if last_frame_image is not None:
            last_frame_image_url = self.upload_file(
                tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096),
                f"{prompt_id}_last.png",
                headers,
            )
            data["last_frame_image"] = last_frame_image_url
        return data, "kling-v2-1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


# class Kling_2_1_PRO_I2V_API(BizyAirTrdApiBaseNode):
#     NODE_DISPLAY_NAME = "Kling 2.1 Pro Image To Video"
#     RETURN_TYPES = ("VIDEO",)
#     RETURN_NAMES = ("video",)
#     CATEGORY = "☁️BizyAir/External APIs/Kling"

#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "first_frame_image": ("IMAGE", {"tooltip": "首帧图片"}),
#                 "prompt": (
#                     "STRING",
#                     {
#                         "multiline": True,
#                         "default": "",
#                     },
#                 ),
#                 "negative_prompt": (
#                     "STRING",
#                     {
#                         "multiline": True,
#                         "default": "",
#                     },
#                 ),
#                 "model_name": (["kling-v2-1", "kling-v2-1-master"], {"default": "kling-v2-1"}),
#                 "duration": ([5, 10], {"default": 5}),
#                 "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
#             },
#             "optional": {
#                 "last_frame_image": ("IMAGE", {"tooltip": "末帧图片"}),
#             },
#         }

#     def handle_inputs(self, headers, prompt_id, **kwargs):
#         model = kwargs.get("model_name", "kling-v2-1")
#         prompt = kwargs.get("prompt", "")
#         negative_prompt = kwargs.get("negative_prompt", "")
#         duration = kwargs.get("duration", 5)
#         aspect_ratio = kwargs.get("aspect_ratio", "16:9")
#         first_frame_image = kwargs.get("first_frame_image", None)
#         last_frame_image = kwargs.get("last_frame_image", None)
#         if first_frame_image is None:
#             raise ValueError("First frame image is required")
#         if len(prompt) > 2500 or len(negative_prompt) > 2500:
#             raise ValueError("Prompt and negative prompt must be less than 2500 characters")
#         # 上传图片
#         first_frame_image_url = self.upload_file(
#             tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
#             f"{prompt_id}_first.png",
#             headers,
#         )
#         data = {
#             "model_name": model,
#             "prompt": prompt,
#             "negative_prompt": negative_prompt,
#             "first_frame_image": first_frame_image_url,
#             "duration": duration,
#             "aspect_ratio": aspect_ratio,
#         }
#         if model == "kling-v2-1":
#             data["mode"] = "pro"
#         if last_frame_image is not None:
#             last_frame_image_url = self.upload_file(
#                 tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096),
#                 f"{prompt_id}_last.png",
#                 headers,
#             )
#             data["last_frame_image"] = last_frame_image_url
#         return data, model

#     def handle_outputs(self, outputs):
#         return (outputs[0][0],)


class Kling_2_5_I2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2.5 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-v2-5-turbo": "kling-v2-5"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame_image": ("IMAGE", {"tooltip": "首帧图片"}),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model_name": (["kling-v2-5-turbo"], {"default": "kling-v2-5-turbo"}),
                "duration": ([5, 10], {"default": 5}),
            },
            "optional": {
                "last_frame_image": ("IMAGE", {"tooltip": "末帧图片"}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2-5-turbo")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        duration = kwargs.get("duration", 5)
        first_frame_image = kwargs.get("first_frame_image", None)
        last_frame_image = kwargs.get("last_frame_image", None)
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        if len(prompt) > 2500 or len(negative_prompt) > 2500:
            raise ValueError(
                "Prompt and negative prompt must be less than 2500 characters"
            )
        # 上传图片
        url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}_first.png",
            headers,
        )
        data = {
            "model_name": model,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration": duration,
            "first_frame_image": url,
        }
        if last_frame_image is not None:
            last_frame_image_url = self.upload_file(
                tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096),
                f"{prompt_id}_last.png",
                headers,
            )
            data["last_frame_image"] = last_frame_image_url
        return data, "kling-v2-5"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_2_6_T2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2.6 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-v2-6": "kling-v2-6"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "sound": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "是否开启声音",
                    },
                ),
                "model_name": (["kling-v2-6"], {"default": "kling-v2-6"}),
                "duration": ([5, 10], {"default": 5}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2-6")
        prompt = kwargs.get("prompt", "")
        sound = kwargs.get("sound", False)
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        if len(prompt) > 1000:
            raise ValueError("Prompt must be less than 1000 characters")
        data = {
            "model_name": model,
            "prompt": prompt,
            "sound": sound,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        return data, "kling-v2-6"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_2_6_I2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2.6 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-v2-6": "kling-v2-6"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame_image": ("IMAGE", {"tooltip": "首帧图片"}),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "sound": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "是否开启声音",
                    },
                ),
                "model_name": (["kling-v2-6"], {"default": "kling-v2-6"}),
                "duration": ([5, 10], {"default": 5}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2-6")
        prompt = kwargs.get("prompt", "")
        sound = kwargs.get("sound", False)
        duration = kwargs.get("duration", 5)
        first_frame_image = kwargs.get("first_frame_image", None)
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        if len(prompt) > 1000:
            raise ValueError("Prompt must be less than 1000 characters")
        # 上传图片
        url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}.png",
            headers,
        )
        data = {
            "model_name": model,
            "prompt": prompt,
            "sound": sound,
            "duration": duration,
            "urls": [url],
        }
        return data, "kling-v2-6"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_2_T2I_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2 Text To Image"
    RETURN_TYPES = ("IMAGE", """{"kling-v2": "kling-v2"}""")
    RETURN_NAMES = ("images", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model_name": (["kling-v2"], {"default": "kling-v2"}),
                "aspect_ratio": (
                    ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3", "21:9"],
                    {"default": "16:9"},
                ),
                "resolution": (["1K", "2K"], {"default": "1K"}),
                "variants": ("INT", {"default": 1, "min": 1, "max": 9}),
                "image_fidelity": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "1K").lower()
        variants = kwargs.get("variants", 1)
        image_fidelity = kwargs.get("image_fidelity", 0.5)
        if len(prompt) > 2500 or len(negative_prompt) > 2500:
            raise ValueError(
                "Prompt and negative prompt must be less than 2500 characters"
            )
        data = {
            "model_name": model,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "variants": variants,
            "image_fidelity": image_fidelity,
        }
        return data, "kling-v2"

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class Kling_2_I2I_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling 2 Image To Image"
    RETURN_TYPES = ("IMAGE", """{"kling-v2": "kling-v2"}""")
    RETURN_NAMES = ("images", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "输入图片"}),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "model_name": (["kling-v2"], {"default": "kling-v2"}),
                "aspect_ratio": (
                    ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3", "21:9"],
                    {"default": "16:9"},
                ),
                "resolution": (["1K"], {"default": "1K"}),
                "variants": ("INT", {"default": 1, "min": 1, "max": 9}),
                "image_fidelity": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        model = kwargs.get("model_name", "kling-v2")
        prompt = kwargs.get("prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "1K").lower()
        variants = kwargs.get("variants", 1)
        image = kwargs.get("image", None)
        image_fidelity = kwargs.get("image_fidelity", 0.5)
        if image is None:
            raise ValueError("Image is required")
        if len(prompt) > 2500:
            raise ValueError("Prompt must be less than 2500 characters")
        # 上传图片
        image_url = self.upload_file(
            tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
            f"{prompt_id}.png",
            headers,
        )
        data = {
            "model_name": model,
            "prompt": prompt,
            "image": image_url,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "variants": variants,
            "image_fidelity": image_fidelity,
        }
        return data, "kling-v2"

    def handle_outputs(self, outputs):
        images = self.combine_images(outputs[1])
        return (images, "")


class Kling_O1_T2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling O1 Text To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-o1-t2v": "kling-o1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "duration": ([5, 10], {"default": 5}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        data = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "model": "kling-o1-t2v",
        }
        return data, "kling-o1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_O1_I2V_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling O1 Image To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-o1-i2v": "kling-o1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "duration": ([5, 10], {"default": 5}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
            },
            "optional": {
                "last_frame_image": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        first_frame_image = kwargs.get("first_frame_image", None)
        last_frame_image = kwargs.get("last_frame_image", None)
        if first_frame_image is None:
            raise ValueError("First frame image is required")
        # 上传图片
        first_frame_image_url = self.upload_file(
            tensor_to_bytesio(image=first_frame_image, total_pixels=4096 * 4096),
            f"{prompt_id}_first.png",
            headers,
        )

        data = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "model": "kling-o1-i2v",
            "first_frame_image": first_frame_image_url,
        }
        if last_frame_image is not None:
            # 上传末帧图片
            last_frame_image_url = self.upload_file(
                tensor_to_bytesio(image=last_frame_image, total_pixels=4096 * 4096),
                f"{prompt_id}_last.png",
                headers,
            )
            data["last_frame_image"] = last_frame_image_url
        return data, "kling-o1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_O1_VI2V_REF_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling O1 Reference Video/Images To Video"
    RETURN_TYPES = ("VIDEO", """{"kling-o1-ref2v": "kling-o1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "duration": ("INT", {"default": 5, "min": 3, "max": 10}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
                "keep_original_sound": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "选择是否通过参数保留视频原始声音"},
                ),
            },
            "optional": {
                "ref_image_1": ("IMAGE",),
                "ref_image_2": ("IMAGE",),
                "ref_image_3": ("IMAGE",),
                "ref_image_4": ("IMAGE",),
                "ref_image_5": ("IMAGE",),
                "ref_image_6": ("IMAGE",),
                "ref_image_7": ("IMAGE",),
                "ref_video": ("VIDEO",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        duration = kwargs.get("duration", 5)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        keep_original_sound = kwargs.get("keep_original_sound", False)
        ref_video = kwargs.get("ref_video", None)
        # 上传图片
        images = []
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
                url = self.upload_file(
                    tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                    f"{prompt_id}_ref_{i+1}.png",
                    headers,
                )
                images.append(url)

        data = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "keep_original_sound": keep_original_sound,
            "model": "kling-o1-ref2v",
        }
        if len(images) > 0:
            data["images"] = images

        if ref_video is not None:
            video_bytes_io = io.BytesIO()
            format_to_use = getattr(ref_video, "container", "mp4")
            codec_to_use = getattr(ref_video, "codec", "h264")
            ref_video.save_to(video_bytes_io, format=format_to_use, codec=codec_to_use)
            video_bytes_io.seek(0)
            ref_video_url = self.upload_file(
                video_bytes_io,
                f"{prompt_id}_ref_video.{format_to_use}",
                headers,
            )
            data["video"] = ref_video_url
        return data, "kling-o1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Kling_O1_VIDEO_EDIT_API(BizyAirTrdApiBaseNode):
    NODE_DISPLAY_NAME = "Kling O1 Video Edit"
    RETURN_TYPES = ("VIDEO", """{"kling-o1-video-edit": "kling-o1"}""")
    RETURN_NAMES = ("video", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/Kling"

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
                "ref_video": ("VIDEO",),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
                "keep_original_sound": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "选择是否通过参数保留视频原始声音"},
                ),
                "fast_mode": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "选择是否使用快速模式"},
                ),
            },
            "optional": {
                "ref_image_1": ("IMAGE",),
                "ref_image_2": ("IMAGE",),
                "ref_image_3": ("IMAGE",),
                "ref_image_4": ("IMAGE",),
            },
        }

    def handle_inputs(self, headers, prompt_id, **kwargs):
        prompt = kwargs.get("prompt", "")
        fast_mode = kwargs.get("fast_mode", False)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        keep_original_sound = kwargs.get("keep_original_sound", False)
        ref_video = kwargs.get("ref_video", None)
        if ref_video is None:
            raise ValueError("Reference video is required")
        # 上传图片
        images = []
        for i, img in enumerate(
            [
                kwargs.get("ref_image_1", None),
                kwargs.get("ref_image_2", None),
                kwargs.get("ref_image_3", None),
                kwargs.get("ref_image_4", None),
            ],
            1,
        ):
            if img is not None:
                url = self.upload_file(
                    tensor_to_bytesio(image=img, total_pixels=4096 * 4096),
                    f"{prompt_id}_ref_{i+1}.png",
                    headers,
                )
                images.append(url)
        # 上传视频
        video_bytes_io = io.BytesIO()
        format_to_use = getattr(ref_video, "container", "mp4")
        codec_to_use = getattr(ref_video, "codec", "h264")
        ref_video.save_to(video_bytes_io, format=format_to_use, codec=codec_to_use)
        video_bytes_io.seek(0)
        ref_video_url = self.upload_file(
            video_bytes_io,
            f"{prompt_id}_ref_video.{format_to_use}",
            headers,
        )

        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "keep_original_sound": keep_original_sound,
            "fast_mode": fast_mode,
            "model": "kling-o1-video-edit",
            "video": ref_video_url,
        }
        if len(images) > 0:
            data["images"] = images
        return data, "kling-o1"

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")
