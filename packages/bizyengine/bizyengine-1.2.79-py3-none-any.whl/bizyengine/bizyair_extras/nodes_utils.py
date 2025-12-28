import os
import uuid

import folder_paths
import requests

from bizyengine.core import BizyAirBaseNode


def get_incremented_filename(file_path):
    """
    Generate a unique filename by appending an incremental counter if needed.
    Format: <base>_<5-digit-counter>.<extension> (e.g., data_00001.txt)
    """
    # If the file doesn't exist, return the original path
    if not os.path.exists(file_path):
        return file_path

    # Split the path into directory, base filename, and extension
    directory, fullname = os.path.split(file_path)
    base, extension = os.path.splitext(fullname)

    # Handle files without extensions
    if not extension:
        base = fullname

    # Start counter at 1 and increment until a unique name is found
    counter = 1
    while counter <= 99999:
        # Format counter as 5-digit string (e.g., 00001)
        counter_str = f"_{counter:05d}"
        new_fullname = f"{base}{counter_str}{extension}"
        new_path = os.path.join(directory, new_fullname)

        if not os.path.exists(new_path):
            return new_path

        counter += 1

    raise RuntimeError("Failed to generate unique filename after 99999 attempts")


class BizyAirDownloadFile(BizyAirBaseNode):
    NODE_DISPLAY_NAME = "☁️BizyAir Download File"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"default": ""}),
                "folder": ("STRING", {"default": "bizyair"}),
                "file_name": ("STRING", {"default": "default.glb"}),
            }
        }

    CATEGORY = "☁️BizyAir/Utils"
    FUNCTION = "main"

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)

    def main(self, url, folder, file_name, **kwargs):
        assert url is not None
        out_dir = os.path.join(folder_paths.get_output_directory(), folder)
        os.makedirs(out_dir, exist_ok=True)
        local_path = os.path.join(out_dir, file_name)
        local_path = get_incremented_filename(local_path)
        _, file_name = os.path.split(local_path)
        output = os.path.join(folder, file_name)
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, "wb") as file:
                file.write(response.content)
            print("download finished in {}".format(local_path))
        else:
            print(f"download error: {response.status_code}")
        return (output,)

    @classmethod
    def IS_CHANGED(self, url, file_name, *args, **kwargs):
        return uuid.uuid4().hex
