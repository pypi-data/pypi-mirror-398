"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'tdjson.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .tdjson_ext import td_create_client_id, td_send, td_receive, td_execute
from ._version import __version__, __copyright__, __license__

__all__ = [
    "td_create_client_id",
    "td_send",
    "td_receive",
    "td_execute",
    "__version__",
    "__copyright__",
    "__license__",
]
