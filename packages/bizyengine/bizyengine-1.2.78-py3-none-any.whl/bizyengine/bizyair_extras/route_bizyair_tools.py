import json
import pprint

from aiohttp import web
from server import PromptServer

import bizyengine.core as bizyair
from bizyengine.core.common.env_var import BIZYAIR_DEBUG
from bizyengine.core.data_types import BIZYAIR_TYPE_MAP

# Invert BIZYAIR_TYPE_MAP for reverse lookup
INVERTED_BIZYAIR_TYPE_MAP = {v: k for k, v in BIZYAIR_TYPE_MAP.items()}

import importlib
import warnings

try:
    comfy_nodes = importlib.import_module("nodes")
except ModuleNotFoundError:
    warnings.warn("Importing comfyui.nodes failed!")
    comfy_nodes = type(
        "nodes",
        (object,),
        {"NODE_DISPLAY_NAME_MAPPINGS": {}, "NODE_CLASS_MAPPINGS": {}},
    )


def get_bizyair_display_name(class_type: str) -> str:
    bizyair_cls_prefix = bizyair.nodes_base.PREFIX
    bizyair_logo = bizyair.nodes_base.LOGO
    return f"{bizyair_logo}{bizyair_cls_prefix} {bizyair.NODE_DISPLAY_NAME_MAPPINGS.get(class_type, class_type)}"


def revert_bizyair_display_name(class_type: str) -> str:
    comfy_class_type = class_type[len(f"{bizyair.nodes_base.PREFIX}_") :]
    return comfy_nodes.NODE_DISPLAY_NAME_MAPPINGS.get(
        comfy_class_type, comfy_class_type
    )


def workflow_convert(inputs: dict, comfy2bizyair: bool = True):
    nodes = inputs["nodes"]
    for node in nodes:
        class_type = node["type"]
        node_inputs = node.get("inputs")
        node_outputs = node.get("outputs")
        is_converted = False

        # check if the node is a bizyair node
        new_class_type = class_type
        if not comfy2bizyair:
            if (
                len(class_type) > len(f"{bizyair.nodes_base.PREFIX}_")
                and class_type[len(f"{bizyair.nodes_base.PREFIX}_") :]
                in comfy_nodes.NODE_CLASS_MAPPINGS
            ):
                new_class_type = class_type[len(f"{bizyair.nodes_base.PREFIX}_") :]
        elif (
            comfy2bizyair
            and f"{bizyair.nodes_base.PREFIX}_{class_type}"
            in bizyair.NODE_CLASS_MAPPINGS
        ):
            new_class_type = f"{bizyair.nodes_base.PREFIX}_{class_type}"

        if new_class_type != class_type:
            node["type"] = new_class_type
            display_name = (
                get_bizyair_display_name(class_type)
                if comfy2bizyair
                else revert_bizyair_display_name(class_type)
            )
            node["properties"]["Node name for S&R"] = display_name

            type_mapping = (
                BIZYAIR_TYPE_MAP if comfy2bizyair else INVERTED_BIZYAIR_TYPE_MAP
            )
            if node_inputs:
                for input_node in node_inputs:
                    input_type = input_node["type"]
                    input_node["type"] = type_mapping.get(input_type, input_type)
            if node_outputs:
                for output_node in node_outputs:
                    output_type = output_node["type"]
                    output_node["type"] = type_mapping.get(output_type, output_type)

            is_converted = True

        if BIZYAIR_DEBUG:
            pprint.pprint(
                {
                    "original_class_type": class_type,
                    "new_class_type": new_class_type,
                    "is_converted": is_converted,
                }
            )

    return inputs


@PromptServer.instance.routes.post("/bizyair/node_converter")
async def convert(request):
    try:
        data = await request.json()
        comfy2bizyair = data.get("comfy2bizyair", True)
        ret = workflow_convert(data, comfy2bizyair=comfy2bizyair)

        # remove "comfy2bizyair" key from the response
        if "comfy2bizyair" in ret:
            del ret["comfy2bizyair"]

        return web.Response(
            text=json.dumps(ret),
            content_type="application/json",
        )
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)
