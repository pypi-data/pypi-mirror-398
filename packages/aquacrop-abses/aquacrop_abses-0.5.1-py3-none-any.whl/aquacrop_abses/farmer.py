#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
这个脚本定义了农民类。

农民应该根据当前的可用水量，选择自己的灌溉策略。
"""

import itertools
from typing import Any, Callable, Dict, Iterable, Literal, Optional, Union, cast

import numpy as np
import pandas as pd
from abses import Actor
from aquacrop import AquaCropModel, Crop, FieldMngt, IrrigationManagement, Soil
from loguru import logger
from scipy.optimize import differential_evolution

from aquacrop_abses import get_config
from aquacrop_abses.cell import (
    DT_PATTERN,
    CropCell,
    CropTypes,
    _CropCell,
    get_crop_datetime,
)

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias


DY = "Dry yield (tonne/ha)"
FY = "Fresh yield (tonne/ha)"
YP = "Yield potential (tonne/ha)"
IRR = "Seasonal irrigation (mm)"

YieldItem: TypeAlias = Literal[
    "dry_yield",
    "fresh_yield",
    "yield_potential",
]


class Farmer(Actor):
    """农民行动者，可以选择和优化灌溉策略。

    这个类继承自 Actor，主要负责：
    1. 管理作物种植
    2. 设置灌溉策略
    3. 模拟作物生长
    4. 优化灌溉参数

    灌溉管理策略包括六种方法：
    - `IrrMethod=0`: 雨养农业（无灌溉）
    - `IrrMethod=1`: 基于土壤水分阈值的灌溉
        在四个主要生长阶段（出苗、冠层生长、最大冠层、衰老）设置不同阈值
    - `IrrMethod=2`: 固定时间间隔灌溉
    - `IrrMethod=3`: 预定义灌溉计划
    - `IrrMethod=4`: 净灌溉（每日补充以维持土壤水分）
    - `IrrMethod=5`: 每日固定灌溉量

    Attributes:
        irr_method (int): 当前使用的灌溉方法
        _results (pd.DataFrame): 存储模拟结果的数据框
        dry_yield (pd.Series): 干产量结果
        fresh_yield (pd.Series): 鲜产量结果
        yield_potential (pd.Series): 潜在产量
        seasonal_irrigation (pd.Series): 季节灌溉量

    Example:
        >>> farmer = Farmer(unique_id="farmer_1", irr_method=1)
        >>> farmer.add_crop("wheat")
        >>> results = farmer.simulate()
        >>> # 优化土壤水分阈值
        >>> optimized = farmer.optimize_smt()
    """

    irr_methods = {
        0: "Rainfed",
        1: "Soil Moisture Targets",
        2: "Set Time Interval",
        3: "Predefined Schedule",
        4: "Net Irrigation",
        5: "Constant Depth",
    }

    def __init__(self, *args, irr_method: Optional[int] = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # 灌溉策略
        default_irr_method = get_config().farmer.irr_method
        self.irr_method: int = irr_method or default_irr_method
        # 产量估算结果
        self._results: pd.DataFrame = pd.DataFrame()

    def __repr__(self) -> str:
        irr: str = self.irr_methods[self.irr_method]
        return f"<{self.unique_id} [{irr}]>"

    def __getattr__(self, name: str) -> Any:
        if name in [DY, FY, YP, IRR]:
            return self._results.get(name)
        return super().__getattribute__(name)

    @property
    def results(self) -> pd.DataFrame:
        """当前年份的模拟结果"""
        return self._results.drop_duplicates(
            subset=["Season", "Crop"],
            keep="last",
        )

    @property
    def crop_here(self) -> Dict[str, Crop]:
        """当前地块上的作物"""
        return self.get("crops", target="cell")

    @property
    def irr_method(self) -> int:
        """灌溉策略"""
        return self._irr_method

    @irr_method.setter
    def irr_method(self, value: int) -> None:
        if value not in self.irr_methods:
            raise ValueError(f"Invalid value for irr_method: {value}.")
        self._irr_method = value

    @property
    def field_management(self) -> FieldMngt:
        """当前的田间管理策略"""
        return FieldMngt(**self.p.get("FieldMngt", {}))

    @property
    def dry_yield(self) -> pd.Series | float:
        """当前年份的干产量"""
        return self._results.get(DY)

    @property
    def fresh_yield(self) -> pd.Series | float:
        """当前年份的湿产量"""
        return self._results.get(FY)

    @property
    def yield_potential(self) -> pd.Series | float:
        """当前年份的潜在产量"""
        return self._results.get(YP)

    @property
    def seasonal_irrigation(self) -> pd.Series:
        """当前年份的灌溉量"""
        return self._results.get(IRR)

    def add_crop(self, crop: str) -> bool:
        """试图添加一个作物

        如果成功添加，返回 True，否则返回 False。"""
        if self.at is None:
            return False
        try:
            self.at.add_crop(crop)
        # 如果生长时间重叠，则不添加作物
        except ValueError:
            return False
        return True

    def irr_management(self, **kwargs) -> IrrigationManagement:
        """当前的灌溉管理策略。"""
        params = self.p.get("IrrigationManagement", {})
        params.update(kwargs)
        return IrrigationManagement(irrigation_method=self.irr_method, **params)

    def optimize(
        self,
        param_bounds: list[tuple[float, float]],
        param_name: str,
        fitness_func: Callable[[pd.DataFrame], float] = lambda x: x[DY].sum(),
        param_processor: Callable[[np.ndarray], Any] = lambda x: float(x[0]),
        size_pop: int = 15,
        max_iter: int = 50,
        **kwargs,
    ) -> pd.DataFrame:
        """通用优化框架，用于优化任何给定参数。

        使用差分进化算法优化指定参数，以最大化适应度函数的值。

        Args:
            param_bounds: 参数边界列表，每个参数的 (min, max)
            param_name: 参数名称，用于传递给 simulate
            fitness_func: 适应度函数，接收模拟结果 DataFrame 作为输入，返回 float
            param_processor: 参数处理函数，将优化器的数组转换为参数实际需要的格式
            size_pop: 种群大小，影响优化的多样性
            max_iter: 最大迭代次数，影响优化的精度
            **kwargs: 传递给 simulate 的其他参数

        Returns:
            pd.DataFrame: 使用最优参数的模拟结果

        Example:
            >>> # 优化灌溉间隔
            >>> farmer.optimize(
            ...     param_bounds=[(1, 10)],
            ...     param_name="IrrInterval",
            ...     fitness_func=lambda df: df["DY"].sum() / df["IrrWater"].sum(),
            ...     param_processor=lambda x: int(x[0])
            ... )
        """

        def objective(params: np.ndarray) -> float:
            processed_params = param_processor(params)
            return -self.simulate(
                is_test=True,
                agg_func=fitness_func,
                **{param_name: processed_params},
                **kwargs,
            )

        result = differential_evolution(
            func=objective,
            bounds=param_bounds,
            popsize=size_pop,
            maxiter=max_iter,
            polish=True,
        )

        best_params = result.x
        best_reward = -result.fun
        logger.debug(f"Best {param_name}: {best_params}, Reward: {best_reward}")
        return self.simulate(
            **{param_name: param_processor(best_params)},
            **kwargs,
            is_test=False,
        )

    def optimize_smt(
        self,
        fitness_func: Callable[[pd.DataFrame], float] = lambda x: x[DY].sum(),
        size_pop: int = 15,
        max_iter: int = 50,
        **kwargs,
    ) -> pd.DataFrame:
        """以土壤水为目标，优化灌溉管理策略。"""
        if self.irr_method != 1:
            raise ValueError(
                "Irr method must be 1 (Soil Moisture Targets) for optimizing SMT."
            )
        return self.optimize(
            param_bounds=[(0, 100)] * 4,
            param_name="SMT",
            fitness_func=fitness_func,
            param_processor=lambda x: x.tolist(),
            size_pop=size_pop,
            max_iter=max_iter,
            **kwargs,
        )

    def simulate(
        self,
        crops: Optional[CropTypes | Iterable[CropTypes]] = None,
        weather_df: Optional[pd.DataFrame] = None,
        is_test: bool = False,
        agg_func: Callable = lambda x: x[DY].sum(),
        **kwargs,
    ) -> Union[pd.DataFrame, float]:
        """模拟当前地块上所有作物的生长。

        执行作物生长模拟，可用于优化或常规模拟。支持多作物系统，
        每个作物都会根据当前的灌溉管理策略进行模拟。

        Args:
            cell: 要模拟的地块，默认为当前地块
            clear_crops: 是否在模拟后清除作物，默认为 True
            is_test: 是否处于测试模式，如果是则返回适应度值
            fitness: 适应度计算函数，仅在 is_test=True 时使用
            **kwargs: 传递给灌溉管理的参数

        Returns:
            Union[pd.DataFrame, float]:
                - 如果 is_test=True，返回适应度值
                - 否则返回包含所有作物模拟结果的 DataFrame

        Note:
            模拟结果会自动添加到 _results 属性中，可通过各种产量属性访问
        """
        year = self.time.year
        # 如果作物为空，则使用当前地块上的作物
        tmp_cell = _CropCell.copy_to(
            copy_cell=self.at,
            crops=crops,
            soil=kwargs.get("soil"),
        )
        # 如果仍然没有作物，则返回当前结果
        if not tmp_cell.crops:
            logger.warning(f"{self} has no crops.")
            return self.results
        # 如果有作物，模拟所有作物生长
        if weather_df is None:
            weather_df = cast(CropCell, self.at).get_weather(year=self.time.year)
        data = []
        for name, crop in tmp_cell.crops.items():
            res = self._simulate_once(
                tmp_cell=tmp_cell,
                crop=crop,
                weather_df=weather_df,
                **kwargs,
            )
            res["Crop"] = name
            res["Season"] = year
            data.append(res.set_index("Crop"))
        result_this_year = pd.concat(data)
        # 如果处于测试模式，则返回适应度值
        if is_test:
            return agg_func(result_this_year)
        # 如果不是测试模式，则将结果添加到 _results 中，并清除作物
        # 优化：避免不必要的复制
        if self._results.empty:
            self._results = result_this_year.reset_index()
        else:
            self._results = pd.concat(
                [self._results, result_this_year.reset_index()],
                ignore_index=True,
                copy=False,  # 避免不必要的复制，提高性能
            )
        self.at.clear()
        return result_this_year

    def _simulate_once(
        self,
        tmp_cell: _CropCell,
        crop: Crop,
        weather_df: Optional[pd.DataFrame] = None,
        **management_kwargs,
    ) -> pd.DataFrame:
        """模拟一个时间步长。
        这个时间步应该是一年，因为作物通常按年来种植。
        但是气象数据集是按日来的，而且有些作物会跨年。
        所以我们用两个自然年的数据来模拟一个作物年。
        """
        # 如果土壤和气象数据为空，则使用当前地块的土壤和气象数据
        # 获取作物的生长日期
        start_dt, end_dt = get_crop_datetime(crop, year=self.time.year)
        # 创建 AquaCropModel 对象，用于模拟作物生长
        model = AquaCropModel(
            sim_start_time=start_dt.strftime(DT_PATTERN),
            sim_end_time=end_dt.strftime(DT_PATTERN),
            weather_df=weather_df,  # fixed
            soil=Soil(tmp_cell.soil_name),  # fixed
            crop=crop,  # fixed
            initial_water_content=tmp_cell.init_wc,  # fixed?
            irrigation_management=self.irr_management(**management_kwargs),
            # groundwater=tmp_cell.groundwater,  # fixed
        )
        # 运行模型，直到作物生长结束
        model.run_model(till_termination=True)
        # 返回模拟结果
        return model.get_simulation_results()

    def scenario_test(
        self,
        agg_func: Callable[[pd.DataFrame], float] = lambda x: x[DY].sum(),
        **kwargs,
    ) -> pd.DataFrame:
        """测试不同策略的效果

        用户可以提供一个字典，指定每个参数的取值范围。
        然后模拟所有可能的组合，并返回结果。
        """
        data = []
        for values in itertools.product(*kwargs.values()):
            tmp_dict = dict(zip(kwargs.keys(), values))
            result = self.simulate(**tmp_dict, is_test=True, agg_func=agg_func)
            if isinstance(result, (int, float)):
                tmp_dict["result"] = result
            elif isinstance(result, pd.Series):
                tmp_dict.update(result.to_dict())
            data.append(tmp_dict)
        return pd.DataFrame(data)
