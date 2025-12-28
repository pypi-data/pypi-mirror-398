from bizyengine.core import BizyAirBaseNode, pop_api_key_and_prompt_id

_FACERESTORE_MODELS = [
    "none",
    "codeformer-v0.1.0.pth",
    # "GFPGANv1.3.onnx",
    # "GFPGANv1.3.pth",
    "GFPGANv1.4.onnx",
    # "GFPGANv1.4.pth",
    # "GPEN-BFR-512.onnx",
    # "GPEN-BFR-1024.onnx",
    "GPEN-BFR-2048.onnx",
    "RestoreFormer_PP.onnx",
]


class reactor(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "enabled": (
                    "BOOLEAN",
                    {"default": True, "label_off": "OFF", "label_on": "ON"},
                ),
                "input_image": ("IMAGE",),
                "swap_model": (["inswapper_128.onnx"],),
                "facedetection": (
                    [
                        "retinaface_resnet50",
                        "retinaface_mobile0.25",
                        "YOLOv5l",
                        "YOLOv5n",
                    ],
                ),
                "face_restore_model": (_FACERESTORE_MODELS,),
                "face_restore_visibility": (
                    "FLOAT",
                    {"default": 1, "min": 0.1, "max": 1, "step": 0.05},
                ),
                "codeformer_weight": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1, "step": 0.05},
                ),
                "detect_gender_input": (["no", "female", "male"], {"default": "no"}),
                "detect_gender_source": (["no", "female", "male"], {"default": "no"}),
                "input_faces_index": ("STRING", {"default": "0"}),
                "source_faces_index": ("STRING", {"default": "0"}),
                "console_log_level": ([0, 1, 2], {"default": 1}),
            },
            "optional": {
                "source_image": ("IMAGE",),
                # "face_model": ("FACE_MODEL",),
                "face_boost": ("FACE_BOOST",),
            },
            "hidden": {"faces_order": "FACES_ORDER"},
        }

    RETURN_TYPES = (
        "IMAGE",
        # "FACE_MODEL",
        "BIZYAIR_PLACEHOLDER",
        "IMAGE",
    )
    RETURN_NAMES = (
        "SWAPPED_IMAGE",
        # "FACE_MODEL",
        "BIZYAIR_PLACEHOLDER",
        "ORIGINAL_IMAGE",
    )
    CATEGORY = "🌌 ReActor"
    CLASS_TYPE_NAME = "ReActorFaceSwap"
    NODE_DISPLAY_NAME = "ReActor 🌌 Fast Face Swap"
    FUNCTION = "execute"

    def execute(self, **kwargs):
        extra_data = pop_api_key_and_prompt_id(kwargs)
        class_type = self._determine_class_type()
        node_ios = self._process_non_send_request_types(class_type, kwargs)
        return self._process_all_send_request_types(node_ios, **extra_data)


class ReActorPlusOpt(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "enabled": (
                    "BOOLEAN",
                    {"default": True, "label_off": "OFF", "label_on": "ON"},
                ),
                "input_image": ("IMAGE",),
                "swap_model": (["inswapper_128.onnx"],),
                "facedetection": (
                    [
                        "retinaface_resnet50",
                        "retinaface_mobile0.25",
                        "YOLOv5l",
                        "YOLOv5n",
                    ],
                ),
                "face_restore_model": (_FACERESTORE_MODELS,),
                "face_restore_visibility": (
                    "FLOAT",
                    {"default": 1, "min": 0.1, "max": 1, "step": 0.05},
                ),
                "codeformer_weight": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1, "step": 0.05},
                ),
            },
            "optional": {
                "source_image": ("IMAGE",),
                # "face_model": ("FACE_MODEL",),
                "options": ("OPTIONS",),
                "face_boost": ("FACE_BOOST",),
            },
        }

    RETURN_TYPES = (
        "IMAGE",
        # "FACE_MODEL",
        "BIZYAIR_PLACEHOLDER",
        "IMAGE",
    )
    RETURN_NAMES = (
        "SWAPPED_IMAGE",
        # "FACE_MODEL",
        "BIZYAIR_PLACEHOLDER",
        "ORIGINAL_IMAGE",
    )
    CATEGORY = "🌌 ReActor"
    NODE_DISPLAY_NAME = "ReActor 🌌 Fast Face Swap [OPTIONS]"
    CLASS_TYPE_NAME = "ReActorFaceSwapOpt"
    FUNCTION = "execute"

    def execute(self, **kwargs):
        extra_data = pop_api_key_and_prompt_id(kwargs)
        class_type = self._determine_class_type()
        node_ios = self._process_non_send_request_types(class_type, kwargs)
        return self._process_all_send_request_types(node_ios, **extra_data)


class RestoreFace(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "facedetection": (
                    [
                        "retinaface_resnet50",
                        "retinaface_mobile0.25",
                        "YOLOv5l",
                        "YOLOv5n",
                    ],
                ),
                "model": (_FACERESTORE_MODELS,),
                "visibility": (
                    "FLOAT",
                    {"default": 1, "min": 0.0, "max": 1, "step": 0.05},
                ),
                "codeformer_weight": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1, "step": 0.05},
                ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    CATEGORY = "🌌 ReActor"
    CLASS_TYPE_NAME = "ReActorRestoreFace"
    NODE_DISPLAY_NAME = "Restore Face 🌌 ReActor"


class ReActorOptions(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_faces_order": (
                    [
                        "left-right",
                        "right-left",
                        "top-bottom",
                        "bottom-top",
                        "small-large",
                        "large-small",
                    ],
                    {"default": "large-small"},
                ),
                "input_faces_index": ("STRING", {"default": "0"}),
                "detect_gender_input": (["no", "female", "male"], {"default": "no"}),
                "source_faces_order": (
                    [
                        "left-right",
                        "right-left",
                        "top-bottom",
                        "bottom-top",
                        "small-large",
                        "large-small",
                    ],
                    {"default": "large-small"},
                ),
                "source_faces_index": ("STRING", {"default": "0"}),
                "detect_gender_source": (["no", "female", "male"], {"default": "no"}),
                "console_log_level": ([0, 1, 2], {"default": 1}),
            }
        }

    RETURN_TYPES = ("OPTIONS",)
    CATEGORY = "🌌 ReActor"
    CLASS_TYPE_NAME = "ReActorOptions"
    NODE_DISPLAY_NAME = "ReActor 🌌 Options"


class ReActorFaceBoost(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "enabled": (
                    "BOOLEAN",
                    {"default": True, "label_off": "OFF", "label_on": "ON"},
                ),
                "boost_model": (_FACERESTORE_MODELS,),
                "interpolation": (
                    ["Nearest", "Bilinear", "Bicubic", "Lanczos"],
                    {"default": "Bicubic"},
                ),
                "visibility": (
                    "FLOAT",
                    {"default": 1, "min": 0.1, "max": 1, "step": 0.05},
                ),
                "codeformer_weight": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1, "step": 0.05},
                ),
                "restore_with_main_after": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("FACE_BOOST",)
    CATEGORY = "🌌 ReActor"
    CLASS_TYPE_NAME = "ReActorFaceBoost"
    NODE_DISPLAY_NAME = "ReActor 🌌 Face Booster"
