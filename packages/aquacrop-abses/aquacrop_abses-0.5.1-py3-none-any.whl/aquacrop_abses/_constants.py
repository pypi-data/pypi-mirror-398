#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Internal constants and configurations.

This module contains all configuration data that was previously stored in YAML files.
By embedding configurations directly in Python, we avoid packaging and resource loading issues.
"""

from datetime import date
from typing import Any, Dict, TypedDict


class CropConfig(TypedDict):
    """Configuration for a single crop."""

    Kc_end: float
    Kc_ini: float
    Kc_mid: float
    height: float
    index: int
    name_ch: str
    name_en: str
    start: date
    ini: date
    dev: date
    mid: date
    end: date


# Keyword mappings for crop and soil types
KW_DICTIONARY: Dict[str, Dict[str, str]] = {
    "crops": {
        "Rice": "PaddyRice",
        "RegionalRice": "PaddyRice",
        "Winter_Wheat": "Wheat",
        "Spring_Wheat": "Wheat",
        "RegionalWheat": "Wheat",
        "Spring_Maize": "Maize",
        "Summer_Maize": "Maize",
        "RegionalMaize": "Maize",
        "Groundnut": "DryBean",
        "Millet": "Sorghum",
        "Rapeseed": "Sunflower",
        "Spring_Barley": "Barley",
        "Sugarbeet": "SugarBeet",
        "Sugarcane": "SugarCane",
        "Winter_Barley": "Barley",
    },
    "soil": {
        "Loam": "Loam",
        "Loamy sand": "LoamySand",
        "Silt loam": "SiltLoam",
        "Clay loam": "ClayLoam",
        "Sandy loam": "SandyLoam",
        "Sandy clay loam": "SandyClayLoam",
        "Clay (light)": "Clay",
    },
}


# Crop configurations with planting/harvest dates and parameters
CROP_CONFIGS: Dict[str, CropConfig] = {
    "Cotton": {
        "Kc_end": 0.6,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 1.3,
        "index": 11,
        "name_ch": "棉花",
        "name_en": "Cotton",
        "start": date(2000, 4, 5),
        "ini": date(2000, 5, 5),
        "dev": date(2000, 6, 24),
        "mid": date(2000, 8, 18),
        "end": date(2000, 10, 2),
    },
    "Groundnut": {
        "Kc_end": 0.6,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 0.4,
        "index": 9,
        "name_ch": "花生",
        "name_en": "Groundnut",
        "start": date(2000, 5, 1),
        "ini": date(2000, 5, 26),
        "dev": date(2000, 6, 30),
        "mid": date(2000, 8, 14),
        "end": date(2000, 9, 8),
    },
    "Millet": {
        "Kc_end": 0.3,
        "Kc_ini": 0.15,
        "Kc_mid": 1.0,
        "height": 1.5,
        "index": 15,
        "name_ch": "小米",
        "name_en": "Millet",
        "start": date(2000, 4, 25),
        "ini": date(2000, 5, 15),
        "dev": date(2000, 6, 14),
        "mid": date(2000, 8, 8),
        "end": date(2000, 9, 12),
    },
    "Potato": {
        "Kc_end": 0.75,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 0.6,
        "index": 7,
        "name_ch": "马铃薯",
        "name_en": "Potato",
        "start": date(2000, 4, 25),
        "ini": date(2000, 5, 25),
        "dev": date(2000, 6, 29),
        "mid": date(2000, 8, 18),
        "end": date(2000, 9, 17),
    },
    "Rapeseed": {
        "Kc_end": 0.35,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 0.6,
        "index": 8,
        "name_ch": "油菜籽",
        "name_en": "Rapeseed",
        "start": date(2000, 4, 1),
        "ini": date(2000, 5, 1),
        "dev": date(2000, 5, 26),
        "mid": date(2000, 6, 25),
        "end": date(2000, 7, 20),
    },
    "Rice": {
        "Kc_end": 0.7,
        "Kc_ini": 1.05,
        "Kc_mid": 1.2,
        "height": 1.0,
        "index": 5,
        "name_ch": "水稻",
        "name_en": "Rice",
        "start": date(2000, 5, 15),
        "ini": date(2000, 6, 14),
        "dev": date(2000, 7, 14),
        "mid": date(2000, 9, 12),
        "end": date(2000, 10, 12),
    },
    "Soybean": {
        "Kc_end": 0.5,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 0.7,
        "index": 6,
        "name_ch": "大豆",
        "name_en": "Soybean",
        "start": date(2000, 5, 1),
        "ini": date(2000, 5, 21),
        "dev": date(2000, 6, 25),
        "mid": date(2000, 8, 24),
        "end": date(2000, 9, 18),
    },
    "Spring_Barley": {
        "Kc_end": 0.25,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 1.0,
        "index": 16,
        "name_ch": "春大麦",
        "name_en": "Spring_Barley",
        "start": date(2000, 4, 15),
        "ini": date(2000, 4, 30),
        "dev": date(2000, 5, 25),
        "mid": date(2000, 7, 14),
        "end": date(2000, 8, 13),
    },
    "Spring_Maize": {
        "Kc_end": 0.4,
        "Kc_ini": 0.15,
        "Kc_mid": 1.2,
        "height": 2.0,
        "index": 4,
        "name_ch": "春玉米",
        "name_en": "Spring_Maize",
        "start": date(2000, 4, 20),
        "ini": date(2000, 5, 20),
        "dev": date(2000, 6, 24),
        "mid": date(2000, 8, 13),
        "end": date(2000, 9, 12),
    },
    "Spring_Wheat": {
        "Kc_end": 0.3,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 1.0,
        "index": 2,
        "name_ch": "春小麦",
        "name_en": "Spring_Wheat",
        "start": date(2000, 3, 20),
        "ini": date(2000, 4, 9),
        "dev": date(2000, 4, 29),
        "mid": date(2000, 6, 28),
        "end": date(2000, 7, 28),
    },
    # Regionalized preset for external usage (maps to AquaCrop 'Wheat')
    "RegionalWheat": {
        "Kc_end": 0.3,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 1.0,
        "index": 2,
        "name_ch": "区域化小麦",
        "name_en": "RegionalWheat",
        # Use local calendar (Spring Wheat calendar by default)
        "start": date(2000, 3, 20),
        "ini": date(2000, 4, 9),
        "dev": date(2000, 4, 29),
        "mid": date(2000, 6, 28),
        "end": date(2000, 7, 28),
    },
    # Regionalized preset for Maize (maps to AquaCrop 'Maize')
    "RegionalMaize": {
        "Kc_end": 0.4,
        "Kc_ini": 0.15,
        "Kc_mid": 1.2,
        "height": 2.0,
        "index": 4,
        "name_ch": "区域化玉米",
        "name_en": "RegionalMaize",
        # Use Spring Maize calendar by default
        "start": date(2000, 4, 20),
        "ini": date(2000, 5, 20),
        "dev": date(2000, 6, 24),
        "mid": date(2000, 8, 13),
        "end": date(2000, 9, 12),
    },
    # Regionalized preset for Rice (maps to AquaCrop 'PaddyRice')
    "RegionalRice": {
        "Kc_end": 0.7,
        "Kc_ini": 1.05,
        "Kc_mid": 1.2,
        "height": 1.0,
        "index": 5,
        "name_ch": "区域化水稻",
        "name_en": "RegionalRice",
        # Use Rice calendar
        "start": date(2000, 5, 15),
        "ini": date(2000, 6, 14),
        "dev": date(2000, 7, 14),
        "mid": date(2000, 9, 12),
        "end": date(2000, 10, 12),
    },
    "Sugarbeet": {
        "Kc_end": 0.7,
        "Kc_ini": 0.35,
        "Kc_mid": 1.2,
        "height": 0.5,
        "index": 13,
        "name_ch": "甜菜",
        "name_en": "Sugarbeet",
        "start": date(2000, 4, 15),
        "ini": date(2000, 5, 10),
        "dev": date(2000, 6, 14),
        "mid": date(2000, 8, 3),
        "end": date(2000, 9, 22),
    },
    "Sugarcane": {
        "Kc_end": 0.75,
        "Kc_ini": 0.4,
        "Kc_mid": 1.25,
        "height": 3.0,
        "index": 12,
        "name_ch": "甘蔗",
        "name_en": "Sugarcane",
        "start": date(2000, 4, 1),
        "ini": date(2000, 4, 21),
        "dev": date(2000, 5, 16),
        "mid": date(2000, 6, 20),
        "end": date(2000, 7, 15),
    },
    "Summer_Maize": {
        "Kc_end": 0.5,
        "Kc_ini": 0.15,
        "Kc_mid": 1.2,
        "height": 2.0,
        "index": 3,
        "name_ch": "夏玉米",
        "name_en": "Summer_Maize",
        "start": date(2000, 6, 15),
        "ini": date(2000, 6, 30),
        "dev": date(2000, 7, 30),
        "mid": date(2000, 8, 29),
        "end": date(2000, 9, 23),
    },
    "Sunflower": {
        "Kc_end": 0.35,
        "Kc_ini": 0.15,
        "Kc_mid": 1.1,
        "height": 2.0,
        "index": 18,
        "name_ch": "向日葵",
        "name_en": "Sunflower",
        "start": date(2000, 4, 20),
        "ini": date(2000, 5, 15),
        "dev": date(2000, 6, 19),
        "mid": date(2000, 8, 3),
        "end": date(2000, 8, 28),
    },
    "Tomato": {
        "Kc_end": 0.8,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 0.6,
        "index": 10,
        "name_ch": "西红柿",
        "name_en": "Tomato",
        "start": date(2000, 4, 15),
        "ini": date(2000, 5, 15),
        "dev": date(2000, 6, 24),
        "mid": date(2000, 8, 3),
        "end": date(2000, 8, 28),
    },
    "Winter_Barley": {
        "Kc_end": 0.25,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 1.0,
        "index": 17,
        "name_ch": "冬大麦",
        "name_en": "Winter_Barley",
        "start": date(2000, 11, 5),
        "ini": date(2001, 2, 23),
        "dev": date(2001, 3, 25),
        "mid": date(2001, 5, 4),
        "end": date(2001, 6, 3),
    },
    "Winter_Wheat": {
        "Kc_end": 0.3,
        "Kc_ini": 0.4,
        "Kc_mid": 1.15,
        "height": 1.0,
        "index": 1,
        "name_ch": "冬小麦",
        "name_en": "Winter_Wheat",
        "start": date(2000, 10, 1),
        "ini": date(2001, 2, 3),
        "dev": date(2001, 3, 30),
        "mid": date(2001, 5, 24),
        "end": date(2001, 6, 13),
    },
    # Backward compatibility aliases
    "Wheat": {
        "Kc_end": 0.3,
        "Kc_ini": 0.15,
        "Kc_mid": 1.15,
        "height": 1.0,
        "index": 2,
        "name_ch": "春小麦",
        "name_en": "Spring_Wheat",
        "start": date(2000, 3, 20),
        "ini": date(2000, 4, 9),
        "dev": date(2000, 4, 29),
        "mid": date(2000, 6, 28),
        "end": date(2000, 7, 28),
    },
    "Maize": {
        "Kc_end": 0.4,
        "Kc_ini": 0.15,
        "Kc_mid": 1.2,
        "height": 2.0,
        "index": 4,
        "name_ch": "春玉米",
        "name_en": "Spring_Maize",
        "start": date(2000, 4, 20),
        "ini": date(2000, 5, 20),
        "dev": date(2000, 6, 24),
        "mid": date(2000, 8, 13),
        "end": date(2000, 9, 12),
    },
}


# Default model configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "model": {
        "name": "AquaCrop-ABSESpy",
        "version": "0.1.0",
        "random_seed": 42,
    },
    "farmer": {
        "irr_method": 4,  # Default to net irrigation
        "crops": [],  # No crops by default
    },
    "paths": {
        "weather": "data/weather",
        "soil": "data/soil",
        "output": "output",
    },
}


# Regionalized crop parameter adjustment configurations
# These allow crops to adapt to local growing calendars instead of FAO defaults
REGIONALIZED_CROP_ADJUSTMENTS: Dict[str, Dict[str, Any]] = {
    "Spring_Wheat": {
        "enabled": True,  # Enable regionalized adjustments for Spring_Wheat
        "adjustment_strategy": "aggressive",  # Options: "proportional", "conservative", "aggressive"
        # Custom parameter overrides (will be applied after proportional adjustment)
        "custom_params": {
            # Optimized combination for 130-day growing season
            # Tested results:
            #   - Base aggressive: ~2.80 tonne/ha
            #   - With HI+20%, CCx+10%, HIstartCD=85: ~3.97 tonne/ha
            # These can be fine-tuned per region if needed
            # "HI0": 0.576,  # HI0 * 1.2 (48% * 1.2)
            # "CCx": 1.056,  # CCx * 1.1 (0.96 * 1.1)
            # "HIstartCD": 85,  # Earlier yield formation start
        },
    },
    "RegionalWheat": {
        "enabled": True,
        "adjustment_strategy": "aggressive",
        # Default to optimized combo for 130-day season; can be reconfigured by users
        "custom_params": {
            # Provide deterministic absolute values so external usage is stable
            "HI0": 0.576,  # 0.48 * 1.2
            "CCx": 1.056,  # 0.96 * 1.1
            "HIstartCD": 85,
        },
    },
    "Winter_Wheat": {
        "enabled": True,
        "adjustment_strategy": "proportional",
        "custom_params": {},
    },
    "RegionalMaize": {
        "enabled": True,
        "adjustment_strategy": "aggressive",
        # Optimized parameters for target yield ~6.7005 t/ha
        # Optimized using CropParameterOptimizer
        "custom_params": {
            "HI0": 0.5082,  # Optimized harvest index
            "CCx": 1.0377,  # Optimized maximum canopy cover
            "HIstartCD": 107,  # Optimized days to harvest index start
        },
    },
    "RegionalRice": {
        "enabled": True,
        "adjustment_strategy": "aggressive",
        # Optimized parameters for target yield ~6.561 t/ha
        # Optimized using CropParameterOptimizer
        "custom_params": {
            "HI0": 0.5082,  # Optimized harvest index
            "CCx": 1.0377,  # Optimized maximum canopy cover
            "HIstartCD": 117,  # Optimized days to harvest index start
        },
    },
    # Add other crops that need regionalization here
}


# Farmer irrigation method configurations
FARMER_IRR_CONFIGS: Dict[int, Dict[str, Any]] = {
    0: {
        "irrigation": {
            "enabled": False,
            "method": 0,
        },
    },
    1: {
        "optimization": {
            "max_iter": 100,
            "size_pop": 50,
        },
        "thresholds": {
            "emergence": 80,
            "canopy": 70,
        },
    },
    2: {
        "optimization": {
            "max_iter": 100,
            "size_pop": 50,
        },
        "thresholds": {
            "emergence": 70,
            "canopy": 60,
        },
    },
    3: {
        "optimization": {
            "max_iter": 100,
            "size_pop": 50,
        },
        "thresholds": {
            "emergence": 50,
            "canopy": 40,
        },
    },
    4: {
        "target_depletion": 0,
        "application_efficiency": 1.0,
    },
    5: {
        "optimization": {
            "max_iter": 100,
            "size_pop": 50,
        },
        "thresholds": {
            "emergence": 90,
            "canopy": 80,
        },
    },
}
