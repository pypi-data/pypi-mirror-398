#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
加载气象数据集
"""

from datetime import date
from functools import wraps
from importlib import resources
from pathlib import Path
from typing import Dict, Literal, Optional

import pandas as pd
from aquacrop import Crop
from aquacrop.entities.crop import crop_params
from aquacrop.utils import get_filepath, prepare_weather
from loguru import logger

from aquacrop_abses._constants import (
    CROP_CONFIGS,
    KW_DICTIONARY,
    REGIONALIZED_CROP_ADJUSTMENTS,
)

# 使用包内的资源文件
try:
    # Python 3.9+: 使用 files() API 访问包内资源
    _RES_PATH = resources.files("aquacrop_abses").joinpath("res")
except (TypeError, AttributeError):
    # 备用方案：使用 __file__
    _RES_PATH = Path(__file__).parent / "res"

CROPS_FOLDER = _RES_PATH / "crops"
COLS: list[str] = ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]

# 使用内嵌的关键字字典
KWARGS = KW_DICTIONARY


def _get_kwargs() -> Dict:
    """获取关键字字典。

    For backward compatibility, this function returns the embedded keyword dictionary.
    Previously, this function would lazy-load from a YAML file, but now it returns
    the embedded configuration.

    Returns:
        Dict: The keyword dictionary containing crop and soil mappings.
    """
    return KW_DICTIONARY


TestData = Literal[
    "soil", "tmin", "tmax", "prec", "pet", "mete", "1993", "1994", "demo"
]
METE_VARS = ("MinTemp", "MaxTemp", "Precipitation", "ReferenceET")
TEST_PATTERN = "test_{var}_CMFD_01dy_010deg_%Y01-%Y12.nc"
_DEMO_PATTERN = "mete/test_{var}_CMFD_01dy_010deg_199301-199312.nc"
_NAMES = {
    "soil": "soil_test.tif",
    "1993": "mete/test_mete_199301-199312.nc",
    "1994": "mete/test_mete_199401-199412.nc",
    "demo": "mete/test_mete_199301-199412.nc",
    "tmin": _DEMO_PATTERN.format(var="min_temp"),
    "tmax": _DEMO_PATTERN.format(var="max_temp"),
    "prec": _DEMO_PATTERN.format(var="prec_mm"),
    "pet": _DEMO_PATTERN.format(var="pet"),
}
METE_VAR_MAPPING = {
    "MinTemp": "min_temp",
    "MaxTemp": "max_temp",
    "Precipitation": "prec_mm",
    "ReferenceET": "pet",
}


def demo_climate_df() -> pd.DataFrame:
    """获取示例气象数据"""
    path = get_filepath("champion_climate.txt")
    return prepare_weather(path)


def get_test_data_path(file_name: Optional[TestData] = None) -> Path:
    """获取测试数据路径"""
    path = _RES_PATH
    if file_name is None:
        return Path(str(path))
    if file_name == "mete":
        return Path(str(path / "mete"))
    return Path(str(path / _NAMES[file_name]))


def clean_crop_type(crop: str) -> str:
    """清洗并检查作物类型是否有效"""
    crop = KW_DICTIONARY["crops"].get(crop, crop)
    if crop not in crop_params.keys():
        logger.critical(f"Unknown crop type: {crop}")
        raise ValueError(f"Unknown crop type: {crop}")
    return crop


def check_file_path(func=None, *, path_arg_name="path"):
    """Decorator to check if the file path exists."""
    if func is None:
        return lambda func: check_file_path(func, path_arg_name=path_arg_name)

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the path parameter based on its name or position
        path_index = (
            func.__code__.co_varnames.index(path_arg_name)
            if path_arg_name in func.__code__.co_varnames
            else 0
        )
        path = kwargs.get(
            path_arg_name, args[path_index] if path_index < len(args) else None
        )

        # Perform the path checks
        if isinstance(path, str):
            path = Path(path)
        if not isinstance(path, Path):
            raise ValueError(f"Invalid type for path: {type(path)}")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File {path} not found.")

        # Proceed with the original function
        return func(*args, **kwargs)

    return wrapper


def _apply_regionalized_adjustments(crop: Crop, crop_name: str) -> Crop:
    """Apply regionalized adjustments so Wheat fits local calendars.

    This aligns key time-dependent parameters (for Wheat) with the configured
    local growing period, optionally applying a chosen adjustment strategy and
    per-crop overrides.

    Args:
        crop: AquaCrop ``Crop`` instance to be adjusted.
        crop_name: Key of the crop in ``CROP_CONFIGS``.

    Returns:
        Crop: Adjusted crop instance (original object is modified and returned).
    """
    adj_config = REGIONALIZED_CROP_ADJUSTMENTS.get(crop_name)
    if not adj_config or not adj_config.get("enabled", False):
        return crop

    if crop.Name != "Wheat":
        return crop

    config = CROP_CONFIGS.get(crop_name)
    if not config:
        return crop

    actual_days = (config["end"] - config["start"]).days

    baseline = crop_params.get(crop.Name, {})
    baseline_senescence = float(baseline.get("SenescenceCD", 158.0))
    baseline_hi_start = float(baseline.get("HIstartCD", 127.0))

    # No calendar compression needed
    if actual_days >= baseline_senescence:
        custom_params = adj_config.get("custom_params", {})
        for param_name, param_value in custom_params.items():
            if hasattr(crop, param_name):
                setattr(crop, param_name, param_value)
                logger.debug(
                    f"Applied custom parameter override: {param_name}={param_value}"
                )
            else:
                logger.warning(
                    f"Custom parameter {param_name} does not exist on Crop object"
                )
        return crop

    strategy = adj_config.get("adjustment_strategy", "proportional")

    def _scale_time_params(ratio: float) -> None:
        time_params = (
            "Flowering",
            "FloweringCD",
            "Canopy10Pct",
            "Canopy10PctCD",
            "CanopyDevEnd",
            "CanopyDevEndCD",
            "MaxCanopy",
            "MaxCanopyCD",
        )
        for name in time_params:
            if hasattr(crop, name):
                original_val = getattr(crop, name)
                if isinstance(original_val, (int, float)) and original_val > 0:
                    setattr(crop, name, original_val * ratio)

    if strategy == "proportional":
        ratio = actual_days / baseline_senescence
        crop.SenescenceCD = actual_days
        crop.HIstartCD = int(baseline_hi_start * ratio)
    elif strategy == "conservative":
        crop.SenescenceCD = min(actual_days + 5, baseline_senescence)
        crop.HIstartCD = max(int(baseline_hi_start * 0.75), actual_days - 30)
    elif strategy == "aggressive":
        crop.SenescenceCD = max(actual_days - 5, 100)
        crop.HIstartCD = max(int(baseline_hi_start * 0.67), actual_days - 45)
        if hasattr(crop, "HI0"):
            crop.HI0 = crop.HI0 * 1.2
        if hasattr(crop, "CCx"):
            crop.CCx = crop.CCx * 1.1
    else:
        logger.warning(f"Unknown adjustment_strategy '{strategy}', using proportional")
        ratio = actual_days / baseline_senescence
        crop.SenescenceCD = actual_days
        crop.HIstartCD = int(baseline_hi_start * ratio)

    # Scale time-dependent parameters for all strategies based on the
    # compression/expansion relative to baseline senescence length.
    ratio = float(crop.SenescenceCD) / float(baseline_senescence)
    if ratio > 0:
        _scale_time_params(ratio)

    logger.debug(
        f"Applied regionalized adjustments to {crop_name}: "
        f"SenescenceCD={crop.SenescenceCD}, HIstartCD={crop.HIstartCD} "
        f"(strategy={strategy}, actual_days={actual_days})"
    )

    custom_params = adj_config.get("custom_params", {})
    for param_name, param_value in custom_params.items():
        if hasattr(crop, param_name):
            setattr(crop, param_name, param_value)
            logger.debug(
                f"Applied custom parameter override: {param_name}={param_value}"
            )
        else:
            logger.warning(
                f"Custom parameter {param_name} does not exist on Crop object"
            )

    return crop


def get_crop_dates(crop: str, folder: Optional[Path] = None) -> Dict[str, str]:
    """获取作物的种植和收获日期。

    Args:
        crop: str, the crop name.
        folder: Optional[Path], deprecated parameter for backward compatibility.

    Returns:
        Dict[str, str], dictionary with planting_date and harvest_date in MM/DD format.
    """
    if folder is not None:
        logger.warning(
            "The 'folder' parameter is deprecated and will be ignored. "
            "Crop configurations are now embedded in the package."
        )

    if crop not in CROP_CONFIGS:
        raise ValueError(
            f"Unknown crop: {crop}. Available crops: {list(CROP_CONFIGS.keys())}"
        )

    crop_config = CROP_CONFIGS[crop]
    start_dt: date = crop_config["start"]
    end_dt: date = crop_config["end"]
    return {
        "planting_date": start_dt.strftime(r"%m/%d"),
        "harvest_date": end_dt.strftime(r"%m/%d"),
    }


def crop_name_to_crop(
    crop_name: str,
    regionalized: bool = True,
    overrides: Optional[Dict[str, float]] = None,
) -> Crop:
    """Convert crop name to Crop object safely and robustly.

    This function handles the complete process of converting a crop name string
    into a valid AquaCrop Crop object. It performs validation, name cleaning,
    retrieves crop dates, and creates the Crop instance with proper error handling.

    The function supports both standard crop names (e.g., "Wheat", "Maize") and
    aliased names defined in the keyword dictionary. It ensures that all required
    crop parameters are available and properly configured before creating the
    Crop object.

    By default, this function applies regionalized parameter adjustments to adapt
    crops to local growing calendars (e.g., adjusting SenescenceCD and HIstartCD
    to match actual growing period length). This ensures crops work correctly with
    regional growing seasons rather than FAO default parameters.

    Args:
        crop_name: The name of the crop to convert. Can be either a standard
            AquaCrop crop name or an alias defined in the keyword dictionary.
        regionalized: Whether to apply regionalized parameter adjustments.
            Defaults to True. Set to False to use FAO default parameters.
        overrides: Optional direct parameter overrides applied after
            regionalization. Keys must be attributes on the AquaCrop Crop
            object (e.g., "HI0", "CCx", "HIstartCD").

    Returns:
        Crop: A fully initialized AquaCrop Crop object with planting and
            harvest dates configured, and optionally regionalized parameter
            adjustments applied.

    Raises:
        ValueError: If the crop name is invalid, not found in configurations,
            or if crop parameters cannot be retrieved. The error message will
            include available crop names for reference.
        TypeError: If the input is not a string.

    Example:
        >>> crop = crop_name_to_crop("Winter_Wheat")
        >>> print(crop.Name)
        'Wheat'
        >>> print(crop.planting_date)
        '10/01'

        >>> # Use FAO defaults without regionalization
        >>> crop_fao = crop_name_to_crop("Spring_Wheat", regionalized=False)

    Note:
        This function relies on embedded crop configurations and the keyword
        dictionary for name mapping. Ensure these resources are properly
        initialized before calling this function.

        Regionalized adjustments automatically adapt crop parameters (such as
        SenescenceCD, HIstartCD) to match the actual growing period defined in
        CROP_CONFIGS, ensuring crops can complete their growth cycle within the
        specified local growing season.
    """
    if not isinstance(crop_name, str):
        raise TypeError(f"Crop name must be a string, got {type(crop_name).__name__}")

    try:
        # Get crop dates using the original crop name (from CROP_CONFIGS)
        dates = get_crop_dates(crop_name)
        logger.debug(
            f"Retrieved dates for '{crop_name}': "
            f"planting={dates['planting_date']}, harvest={dates['harvest_date']}"
        )
    except ValueError as e:
        available_crops = list(CROP_CONFIGS.keys())
        raise ValueError(
            f"Failed to get dates for crop '{crop_name}': {e}. "
            f"Available crops with configurations: {available_crops}"
        ) from e

    try:
        # Clean and validate crop type for AquaCrop
        cleaned_crop = clean_crop_type(crop_name)
        logger.debug(
            f"Cleaned crop name '{crop_name}' to AquaCrop type '{cleaned_crop}'"
        )
    except ValueError as e:
        available_crops = list(CROP_CONFIGS.keys())
        available_aliases = list(KW_DICTIONARY.get("crops", {}).keys())
        raise ValueError(
            f"Failed to process crop '{crop_name}': {e}. "
            f"Available crops: {available_crops}. "
            f"Available aliases: {available_aliases}"
        ) from e

    try:
        # Create Crop object with the AquaCrop type name and dates
        crop = Crop(cleaned_crop, **dates)

        # Apply regionalized adjustments if enabled and needed
        if regionalized and crop_name in CROP_CONFIGS:
            crop = _apply_regionalized_adjustments(crop, crop_name)

        # Apply user overrides (highest priority)
        if overrides:
            for param_name, param_value in overrides.items():
                if hasattr(crop, param_name):
                    setattr(crop, param_name, param_value)
                    logger.debug(f"Applied user override: {param_name}={param_value}")
                else:
                    logger.warning(
                        f"Override parameter {param_name} does not exist on Crop object"
                    )

        logger.info(
            f"Successfully created Crop object for '{crop_name}' "
            f"(AquaCrop type: {cleaned_crop}, planting: {dates['planting_date']}, "
            f"harvest: {dates['harvest_date']}, regionalized={regionalized}, "
            f"overrides={bool(overrides)})"
        )
        return crop
    except Exception as e:
        raise ValueError(
            f"Failed to create Crop object for '{cleaned_crop}' with dates {dates}: {e}"
        ) from e


def check_climate_dataframe(df: pd.DataFrame) -> bool:
    """Check if the climate dataframe is valid for AquaCrop.

    Args:
        df: pd.DataFrame, the climate dataframe.

    Raises:
        NameError: if the name of the columns is not valid.
        TypeError: if the type of the columns is not valid.
        TimeoutError: if the time is not monotonic increasing.

    Returns:
        pd.DataFrame, the climate dataframe.
    """
    # 检查列名
    for i, col in enumerate(COLS):
        if col != df.columns[i]:
            raise NameError(f"No. {i} column {df.columns[i]} is not expected ({col}).")
    # 检查时间列
    if not df["Date"].dtype == "datetime64[ns]":
        raise TypeError("Date column must be datetime64[ns]")
    # 检查时间列是否连续
    if not df["Date"].is_monotonic_increasing:
        raise TimeoutError("Date column must be monotonic increasing.")
    return True
