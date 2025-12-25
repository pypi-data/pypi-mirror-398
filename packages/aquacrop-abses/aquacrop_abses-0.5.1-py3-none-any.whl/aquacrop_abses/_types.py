#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Literal, Optional, Set, Union

import numpy as np
import xarray as xr
from matplotlib.colors import ListedColormap

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

ResamplingMethod: TypeAlias = Literal[
    "mode",
    "nearest",
    "average",
    "rms",
    "sum",
    "min",
    "max",
    "median",
    "q1",
    "q3",
    "std",
    "var",
]


class ClimateData(str, Enum):
    """气候数据集枚举"""

    TMIN = "MinTemp"
    TMAX = "MaxTemp"
    RAIN = "Precipitation"
    PET = "ReferenceET"


# 有效的土壤类型值集合
class SoilType(int, Enum):
    """土壤类型枚举。"""

    Clay = 1  # clay (heavy)
    SiltClay = 2  # Silt clay
    ClayLight = 3  # clay
    SiltClayLoam = 4  # Silt clay loam
    ClayLoam = 5  # clay loam
    Silt = 6  # silt
    SandyClay = 7  # sandy clay
    SiltLoam = 8  # silt loam
    Loam = 9  # loam
    SandyClayLoam = 10  # sandy clay loam
    SandyLoam = 11  # sandy loam
    LoamySand = 12  # loamy sand
    Sand = 13  # sand
    Paddy = 14  # paddy
    Default = 0  # 默认值或未知类型

    @classmethod
    def _missing_(cls, value):
        """处理未找到的值。

        当通过值创建枚举成员失败时，这个方法会被调用。
        """
        if isinstance(value, str):
            # 如果输入是字符串，尝试匹配枚举成员名称
            try:
                return next(m for m in cls if m.name.lower() == value.lower())
            except StopIteration:
                pass
        return None  # 返回 None 会导致抛出 ValueError

    @classmethod
    def codes(cls) -> Set[int]:
        """获取所有有效的土壤类型代码。"""
        return {member.value for member in cls}

    @classmethod
    def to_name(cls, code: int) -> str:
        """从土壤代码转换为土壤类型字符串。"""
        return cls(code).name

    @classmethod
    def color(cls, soil: str | int) -> str:
        """从土壤类型字符串转换为颜色"""
        if isinstance(soil, str):
            return SOIL_COLORS[SoilType(soil)]
        return SOIL_COLORS[cls(soil)]

    @classmethod
    def to_code(cls, soil_name: str | np.ndarray, default: int = 0) -> int:
        """将土壤类型字符串转换为土壤代码

        Args:
            soil_name: 土壤类型名称或包含土壤类型名称的数组

        Returns:
            对应的土壤代码或包含土壤代码的数组
        """
        # 创建反向映射：从土壤类型名称到代码
        if isinstance(soil_name, str):
            try:
                return cls(soil_name).value
            except ValueError:
                return default
        return np.vectorize(cls.to_code)(soil_name, default)

    @classmethod
    def get_colormap(cls, soil_array: Optional[np.ndarray] = None) -> ListedColormap:
        """创建颜色映射，如果传入土壤类型数组，则返回该数组中所有土壤类型的颜色映射"""
        if isinstance(soil_array, np.ndarray):
            return ListedColormap(
                [SOIL_COLORS[cls(soil)] for soil in np.unique(soil_array)]
            )
        return ListedColormap([SOIL_COLORS[soil] for soil in cls])

    @classmethod
    def names(cls) -> Set[str]:
        """获取所有有效的土壤类型名称。"""
        return {member.name for member in cls}


# 土壤类型对应的颜色代码
SOIL_COLORS: Dict[SoilType, str] = {
    SoilType.Clay: "#8B4513",  # 深棕色
    SoilType.ClayLoam: "#A0522D",  # 赭色
    SoilType.ClayLight: "#8B4513",  # 深棕色
    SoilType.Loam: "#CD853F",  # 秘鲁色
    SoilType.LoamySand: "#DEB887",  # 实木色
    SoilType.Sand: "#F4A460",  # 沙褐色
    SoilType.SandyClay: "#D2691E",  # 巧克力色
    SoilType.SandyClayLoam: "#B8860B",  # 暗金色
    SoilType.SandyLoam: "#DAA520",  # 金菊色
    SoilType.Silt: "#BDB76B",  # 暗卡其色
    SoilType.SiltClayLoam: "#6B8E23",  # 橄榄褐色
    SoilType.SiltLoam: "#9ACD32",  # 黄绿色
    SoilType.SiltClay: "#556B2F",  # 暗橄榄绿
    SoilType.Paddy: "#2F4F4F",  # 暗岩灰
    SoilType.Default: "#FFFFFF",  # 白色
}

# 用于类型提示
SoilTypeAlias = str | SoilType

# 用于类型提示
PathLike: TypeAlias = Union[str, Path]
# 用于类型提示
ClimateDatasets: TypeAlias = Dict[str, xr.DataArray]
# 用于类型提示
MeteVar: TypeAlias = Literal["MaxTemp", "MinTemp", "Precipitation", "ReferenceET"]
# 用于类型提示
DateType: TypeAlias = Union[str, datetime]
