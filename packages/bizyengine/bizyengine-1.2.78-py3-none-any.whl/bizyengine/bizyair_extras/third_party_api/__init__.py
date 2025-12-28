modules = [
    ".nodes_hailuo",
    ".nodes_gemini",
    ".nodes_gpt",
    ".nodes_kling",
    ".nodes_doubao",
    ".nodes_flux",
    ".nodes_sora",
    ".nodes_veo3",
    ".nodes_wan_api",
    ".nodes_vidu",
]
from bizyengine.core.common.utils import safe_star_import

for mod in modules:
    safe_star_import(mod, package=__package__)
