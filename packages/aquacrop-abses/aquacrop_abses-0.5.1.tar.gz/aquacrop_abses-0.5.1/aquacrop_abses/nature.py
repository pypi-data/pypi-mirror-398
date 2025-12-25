#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""农田自然系统模块。

这个模块实现了农田自然系统的核心功能，包括：
1. 气象数据管理：加载、缓存和获取气象数据
2. 土壤类型管理：加载和验证土壤类型数据
3. 空间数据处理：重投影和坐标转换
4. 可视化：土壤类型分布展示

主要组件：
- CropLand: 农田系统的核心类
- 辅助函数：空间维度识别等
"""

from __future__ import annotations

import os
from datetime import datetime
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Dict, Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rioxarray as rxr
import xarray as xr
from abses import PatchModule
from loguru import logger
from matplotkit import with_axes
from pandas import Timestamp

from aquacrop_abses._types import DateType, MeteVar, PathLike, SoilType, SoilTypeAlias
from aquacrop_abses.cell import CropCell
from aquacrop_abses.load_datasets import COLS, METE_VARS, check_climate_dataframe

# Type alias for raster data
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

Raster: TypeAlias = "np.ndarray | xr.DataArray"


def get_spatial_dims(da: xr.DataArray) -> tuple[str, str]:
    """自动识别数据集的空间维度名称。

    支持多种常见的空间维度命名方式，如：
    - x/y
    - lon/lat
    - longitude/latitude
    不区分大小写。

    Args:
        da: 包含空间维度的数据集

    Returns:
        tuple[str, str]: 识别出的 x 和 y 维度名称

    Raises:
        TypeError: 如果输入不是 xr.DataArray
        ValueError: 如果无法识别空间维度
    """
    if not isinstance(da, xr.DataArray):
        raise TypeError(f"Expected xr.DataArray, got {type(da)}")

    xs = {"x", "lon", "longitude", "X", "LON", "LONGITUDE"}
    ys = {"y", "lat", "latitude", "Y", "LAT", "LATITUDE"}

    dims = set(da.dims)
    x_dim = next((d for d in dims if d.lower() in xs), None)
    y_dim = next((d for d in dims if d.lower() in ys), None)

    if not (x_dim and y_dim):
        raise ValueError(
            f"Cannot identify spatial dimensions from {dims}. "
            f"Expected dimensions like: x/y, lon/lat, longitude/latitude"
        )
    return x_dim, y_dim


class CropLand(PatchModule):
    """农田自然系统类。

    管理农田系统的空间属性、气象数据和土壤类型。支持：
    1. 加载和管理多种气象数据
    2. 处理不同格式的土壤类型数据
    3. 提供时空数据的访问接口
    4. 可视化系统状态

    Attributes:
        _cached_datasets (Dict[str, xr.DataArray]): 缓存的气象数据
        _data_path (Dict[str, Path]): 气象数据文件路径
        _last_climate_time_range (tuple): 上次访问的时间范围

    Properties:
        data_path (pd.Series): 气象数据路径信息
        time_range (pd.DataFrame): 气象数据的时间范围信息
        common_time_range (tuple): 所有气象数据的共同时间范围

    Example:
        >>> cropland = CropLand(model, name="farmland")
        >>> cropland.load_soil("clay_loam")  # 加载土壤类型
        >>> cropland.load_weather("Temperature", "temp.nc")  # 加载气象数据
    """

    def __init__(self, *args, **kwargs):
        cell_cls = kwargs.pop("cell_cls", CropCell)
        super().__init__(*args, cell_cls=cell_cls, **kwargs)
        self._cached_datasets: Dict[str, xr.DataArray | pd.DataFrame] = {}
        self._data_path: Dict[str, Path] = {}
        self._last_time_range: tuple[Optional[DateType], Optional[DateType]] = (
            None,
            None,
        )

    @property
    def weather_is_df(self) -> bool:
        """气象数据是否为 DataFrame"""
        return isinstance(self._cached_datasets, pd.DataFrame)

    @property
    def data_path(self) -> pd.Series | str:
        """气象数据路径"""
        if self.weather_is_df:
            return "pd.DataFrame"
        paths = [self._data_path.get(key, Path(".")).stem for key in METE_VARS]
        return pd.Series(paths, index=METE_VARS, name="Data Path")

    @cached_property
    def time_range(self) -> pd.DataFrame:
        """当前缓存的每个气象变量的时间范围。
        索引：气象变量
        三列：开始时间、结束时间、时间步长

        如果气象变量没有缓存，则返回空值。

        Returns:
            pd.DataFrame: 包含三列 ('start', 'end', 'freq') 的数据框，
                         索引为气象变量名称
        """
        if not hasattr(self, "_cached_datasets") or not self._cached_datasets:
            return pd.DataFrame()

        ranges = {}
        for var_name, data in self._cached_datasets.items():
            time_index = data.time.to_index()
            ranges[var_name] = {
                "start": time_index[0],
                "end": time_index[-1],
                "freq": pd.infer_freq(time_index),
            }

        return pd.DataFrame.from_dict(
            ranges, orient="index", columns=["start", "end", "freq"]
        )

    @cached_property
    def common_time_range(self) -> tuple[Timestamp, Timestamp]:
        """所有气象数据集的公共时间范围"""
        return (
            self.time_range.start.min(),
            self.time_range.end.max(),
        )

    def _check_cache_clear(
        self,
        t1: Optional[str | datetime],
        t2: Optional[str | datetime],
    ) -> None:
        """清空缓存"""
        # 检查时间范围是否改变
        current_time_range = (t1, t2)
        if self._last_time_range != current_time_range:
            self.get_climate.cache_clear()
            self._last_time_range = current_time_range

    @lru_cache(maxsize=256)  # 增加缓存大小以提高性能
    def get_climate(
        self,
        mete: MeteVar,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None,
        dim: str = "time",
    ) -> xr.DataArray:
        """获取指定时间范围的气象数据。

        自动处理时间范围超出数据集范围的情况。使用缓存提高性能。

        Args:
            mete: 气象变量名称
            time_start: 开始时间，None 表示数据集起始
            time_end: 结束时间，None 表示数据集结束
            dim: 时间维度名称

        Returns:
            xr.DataArray: 选定时间范围的气象数据

        Raises:
            IndexError: 如果指定的维度不存在
        """
        if dim not in self._cached_datasets[mete].dims:
            raise IndexError(f"Dimension {dim} not found.")
        data_start, data_end = self.common_time_range
        if time_start is None:
            time_start = data_start
        if time_end is None:
            time_end = data_end
        return self._cached_datasets[mete].sel(**{dim: slice(time_start, time_end)})

    def get_weather_df(
        self,
        pos: tuple[float, float] | CropCell,
        t0: Optional[str | datetime] = None,
        t1: Optional[str | datetime] = None,
    ) -> pd.DataFrame:
        """获取指定位置和时间范围的气象数据。

        支持通过坐标或 CropCell 指定位置。自动处理数据插值和时间聚合。

        Args:
            pos: 位置坐标或 CropCell 实例
            t0: 开始时间
            t1: 结束时间

        Returns:
            pd.DataFrame: 包含所有气象变量的数据框，列包括：
                - Date: 日期
                - Temperature: 温度
                - Precipitation: 降水量
                - ReferenceET: 参考蒸散发（下限为 0.1）
                - ...其他气象变量
        """
        # 如果缓存是 DataFrame，则直接返回
        if self.weather_is_df:
            return self._cached_datasets
        # 否则，从缓存中获取气象数据
        if isinstance(pos, CropCell):
            pos = pos.indices
        # 创建一个字典来存储所有变量的数据
        data_dict = {}
        for mete in METE_VARS:
            da = self.get_climate(mete=mete, time_start=t0, time_end=t1)
            v = da.sel(x=pos[1], y=pos[0], method="nearest").groupby("time.date").mean()
            data_dict[mete] = pd.Series(v.values, index=pd.to_datetime(v.date))

        # 清空缓存
        self._check_cache_clear(t0, t1)
        # 创建 DataFrame 并直接设置列顺序
        df = pd.DataFrame(data_dict).reset_index(names="Date").reindex(columns=COLS)
        df["ReferenceET"] = df["ReferenceET"].clip(lower=0.1)
        return df

    def _reproject_datasets(self, ds: xr.DataArray, **kwargs) -> xr.DataArray:
        """重投影数据集

        Note: ABSESpy 0.8.0 中坐标系统有变化，批量重投影可能导致坐标不匹配。
        当前使用稳定的逐时间步处理方式。
        """

        def _reproject_by_time(da: xr.DataArray) -> xr.DataArray:
            reprojected_list = []
            for time_step in da.time:
                tmp_res = self.reproject(da.sel(time=time_step), **kwargs)
                reprojected_list.append(tmp_res)
            return xr.concat(reprojected_list, dim="time")

        x_dim, y_dim = get_spatial_dims(ds)
        ds = ds.rename({x_dim: "x", y_dim: "y"})
        crs = kwargs.pop("crs", self.crs)
        ds.rio.write_crs(crs, inplace=True)
        return _reproject_by_time(ds)

    def _clear_time_range_cache(self):
        """安全地清除 time_range 的缓存"""
        try:
            del self.time_range
            del self.common_time_range
        except AttributeError:
            pass  # 如果属性不存在，就忽略错误

    def load_weather(
        self,
        mete: MeteVar,
        data: PathLike | xr.DataArray,
        reproject: bool = True,
        **rpj_kwargs,
    ) -> None:
        """加载气象数据集

        Args:
            mete: 气象变量
            data: 气象数据集，可以是文件路径或加载好的 DataArray 数据
            reproject: 是否重投影
            **kwargs: 重投影参数

        Raises:
            FileNotFoundError: 如果气象数据文件不存在
        """
        if isinstance(data, str):
            data = Path(data)
        if isinstance(data, Path):
            if not data.exists():
                raise FileNotFoundError(f"Climate data file not found: {data}")
            self._data_path[mete] = data
            data = xr.open_dataarray(data)
        if reproject:
            data = self._reproject_datasets(data, **rpj_kwargs)
        self._cached_datasets[mete] = data
        self._clear_time_range_cache()
        logger.info(f"Loaded climate data from {data}")

    def _load_soil_raster(
        self,
        soil_array: np.ndarray,
    ) -> None:
        """加载土壤类型"""
        # 如果是浮点型，转换为整数
        if soil_array.dtype in [np.float32, np.float64]:
            soil_array = soil_array.astype(int)
        # 如果是字符串型，转换为整数
        if np.issubdtype(soil_array.dtype, np.str_):
            soil_array = SoilType.to_code(soil_name=soil_array)
        # 验证是否为整数（土壤类型代码）
        if not np.issubdtype(soil_array.dtype, np.integer):
            raise ValueError(f"Soil raster dtype {soil_array.dtype} is not integer.")
        # 验证栅格数据中的土壤类型是否有效
        unique_values = np.unique(soil_array)
        invalid_types = set(unique_values) - SoilType.codes()
        if invalid_types:
            raise ValueError(f"Invalid soil types found in raster: {invalid_types}")
        # 验证维度与 Patch 一致
        if soil_array.shape != self.shape2d:
            raise ValueError(
                f"Soil raster ({soil_array.shape}) not match Patch ({self.shape2d})."
            )
        self.apply_raster(soil_array, "soil")
        soils = self.get_raster("soil")
        for soil_type in np.unique(soils):
            logger.debug(
                f"Soil type {soil_type} has {np.sum(soils == soil_type)} pixels."
            )

    def load_soil(
        self,
        soil: Raster | PathLike | SoilTypeAlias | Literal["Random"],
        reload: bool = False,  # 优化：默认不 reload，避免性能损失
    ) -> None:
        """加载土壤类型数据。

        支持多种输入格式：
        1. 栅格文件或数组：空间分布的土壤类型
        2. 土壤类型名称：整个区域使用相同土壤
        3. "Random"：随机生成土壤类型分布

        Args:
            soil: 土壤类型数据
            reload: 是否重新初始化空间结构

        Raises:
            TypeError: 输入格式不支持
            ValueError: 土壤类型无效
            FileNotFoundError: 栅格文件不存在
        """
        # 处理字符串类型的输入
        if isinstance(soil, str):
            if soil == "Random":
                # 随机生成土壤类型
                random_soils = np.random.choice(
                    list(SoilType.codes()),
                    size=self.shape2d,
                )
                self._load_soil_raster(random_soils)
                return
            # 如果是单一土壤类型，转换为土壤代码
            try:
                self._load_soil_raster(np.full(self.shape2d, SoilType.to_code(soil)))
                return
            except TypeError:
                # 如果是字符串路径，转换为 Path 对象
                soil = Path(soil)

        # 处理栅格文件路径
        if isinstance(soil, Path):
            if not soil.exists():
                raise FileNotFoundError(f"Soil raster file not found: {soil}")
            # 加载栅格数据
            soil = rxr.open_rasterio(soil)
            logger.info(f"Loaded soil type from {soil}")

        # 处理栅格数据
        if isinstance(soil, xr.DataArray):
            bounds = soil.rio.bounds()
        if isinstance(soil, np.ndarray):
            bounds = None
        if isinstance(soil, (xr.DataArray, np.ndarray)):
            # 如果需要重新加载，则重新初始化
            data = np.nan_to_num(soil.squeeze(), nan=0)
            if reload:
                self._reload(array=data, bounds=bounds)
            self._load_soil_raster(data)
            return

        raise TypeError(
            f"Unsupported soil type: {type(soil)}. "
            "Expected Raster, PathLike, SoilType, or 'Random'"
        )

    @with_axes
    def display(self, ax: plt.Axes) -> None:
        """可视化土壤类型分布。

        绘制土壤类型空间分布图，包括：
        1. 土壤类型栅格
        2. 农民位置
        3. 图例

        Args:
            ax: matplotlib 坐标轴
            **scatter_kwargs: 传递给散点图的参数
        """
        soil_array = self.get_raster("soil").squeeze()
        cmap = SoilType.get_colormap(soil_array)
        ax.imshow(soil_array, cmap=cmap, alpha=0.6, zorder=1)
        # 添加图例
        unique_soils = np.unique(soil_array)
        legend_elements = [
            plt.Rectangle(
                (0, 0),
                1,
                1,
                facecolor=SoilType.color(soil),
                label=SoilType.to_name(soil),
                edgecolor="white",
                linewidth=0.5,
                alpha=0.6,
            )
            for soil in unique_soils
        ]
        ax.set_title("Soil Type Distribution")
        ax.legend(
            handles=legend_elements,
            loc="center left",
            bbox_to_anchor=(1, 0.5),
            title="Soil Types",
        )

    def _reload(
        self,
        array: np.ndarray | xr.DataArray,
        bounds: tuple[float | int, ...] | None = None,
        inplace: bool = True,
    ) -> None:
        """重新初始化"""
        height, width = array.shape
        if isinstance(array, xr.DataArray):
            bounds = array.rio.bounds()
        if bounds is None:
            bounds = (0, 0, width, height)
        obj = CropLand(
            self.model,
            name=self.name,
            cell_cls=CropCell,
            width=width,
            height=height,
            total_bounds=bounds,
            crs=self.crs,
        )
        if inplace:
            # 显式更新关键属性
            self._cells = getattr(obj, "_cells")
            self._width = obj.width
            self._height = obj.height
            self._total_bounds = obj.total_bounds
            self._mask = obj.mask
            self._update_transform()
            # Clear cached properties to force regeneration
            for attr in ["array_cells", "cells", "xda"]:
                self.__dict__.pop(attr, None)
            # Update layer reference for all cells AFTER clearing caches
            for cell in self._cells:
                if hasattr(cell, "_set_layer"):
                    cell._set_layer(self)
            # Note: Keep _cached_datasets and other weather-related attributes unchanged

    def batch_load_weather(
        self,
        weather: PathLike | xr.Dataset | pd.DataFrame,
        mete_var_mapping: Optional[Dict[MeteVar, str]] = None,
        **rpj_kwargs,
    ) -> pd.Series:
        """批量加载气象数据。
        如果气象数据集是一个 xr.Dataset 文件里的多个变量，
        或者每一个气象变量是一个 xr.DataArray 文件，
        则可以批量加载气象数据。

        Args:
            path_pattern: 气象数据集路径或路径模式，
            - 使用 {var} 表示气象变量
            - 使用 "%d/%m/%Y, %H:%M:%S" 表示时间
            本函数会自动将路径模式中的气象变量替换为 METE_VARS 中的变量、
            根据当前模型的时间，自动生成路径模式中的时间，
            最后生成完整的气象数据集路径。
            mete_var_mapping: 气象变量与数据集变量名称的映射，
            需包含所有四个气象变量，以及它们在数据集中的变量名称：
            - MinTemp: 最低温度；
            - MaxTemp: 最高温度；
            - Precipitation: 降水量；
            - ReferenceET: 参考蒸散发量；
        rpj_kwargs: 重投影参数

        Returns:
            Dict[str, xr.DataArray]: 气象数据集
        """
        if mete_var_mapping is None:
            mete_var_mapping = {mete: mete for mete in METE_VARS}
        if isinstance(weather, (xr.Dataset, pd.DataFrame)):
            return self._load_ds(weather, mete_var_mapping, **rpj_kwargs)
        weather = str(weather)  # 转换为字符串
        # 如果路径是一个文件，则直接加载
        if Path(weather).is_file():
            return self._load_ds(weather, mete_var_mapping, **rpj_kwargs)
        # 否则先替代时间，看看是不是每个时间戳一个文件
        path = self.time.dt.strftime(weather)
        if Path(path).is_file():
            return self._load_ds(path, mete_var_mapping, **rpj_kwargs)
        # 否则逐一变换气象变量，加载文件
        for mete_var, var_name in mete_var_mapping.items():
            tmp_path = path.replace(r"{var}", var_name)
            if Path(tmp_path).is_file():
                self.load_weather(mete=mete_var, data=tmp_path, **rpj_kwargs)
            else:
                raise FileNotFoundError(f"No weather data found at {tmp_path}")
        return self.data_path

    def _load_ds(
        self,
        path: PathLike | xr.Dataset | pd.DataFrame,
        mete_var_mapping: Dict[MeteVar, str],
        **rpj_kwargs,
    ) -> pd.Series:
        """从单个气象数据集文件加载气象数据集"""
        # 处理 DataFrame 输入
        if isinstance(path, pd.DataFrame):
            # 重命名列以匹配所需变量名
            df = path.rename(columns=mete_var_mapping)
            if check_climate_dataframe(df):
                self._cached_datasets = df
                return self.data_path
            raise ValueError("Invalid climate DataFrame format")
        # 处理 xr.Dataset 输入
        if isinstance(path, xr.Dataset):
            ds = path  # 直接使用数据集
            path = Path(os.getcwd()) / "xr.Dataset.nc"
        # 处理 PathLike 输入
        else:
            path = Path(path)
            ds = xr.open_dataset(path)
        for mete_var, var_name in mete_var_mapping.items():
            self._data_path[mete_var] = path
            self.load_weather(mete=mete_var, data=ds[var_name], **rpj_kwargs)
        return self.data_path
