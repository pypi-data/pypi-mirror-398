#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""CropCell 模块：定义了作物生长单元格的基本属性和行为。

这个模块实现了一个专门用于作物生长模拟的空间单元格系统。每个单元格可以：
- 管理多个作物的种植
- 处理作物生长时间
- 获取相关的气象和土壤数据
- 防止作物生长时间的重叠

主要组件：
- CropCell: 作物生长单元格的核心类
- 辅助函数：处理日期和作物重叠检查
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Tuple, TypeAlias

import pandas as pd
from abses import PatchCell, raster_attribute
from aquacrop import Crop, GroundWater, InitialWaterContent

from aquacrop_abses._types import SoilType
from aquacrop_abses.load_datasets import crop_name_to_crop

if TYPE_CHECKING:
    from aquacrop_abses.nature import CropLand

CropTypes: TypeAlias = Crop | str
IterCrops: TypeAlias = (
    list[CropTypes] | tuple[CropTypes] | set[CropTypes] | dict[str, CropTypes]
)
DT_PATTERN = r"%Y/%m/%d"


def is_overlapping(
    start: datetime, end: datetime, start_2: datetime, end_2: datetime
) -> bool:
    """检查两个时间区间是否重叠。

    Args:
        start: 第一个区间的开始时间
        end: 第一个区间的结束时间
        start_2: 第二个区间的开始时间
        end_2: 第二个区间的结束时间

    Returns:
        bool: 如果时间区间重叠返回 True，否则返回 False
    """
    return start <= end_2 and start_2 <= end


def get_crop_datetime(
    crop: Crop | Iterable[Crop], year: int = 2000
) -> Tuple[datetime, datetime]:
    """获取作物在指定年份的种植和收获日期。

    处理跨年生长的情况，如果收获日期早于种植日期，
    则认为是跨年生长，收获日期会被设置在下一年。

    Args:
        crop: 作物对象
        year: 种植年份，默认为2000年

    Returns:
        Tuple[datetime, datetime]: 种植日期和收获日期
    """
    # 如果 crop 是可迭代对象，则对每个作物进行处理
    if hasattr(crop, "__iter__"):
        planting_dates, harvest_dates = [], []
        for item in crop:
            t0, t1 = get_crop_datetime(item, year)
            planting_dates.append(t0)
            harvest_dates.append(t1)
        return min(planting_dates), max(harvest_dates)
    if isinstance(crop, Crop):
        # 如果 crop 是单个作物，则直接处理
        t0 = datetime.strptime(f"{year}/{crop.planting_date}", DT_PATTERN)
        t1 = datetime.strptime(f"{year}/{crop.harvest_date}", DT_PATTERN)
        if t1 < t0:
            t1 = datetime.strptime(f"{year + 1}/{crop.harvest_date}", DT_PATTERN)
        return t0, t1
    raise TypeError(f"Crop must be a Crop or a list of Crop, got {type(crop)}.")


