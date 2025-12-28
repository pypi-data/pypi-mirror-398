import os

from .wrappers import UGlobalWrapper as global_wrapper
from .validation.files import validate_directory_path

class Global:

    @staticmethod
    def set_build_plugin_root_directory(directory:str) -> None:
        # Validate directory path
        validated_path = validate_directory_path(
            directory, 
            must_exist=True, 
            create_if_missing=False,
            param_name="directory", 
            function_name="set_build_plugin_root_directory"
        )
        global_wrapper.setBuildPluginRootDirectory(validated_path)

    @staticmethod
    def get_build_plugin_root_directory() -> str:
        return global_wrapper.getBuildPluginRootDirectory()
    
