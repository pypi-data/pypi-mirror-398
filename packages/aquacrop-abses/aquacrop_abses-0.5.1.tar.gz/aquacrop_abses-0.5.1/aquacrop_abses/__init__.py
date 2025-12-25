#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""结合AquaCrop和ABSES的模拟器。"""

import os
import warnings

os.environ["DEVELOPMENT"] = "DEVELOPMENT"

# 方法1：在代码中直接过滤
warnings.filterwarnings("ignore", category=FutureWarning)

from .cell import CropCell  # noqa: E402
from .config import get_config  # noqa: E402
from .farmer import Farmer  # noqa: E402
from .nature import CropLand  # noqa: E402

__all__ = [
    "CropCell",
    "Farmer",
    "CropLand",
    "get_config",
]
