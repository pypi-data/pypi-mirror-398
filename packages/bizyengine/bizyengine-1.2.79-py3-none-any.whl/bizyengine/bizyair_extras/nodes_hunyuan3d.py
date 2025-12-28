from bizyengine.core import BizyAirBaseNode


class Hy3D_2_1SimpleMeshGen(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": (["hunyuan3d-dit-v2-1/model.fp16.ckpt"],),
                "image": ("IMAGE", {"tooltip": "Image to generate mesh from"}),
                "steps": (
                    "INT",
                    {
                        "default": 50,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Number of diffusion steps",
                    },
                ),
                "guidance_scale": (
                    "FLOAT",
                    {
                        "default": 5.0,
                        "min": 1,
                        "max": 30,
                        "step": 0.1,
                        "tooltip": "Guidance scale",
                    },
                ),
                "octree_resolution": (
                    "INT",
                    {
                        "default": 384,
                        "min": 32,
                        "max": 1024,
                        "step": 32,
                        "tooltip": "Octree resolution",
                    },
                ),
            },
        }

    RETURN_TYPES = ("TRIMESH",)
    RETURN_NAMES = ("trimesh",)
    # FUNCTION = "loadmodel"
    CATEGORY = "Hunyuan3DWrapper"


class Hy3DExportMesh(BizyAirBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "trimesh": ("TRIMESH",),
                "filename_prefix": ("STRING", {"default": "3D/Hy3D"}),
                "file_format": (["glb", "obj", "ply", "stl", "3mf", "dae"],),
            },
            "optional": {
                "save_file": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("glb_path",)
    # FUNCTION = "process"
    CATEGORY = "Hunyuan3DWrapper"
    # OUTPUT_NODE = True
