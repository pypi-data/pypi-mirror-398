#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

from .cam_base import HexCamBase, HexCamClientBase, HexCamServerBase
from .dummy import HexCamDummy, HexCamDummyClient, HexCamDummyServer
from .rgb import HexCamRGB, HexCamRGBClient, HexCamRGBServer

__all__ = [
    # base
    "HexCamBase",
    "HexCamClientBase",
    "HexCamServerBase",

    # dummy
    "HexCamDummy",
    "HexCamDummyClient",
    "HexCamDummyServer",

    # rgb
    "HexCamRGB",
    "HexCamRGBClient",
    "HexCamRGBServer",
]

# Check optional dependencies availability
from importlib.util import find_spec

_HAS_BERXEL = find_spec("berxel_py_wrapper") is not None
_HAS_REALSENSE = find_spec("pyrealsense2") is not None

# Optional: berxel
if _HAS_BERXEL:
    from .berxel import HexCamBerxel, HexCamBerxelClient, HexCamBerxelServer
    __all__.extend([
        "HexCamBerxel",
        "HexCamBerxelClient",
        "HexCamBerxelServer",
    ])

# Optional: realsense
if _HAS_REALSENSE:
    from .realsense import HexCamRealsense, HexCamRealsenseClient, HexCamRealsenseServer
    __all__.extend([
        "HexCamRealsense",
        "HexCamRealsenseClient",
        "HexCamRealsenseServer",
    ])
