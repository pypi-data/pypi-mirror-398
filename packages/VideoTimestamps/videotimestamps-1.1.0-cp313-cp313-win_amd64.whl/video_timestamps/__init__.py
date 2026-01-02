# Packages


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'videotimestamps.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .video_provider import *

# Files
from .abc_timestamps import *
from .fps_timestamps import *
from .rounding_method import *
from .text_file_timestamps import *
from .time_type import *
from .time_unit_converter import *
from .video_timestamps import *
