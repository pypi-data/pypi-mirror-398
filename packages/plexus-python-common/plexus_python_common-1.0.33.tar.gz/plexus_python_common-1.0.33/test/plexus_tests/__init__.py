import os

__all__ = [
    "module_directory",
    "source_directory",
    "test_directory",
    "resources_directory",
    "temporary_directory",
]

module_directory: str = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
source_directory: str = os.path.abspath(os.path.join(module_directory, "src"))
test_directory: str = os.path.abspath(os.path.join(module_directory, "test"))
resources_directory: str = os.path.abspath(os.path.join(module_directory, "resources"))
temporary_directory: str = os.path.abspath(os.path.join(module_directory, "tmp"))
