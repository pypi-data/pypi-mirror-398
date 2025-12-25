#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
这个模块用于加载配置文件。
"""

import os
import tomllib
from importlib import resources
from pathlib import Path
from typing import Optional

from loguru import logger
from omegaconf import DictConfig, OmegaConf

from aquacrop_abses._constants import DEFAULT_CONFIG, FARMER_IRR_CONFIGS

# 配置文件路径（使用包内资源）
try:
    # Python 3.9+: 使用 files() API 访问包内资源
    CONFIG_DIR = resources.files("aquacrop_abses").joinpath("config")
except (TypeError, AttributeError):
    # 备用方案：使用 __file__
    CONFIG_DIR = Path(__file__).parent / "config"

DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"
FARMER_CONFIG_DIR = CONFIG_DIR / "farmer"
PROJECT_CONFIG_NAMES = ["aquacrop_abses.yaml", "aquacrop.yaml"]


def find_project_root(start_path: Path = Path.cwd()) -> Optional[Path]:
    """查找项目根目录（包含 pyproject.toml 的目录）。"""
    current = start_path.absolute()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return None


def get_config_from_pyproject() -> tuple[Optional[Path], Optional[DictConfig]]:
    """从 pyproject.toml 获取配置。

    Returns:
        tuple: (配置文件路径, 内联配置)
    """
    if not (root := find_project_root()):
        return None, None

    pyproject_path = root / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
    except FileNotFoundError:
        return None, None

    tool_config = pyproject.get("tool", {}).get("aquacrop-abses", {})

    # 获取配置文件路径
    if config_path := tool_config.get("config"):
        config_path = root / config_path
        if config_path.exists():
            return config_path, None

    # 获取内联配置
    if inline_config := tool_config.get("settings"):
        return None, OmegaConf.create(inline_config)

    return None, None


def get_config_path() -> tuple[Optional[Path], Optional[DictConfig]]:
    """获取用户配置文件路径和内联配置。

    按以下顺序查找配置:
    1. 环境变量 AQUACROP_CONFIG
    2. pyproject.toml 中指定的路径
    3. pyproject.toml 中的内联配置
    4. 项目根目录下的配置文件
    5. 当前目录下的配置文件
    6. 用户主目录下的配置文件
    """
    # 1. 环境变量
    if env_path := os.getenv("AQUACROP_CONFIG"):
        return Path(env_path), None

    # 2 & 3. pyproject.toml
    if (result := get_config_from_pyproject()) != (None, None):
        return result

    # 4. 项目根目录
    if root := find_project_root():
        for name in PROJECT_CONFIG_NAMES:
            if (config := root / name).exists():
                return config, None

    # 5. 当前目录
    for name in PROJECT_CONFIG_NAMES:
        if (config := Path.cwd() / name).exists():
            return config, None

    # 6. 用户主目录
    if (config := Path.home() / ".aquacrop_abses.yaml").exists():
        return config, None

    return None, None


def load_farmer_config(irr_method: int) -> DictConfig:
    """加载特定灌溉方式的配置。

    Args:
        irr_method: 灌溉方式编号

    Returns:
        该灌溉方式的配置
    """
    # 首先尝试从内嵌配置加载
    if irr_method in FARMER_IRR_CONFIGS:
        logger.debug(f"Using embedded config for irrigation method {irr_method}")
        return OmegaConf.create(FARMER_IRR_CONFIGS[irr_method])

    # 如果内嵌配置不存在，尝试从文件加载
    try:
        method_config = FARMER_CONFIG_DIR / f"irr_method_{irr_method}.yaml"
        if method_config.is_file():
            logger.debug(f"Loading irrigation config from {method_config}")
            return OmegaConf.load(method_config)
    except (FileNotFoundError, TypeError):
        pass

    raise ValueError(
        f"No config found for irrigation method {irr_method}. "
        f"Available methods: {list(FARMER_IRR_CONFIGS.keys())}"
    )


def _load_config(config_path: Optional[str | Path] = None) -> DictConfig:
    """加载配置文件。

    Args:
        config_path: 可选的用户配置文件路径

    Returns:
        合并后的配置对象
    """
    # 1. 加载默认配置（优先使用内嵌配置）
    try:
        config = OmegaConf.load(DEFAULT_CONFIG_PATH)
        logger.debug(f"Loaded default config from {DEFAULT_CONFIG_PATH}")
    except (FileNotFoundError, TypeError):
        logger.debug("Using embedded default config")
        config = OmegaConf.create(DEFAULT_CONFIG)

    # 2. 加载灌溉方式特定的配置
    irr_method = config.farmer.irr_method
    try:
        farmer_config = load_farmer_config(irr_method)
        config = OmegaConf.merge(config, {"farmer": farmer_config})
    except ValueError:
        pass  # 如果没有特定配置文件，使用默认配置

    # 3. 加载用户指定的配置
    if config_path:
        user_config = OmegaConf.load(config_path)
        return OmegaConf.merge(config, user_config)

    # 4. 尝试加载自动发现的配置
    path, inline_config = get_config_path()

    if path:
        user_config = OmegaConf.load(path)
        config = OmegaConf.merge(config, user_config)

    if inline_config:
        config = OmegaConf.merge(config, inline_config)

    return config


def get_config():
    """获取全局配置。"""
    if not hasattr(get_config, "config"):
        get_config.config = _load_config()
    return get_config.config