class _CropCell:
    """作物生长单元格，用于模拟特定位置的作物生长。

    这个类继承自 PatchCell，添加了作物生长相关的功能：
    - 管理多个作物的种植和收获
    - 处理土壤属性
    - 获取气象数据
    - 防止作物生长期重叠

    Attributes:
        groundwater: 地下水情况
        _crop_types: 当前种植的作物字典
        _soil: 土壤类型编码

    Properties:
        init_wc: 初始土壤含水量
        layer: 所属的 CropLand 图层
        soil: 土壤类型编码
        soil_name: 土壤类型名称
        crops: 当前种植的所有作物
        has_crops: 当前种植的作物数量

    Example:
        >>> from abses import MainModel
        >>> from aquacrop_abses import CropLand
        >>> model = MainModel()
        >>> cropland = model.nature.create_module(
        ...     name="cropland",
        ...     module_cls=CropLand,
        ...     shape=(3, 4),
        ...     cell_cls=CropCell,
        ... )
        >>> cell = cropland.random.choice()
        >>> cell.soil = 1  # 设置土壤类型
        >>> cell.add_crop("Winter_Wheat")  # 添加冬小麦
        >>> # cell.get_weather(2020)  # 获取2020年的气象数据
    """

    def __init__(
        self,
        crops: CropTypes | Iterable[CropTypes] = None,
        soil: int = 0,
        groundwater: Optional[GroundWater] = None,
    ) -> None:
        """初始化作物单元格。"""
        self._crop_types: Dict[str, Crop] = {}
        self._soil: int = soil
        self.groundwater: Optional[GroundWater] = groundwater
        self.init_wc: Optional[InitialWaterContent] = InitialWaterContent(
            wc_type="Pct",
            value=[70],
        )
        if crops is not None:
            self.add_crop(crops)

    @classmethod
    def copy_to(
        cls,
        copy_cell: _CropCell,
        crops: Optional[CropTypes | Iterable[CropTypes]] = None,
        soil: Optional[int] = None,
    ) -> _CropCell:
        """复制一个地块的作物和土壤属性，并返回一个新的地块对象。"""
        crops = crops or getattr(copy_cell, "crops", None)
        soil = soil if soil is not None else getattr(copy_cell, "soil", 0)
        return _CropCell(
            crops=crops,
            soil=soil,
        )

    @property
    def soil(self) -> int:
        """土壤类型"""
        return self._soil

    @soil.setter
    def soil(self, soil_type: int | SoilType) -> None:
        """设置土壤类型。

        Args:
            soil_type: 可以是整数编码或 SoilType 枚举成员
        """
        # 如果输入是枚举成员，转换为其值
        if isinstance(soil_type, SoilType):
            soil_type = soil_type.value
        if isinstance(soil_type, str):
            soil_type = SoilType.to_code(soil_type)
        if soil_type not in SoilType.codes():
            raise ValueError(f"Invalid soil type: {soil_type}")
        self._soil = soil_type

    @property
    def soil_name(self) -> str:
        """土壤类型"""
        name = SoilType.to_name(self._soil)
        return (
            "Clay" if name == "ClayLight" else name
        )  # 兼容Soil，ClayLight 和 Clay 不区分

    def _check_crop_overlapping(self, crop: Crop) -> None:
        for existing_crop in self.crops.values():
            if is_overlapping(
                *get_crop_datetime(crop),
                *get_crop_datetime(existing_crop),
            ):
                raise ValueError(
                    f"Crops overlap: {crop.Name} and existing {existing_crop.Name}."
                )

    @property
    def crops(self) -> Dict[str, Crop]:
        """获取当前种植的所有作物。

        Returns:
            Dict[str, Crop]: 作物名称到作物对象的映射
        """
        return self._crop_types

    def add_crop(self, crop: CropTypes | IterCrops) -> None:
        """添加新的作物到单元格。

        会检查新作物的生长期是否与现有作物重叠。
        支持直接传入作物名称或 Crop 对象。

        Args:
            crop: 作物名称或 Crop 对象

        Raises:
            TypeError: 如果输入的作物类型无效
            ValueError: 如果作物生长期与现有作物重叠
        """
        if isinstance(crop, (list, tuple, set, dict)):
            for item in crop:
                self.add_crop(item)
            return
        name = crop if isinstance(crop, str) else crop.Name
        if isinstance(crop, str):
            crop = crop_name_to_crop(crop)
        if not isinstance(crop, Crop):
            raise TypeError("Crop must be a Crop.")
        self._check_crop_overlapping(crop=crop)
        self._crop_types[name] = crop

    def clear(self) -> None:
        """清除作物"""
        self._crop_types.clear()

    @raster_attribute
    def has_crops(self) -> int:
        """有多少农作物"""
        return len(self.crops)


class CropCell(PatchCell, _CropCell):
    """作物生长单元格，用于模拟特定位置的作物生长。"""

    def __init__(self, *args, **kwargs) -> None:
        groundwater = kwargs.pop("groundwater", None)
        soil = kwargs.pop("soil", 0)
        _CropCell.__init__(self, groundwater=groundwater, soil=soil)
        PatchCell.__init__(self, *args, **kwargs)

    @property
    def layer(self) -> "CropLand":
        """地块所在的图层"""
        return super().layer

    def get_weather(
        self,
        crops: Optional[Crop | Iterable[Crop]] = None,
        year: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取指定年份的气象数据。

        获取覆盖所有作物生长期的气象数据。

        Args:
            year: 指定年份，默认为当前模拟年份

        Returns:
            pd.DataFrame: 包含日期和气象变量的数据框
        """
        if year is None:
            year = self.time.year
        if crops is None:
            crops = self.crops.values()
        if crops:
            t0, t1 = get_crop_datetime(crops, year=year)
        else:
            t0, t1 = None, None
        return self.layer.get_weather_df(self, t0=t0, t1=t1)
