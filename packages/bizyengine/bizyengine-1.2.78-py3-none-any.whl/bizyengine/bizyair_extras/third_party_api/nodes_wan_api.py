from bizyairsdk import tensor_to_bytesio

from bizyengine.bizyair_extras.utils.audio import save_audio

from .trd_nodes_base import BizyAirTrdApiBaseNode


class Wan_V2_5_I2V_API(BizyAirTrdApiBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "audio": ("AUDIO",),
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
                "resolution": (
                    ["480P", "720P", "1080P"],
                    {"default": "1080P"},
                ),
                "duration": ([5, 10], {"default": 5}),
                "prompt_extend": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否开启prompt智能改写。开启后使用大模型对输入prompt进行智能改写。对于较短的prompt生成效果提升明显，但会增加耗时。",
                    },
                ),
                "auto_audio": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否由模型自动生成声音，优先级低于audio参数。",
                    },
                ),
            },
        }

    NODE_DISPLAY_NAME = "Wan2.5 Image To Video"
    RETURN_TYPES = (
        "VIDEO",
        "STRING",
        """{"wan2.5-i2v-preview": "wan2.5-i2v-preview"}""",
    )
    RETURN_NAMES = ("video", "actual_prompt", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/WanVideo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        audio = kwargs.get("audio", None)
        resolution = kwargs.get("resolution", "1080P")
        duration = kwargs.get("duration", 5)
        prompt_extend = kwargs.get("prompt_extend", True)
        auto_audio = kwargs.get("auto_audio", True)
        image = kwargs.get("image", None)

        model = "wan2.5-i2v-preview"
        input = {
            "resolution": resolution,
            "prompt_extend": prompt_extend,
            "duration": duration,
            "audio": auto_audio,
            "model": model,
        }
        if prompt is not None and prompt.strip() != "":
            input["prompt"] = prompt
        if negative_prompt is not None and negative_prompt.strip() != "":
            input["negative_prompt"] = negative_prompt

        # 上传图片&音频
        if image is not None:
            image_url = self.upload_file(
                tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
                f"{prompt_id}.png",
                headers,
            )
            input["img_url"] = image_url
        if audio is not None:
            audio_url = self.upload_file(
                save_audio(audio=audio, format="mp3"), f"{prompt_id}.mp3", headers
            )
            input["audio_url"] = audio_url

        return input, model

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Wan_V2_5_T2V_API(BizyAirTrdApiBaseNode):
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
            },
            "optional": {
                "audio": ("AUDIO",),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "size": (
                    [
                        "832*480",
                        "480*832",
                        "624*624",
                        "1280*720",
                        "720*1280",
                        "960*960",
                        "1088*832",
                        "832*1088",
                        "1920*1080",
                        "1080*1920",
                        "1440*1440",
                        "1632*1248",
                        "1248*1632",
                    ],
                    {"default": "1920*1080"},
                ),
                "duration": ([5, 10], {"default": 5}),
                "prompt_extend": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否开启prompt智能改写。开启后使用大模型对输入prompt进行智能改写。对于较短的prompt生成效果提升明显，但会增加耗时。",
                    },
                ),
                "auto_audio": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否由模型自动生成声音，优先级低于audio参数。",
                    },
                ),
            },
        }

    NODE_DISPLAY_NAME = "Wan2.5 Text To Video"
    RETURN_TYPES = (
        "VIDEO",
        "STRING",
        """"{"wan2.5-t2v-preview": "wan2.5-t2v-preview"}""",
    )
    RETURN_NAMES = ("video", "actual_prompt", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/WanVideo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        model = "wan2.5-t2v-preview"
        negative_prompt = kwargs.get("negative_prompt", "")
        audio = kwargs.get("audio", None)
        size = kwargs.get("size", "1920*1080")
        duration = kwargs.get("duration", 5)
        prompt_extend = kwargs.get("prompt_extend", True)
        auto_audio = kwargs.get("auto_audio", True)
        prompt = kwargs.get("prompt", "")

        input = {
            "size": size,
            "prompt_extend": prompt_extend,
            "duration": duration,
            "audio": auto_audio,
            "model": model,
        }
        if prompt is not None and prompt.strip() != "":
            input["prompt"] = prompt
        if negative_prompt is not None and negative_prompt.strip() != "":
            input["negative_prompt"] = negative_prompt

        # 上传音频
        if audio is not None:
            audio_url = self.upload_file(
                save_audio(audio=audio, format="mp3"), f"{prompt_id}.mp3", headers
            )
            input["audio_url"] = audio_url

        return input, model

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Wan_V2_6_I2V_API(BizyAirTrdApiBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "audio": ("AUDIO",),
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
                "resolution": (
                    ["720P", "1080P"],
                    {"default": "1080P"},
                ),
                "duration": ([5, 10, 15], {"default": 5}),
                "prompt_extend": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否开启prompt智能改写。开启后使用大模型对输入prompt进行智能改写。对于较短的prompt生成效果提升明显，但会增加耗时。",
                    },
                ),
                "shot_type": (
                    ["single", "multi"],
                    {
                        "default": "single",
                        "tooltip": "指定生成视频的镜头类型，即视频是由一个连续镜头还是多个切换镜头组成。仅当prompt_extend: true时生效",
                    },
                ),
                "auto_audio": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否由模型自动生成声音，优先级低于audio参数。",
                    },
                ),
            },
        }

    NODE_DISPLAY_NAME = "Wan2.6 Image To Video"
    RETURN_TYPES = ("VIDEO", "STRING", """{"wan2.6-i2v": "wan2.6-i2v"}""")
    RETURN_NAMES = ("video", "actual_prompt", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/WanVideo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        audio = kwargs.get("audio", None)
        resolution = kwargs.get("resolution", "1080P")
        duration = kwargs.get("duration", 5)
        prompt_extend = kwargs.get("prompt_extend", True)
        shot_type = kwargs.get("shot_type", "single")
        auto_audio = kwargs.get("auto_audio", True)
        image = kwargs.get("image", None)

        model = "wan2.6-i2v"
        input = {
            "resolution": resolution,
            "prompt_extend": prompt_extend,
            "duration": duration,
            "audio": auto_audio,
            "model": model,
            "shot_type": shot_type,
        }
        if prompt is not None and prompt.strip() != "":
            input["prompt"] = prompt
        if negative_prompt is not None and negative_prompt.strip() != "":
            input["negative_prompt"] = negative_prompt

        # 上传图片&音频
        if image is not None:
            image_url = self.upload_file(
                tensor_to_bytesio(image=image, total_pixels=4096 * 4096),
                f"{prompt_id}.png",
                headers,
            )
            input["img_url"] = image_url
        if audio is not None:
            audio_url = self.upload_file(
                save_audio(audio=audio, format="mp3"), f"{prompt_id}.mp3", headers
            )
            input["audio_url"] = audio_url

        return input, model

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")


class Wan_V2_6_T2V_API(BizyAirTrdApiBaseNode):
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
            },
            "optional": {
                "audio": ("AUDIO",),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                "size": (
                    [
                        "1280*720",
                        "720*1280",
                        "960*960",
                        "1088*832",
                        "832*1088",
                        "1920*1080",
                        "1080*1920",
                        "1440*1440",
                        "1632*1248",
                        "1248*1632",
                    ],
                    {"default": "1920*1080"},
                ),
                "duration": ([5, 10, 15], {"default": 5}),
                "prompt_extend": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否开启prompt智能改写。开启后使用大模型对输入prompt进行智能改写。对于较短的prompt生成效果提升明显，但会增加耗时。",
                    },
                ),
                "shot_type": (
                    ["single", "multi"],
                    {
                        "default": "single",
                        "tooltip": "指定生成视频的镜头类型，即视频是由一个连续镜头还是多个切换镜头组成。仅当prompt_extend: true时生效",
                    },
                ),
                "auto_audio": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "是否由模型自动生成声音，优先级低于audio参数。",
                    },
                ),
            },
        }

    NODE_DISPLAY_NAME = "Wan2.6 Text To Video"
    RETURN_TYPES = ("VIDEO", "STRING", """{"wan2.6-t2v": "wan2.6-t2v"}""")
    RETURN_NAMES = ("video", "actual_prompt", "bizyair_model_name")
    CATEGORY = "☁️BizyAir/External APIs/WanVideo"

    def handle_inputs(self, headers, prompt_id, **kwargs):
        # 参数
        model = "wan2.6-t2v"
        negative_prompt = kwargs.get("negative_prompt", "")
        audio = kwargs.get("audio", None)
        size = kwargs.get("size", "1920*1080")
        duration = kwargs.get("duration", 5)
        prompt_extend = kwargs.get("prompt_extend", True)
        shot_type = kwargs.get("shot_type", "single")
        auto_audio = kwargs.get("auto_audio", True)
        prompt = kwargs.get("prompt", "")

        input = {
            "size": size,
            "prompt_extend": prompt_extend,
            "duration": duration,
            "audio": auto_audio,
            "model": model,
            "shot_type": shot_type,
        }
        if prompt is not None and prompt.strip() != "":
            input["prompt"] = prompt
        if negative_prompt is not None and negative_prompt.strip() != "":
            input["negative_prompt"] = negative_prompt

        # 上传音频
        if audio is not None:
            audio_url = self.upload_file(
                save_audio(audio=audio, format="mp3"), f"{prompt_id}.mp3", headers
            )
            input["audio_url"] = audio_url

        return input, model

    def handle_outputs(self, outputs):
        return (outputs[0][0], "")
