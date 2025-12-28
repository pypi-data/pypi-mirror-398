from bizyengine.core import BizyAirBaseNode


# Parse Text to BBox
class ParseQwenVLBBoxes(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (
                    [
                        "Qwen/Qwen2.5-VL-7B-Instruct",
                        "Qwen/Qwen2.5-VL-32B-Instruct",
                        "Qwen/Qwen2.5-VL-72B-Instruct",
                    ],
                ),
                "bboxes_text": ("STRING",),
                "image": ("IMAGE",),
                "target": ("STRING",),
                "bbox_selection": (
                    "STRING",
                    {
                        "default": "all",
                        "tooltip": "all或者逗号分隔的序列号",
                    },
                ),
                "merge_boxes": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("JSON", "BBOXES")
    RETURN_NAMES = ("text", "bboxes")
    CATEGORY = "Qwen2.5-VL"
    NODE_DISPLAY_NAME = "Parse Qwen VL BBoxes Text for SAM2"


# LayerMask Advance plugin
# class LayerMaskSAM2Ultra(BizyAirBaseNode):

#     def __init__(self):
#         self.NODE_NAME = "SAM2 Ultra"
#         pass

#     @classmethod
#     def INPUT_TYPES(cls):
#         sam2_model_list = [
#             "sam2_hiera_base_plus.safetensors",
#             "sam2_hiera_large.safetensors",
#             "sam2_hiera_small.safetensors",
#             "sam2_hiera_tiny.safetensors",
#             "sam2.1_hiera_base_plus.safetensors",
#             "sam2.1_hiera_large.safetensors",
#             "sam2.1_hiera_small.safetensors",
#             "sam2.1_hiera_tiny.safetensors",
#         ]
#         model_precision_list = ["fp16", "bf16", "fp32"]
#         select_list = ["all", "first", "by_index"]
#         method_list = [
#             "VITMatte",
#             "VITMatte(local)",
#             "PyMatting",
#             "GuidedFilter",
#         ]
#         device_list = ["cuda"]
#         return {
#             "required": {
#                 "image": ("IMAGE",),
#                 "bboxes": ("BBOXES",),
#                 "sam2_model": (sam2_model_list,),
#                 "precision": (model_precision_list,),
#                 "bbox_select": (select_list,),
#                 "select_index": (
#                     "STRING",
#                     {"default": "0,"},
#                 ),
#                 "cache_model": ("BOOLEAN", {"default": False}),
#                 "detail_method": (method_list,),
#                 "detail_erode": (
#                     "INT",
#                     {"default": 6, "min": 1, "max": 255, "step": 1},
#                 ),
#                 "detail_dilate": (
#                     "INT",
#                     {"default": 4, "min": 1, "max": 255, "step": 1},
#                 ),
#                 "black_point": (
#                     "FLOAT",
#                     {
#                         "default": 0.15,
#                         "min": 0.01,
#                         "max": 0.98,
#                         "step": 0.01,
#                         "display": "slider",
#                     },
#                 ),
#                 "white_point": (
#                     "FLOAT",
#                     {
#                         "default": 0.99,
#                         "min": 0.02,
#                         "max": 0.99,
#                         "step": 0.01,
#                         "display": "slider",
#                     },
#                 ),
#                 "process_detail": ("BOOLEAN", {"default": True}),
#                 "device": (device_list,),
#                 "max_megapixels": (
#                     "FLOAT",
#                     {"default": 2.0, "min": 1, "max": 999, "step": 0.1},
#                 ),
#             },
#             "optional": {},
#         }

#     RETURN_TYPES = (
#         "IMAGE",
#         "MASK",
#     )
#     RETURN_NAMES = (
#         "image",
#         "mask",
#     )
#     CATEGORY = "😺dzNodes/LayerMask"
#     NODE_DISPLAY_NAME = "LayerMask: SAM2 Ultra(Advance)"
#     CLASS_TYPE_NAME = "LayerMask: SAM2Ultra"


class LayerMaskLoadSAM2Model(BizyAirBaseNode):

    def __init__(self):
        self.NODE_NAME = "Load SAM2 Model"
        pass

    @classmethod
    def INPUT_TYPES(cls):
        sam2_model_list = [
            # "sam2_hiera_base_plus.safetensors",
            # "sam2_hiera_large.safetensors",
            # "sam2_hiera_small.safetensors",
            # "sam2_hiera_tiny.safetensors",
            "sam2.1_hiera_base_plus.safetensors",
            # "sam2.1_hiera_large.safetensors",
            # "sam2.1_hiera_small.safetensors",
            # "sam2.1_hiera_tiny.safetensors",
        ]
        model_precision_list = [
            # "fp16",
            "bf16",
            # "fp32"
        ]
        device_list = ["cuda"]
        return {
            "required": {
                "sam2_model": (sam2_model_list,),
                "precision": (model_precision_list,),
                "device": (device_list,),
            },
            "optional": {},
        }

    RETURN_TYPES = ("LS_SAM2_MODEL",)
    RETURN_NAMES = ("sam2_model",)
    CATEGORY = "😺dzNodes/LayerMask"
    NODE_DISPLAY_NAME = "LayerMask: Load SAM2 Model(Advance)"
    CLASS_TYPE_NAME = "LayerMask: LoadSAM2Model"


class LayerMaskSAM2UltraV2(BizyAirBaseNode):

    def __init__(self):
        self.NODE_NAME = "SAM2 Ultra V2"
        pass

    @classmethod
    def INPUT_TYPES(cls):

        select_list = ["all", "first", "by_index"]
        method_list = [
            "VITMatte",
            "VITMatte(local)",
            "PyMatting",
            "GuidedFilter",
        ]
        return {
            "required": {
                "sam2_model": ("LS_SAM2_MODEL",),
                "image": ("IMAGE",),
                "bboxes": ("BBOXES",),
                "bbox_select": (select_list,),
                "select_index": (
                    "STRING",
                    {"default": "0,"},
                ),
                "detail_method": (method_list,),
                "detail_erode": (
                    "INT",
                    {"default": 6, "min": 1, "max": 255, "step": 1},
                ),
                "detail_dilate": (
                    "INT",
                    {"default": 4, "min": 1, "max": 255, "step": 1},
                ),
                "black_point": (
                    "FLOAT",
                    {
                        "default": 0.15,
                        "min": 0.01,
                        "max": 0.98,
                        "step": 0.01,
                        "display": "slider",
                    },
                ),
                "white_point": (
                    "FLOAT",
                    {
                        "default": 0.99,
                        "min": 0.02,
                        "max": 0.99,
                        "step": 0.01,
                        "display": "slider",
                    },
                ),
                "process_detail": ("BOOLEAN", {"default": True}),
                "max_megapixels": (
                    "FLOAT",
                    {"default": 2.0, "min": 1, "max": 999, "step": 0.1},
                ),
            },
            "optional": {},
        }

    RETURN_TYPES = (
        "IMAGE",
        "MASK",
    )
    RETURN_NAMES = (
        "image",
        "mask",
    )
    CATEGORY = "😺dzNodes/LayerMask"
    NODE_DISPLAY_NAME = "LayerMask: SAM2 Ultra V2(Advance)"
    CLASS_TYPE_NAME = "LayerMask: SAM2UltraV2"


# class LayerMaskSAM2VideoUltra(BizyAirBaseNode):

#     def __init__(self):
#         self.NODE_NAME = "SAM2 Video Ultra"

#     @classmethod
#     def INPUT_TYPES(cls):
#         sam2_model_list = [
#             "sam2_hiera_base_plus.safetensors",
#             "sam2_hiera_large.safetensors",
#             "sam2_hiera_small.safetensors",
#             "sam2_hiera_tiny.safetensors",
#             "sam2.1_hiera_base_plus.safetensors",
#             "sam2.1_hiera_large.safetensors",
#             "sam2.1_hiera_small.safetensors",
#             "sam2.1_hiera_tiny.safetensors",
#         ]
#         model_precision_list = ["fp16", "bf16"]
#         method_list = ["VITMatte"]
#         device_list = ["cuda"]
#         return {
#             "required": {
#                 "image": ("IMAGE",),
#                 "sam2_model": (sam2_model_list,),
#                 "precision": (model_precision_list,),
#                 "cache_model": ("BOOLEAN", {"default": False}),
#                 "individual_objects": ("BOOLEAN", {"default": False}),
#                 "mask_preview_color": (
#                     "STRING",
#                     {"default": "#FF0080"},
#                 ),
#                 "detail_method": (method_list,),
#                 "detail_erode": (
#                     "INT",
#                     {"default": 6, "min": 1, "max": 255, "step": 1},
#                 ),
#                 "detail_dilate": (
#                     "INT",
#                     {"default": 4, "min": 1, "max": 255, "step": 1},
#                 ),
#                 "black_point": (
#                     "FLOAT",
#                     {
#                         "default": 0.15,
#                         "min": 0.01,
#                         "max": 0.98,
#                         "step": 0.01,
#                         "display": "slider",
#                     },
#                 ),
#                 "white_point": (
#                     "FLOAT",
#                     {
#                         "default": 0.99,
#                         "min": 0.02,
#                         "max": 0.99,
#                         "step": 0.01,
#                         "display": "slider",
#                     },
#                 ),
#                 "process_detail": ("BOOLEAN", {"default": True}),
#                 "device": (device_list,),
#                 "max_megapixels": (
#                     "FLOAT",
#                     {"default": 0.5, "min": 0.1, "max": 10, "step": 0.1},
#                 ),
#             },
#             "optional": {
#                 "bboxes": ("BBOXES",),
#                 "first_frame_mask": ("MASK",),
#                 "pre_mask": ("MASK",),
#             },
#         }

#     RETURN_TYPES = ("MASK", "IMAGE")
#     RETURN_NAMES = ("mask", "preview")
#     CATEGORY = "😺dzNodes/LayerMask"
#     NODE_DISPLAY_NAME = "LayerMask: SAM2 Video Ultra(Advance)"
#     CLASS_TYPE_NAME = "LayerMask: SAM2VideoUltra"
