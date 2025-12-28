from bizyengine.core import BizyAirBaseNode


class WanImageToVideo(BizyAirBaseNode):
    MAX_RESOLUTION = 960

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "vae": ("VAE",),
                "width": (
                    "INT",
                    {"default": 832, "min": 16, "max": s.MAX_RESOLUTION, "step": 16},
                ),
                "height": (
                    "INT",
                    {"default": 480, "min": 16, "max": s.MAX_RESOLUTION, "step": 16},
                ),
                "length": (
                    "INT",
                    {"default": 81, "min": 1, "max": s.MAX_RESOLUTION, "step": 4},
                ),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096}),
            },
            "optional": {
                "clip_vision_output": ("CLIP_VISION_OUTPUT",),
                "start_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("positive", "negative", "latent")
    CATEGORY = "WanI2V"
    # FUNCTION = "encode"


class Wan_Model_Loader(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (("Wan2.1-T2V-1.3B",),),
            }
        }

    RETURN_TYPES = ("WAN_MODEL",)
    RETURN_NAMES = ("model",)
    CATEGORY = "WanT2V"


class Wan_T2V_Pipeline(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("WAN_MODEL",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Two anthropomorphic cats in comfy boxing gear and bright gloves fight intensely on a spotlighted stage.",
                    },
                ),
                "resolution": (
                    ["480*832", "832*480", "624*624", "704*544", "544*704"],
                    {"default": "480*832"},
                ),
                "sampling_steps": ("INT", {"default": 50, "min": 1, "max": 50}),
                "guidance_scale": ("FLOAT", {"default": 6.0, "min": 0, "max": 20}),
                "shift_scale": ("FLOAT", {"default": 8.0, "min": 0, "max": 20}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFFFFFFFFFF}),
                "negative_prompt": (
                    "STRING",
                    {"multiline": True, "default": "Low quality, blurry"},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_url",)
    CATEGORY = "WanT2V"
    # FUNCTION = "generate_video"
