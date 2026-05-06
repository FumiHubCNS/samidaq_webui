from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AGASA_REPO = PROJECT_ROOT / "agasa"
AGASA_BACKEND = AGASA_REPO / "Backend"

print(AGASA_REPO)

sys.path.insert(0, str(AGASA_BACKEND))

from helpers.backEndHelpers import bitValueConversionAGASAv3

default_path = AGASA_BACKEND / "config" / "general" / "default_AGASAv3_config.json"
bitmap_path = AGASA_BACKEND / "config" / "general" / "AGASAv3_spi_bitmap.json"

channels = [
    {
        "id": 1,
        "output": True,
        "polarity": "positive",
        "testpulse": False,
        "threshold": 0.0,
        "csa_res": 0,
        "pzc_res": 0,
        "shp_res": 0.0,
        "csa_cap": 0,
        "pzc_cap": 0,
        "shp_cap": 0,
    }
]

converted = bitValueConversionAGASAv3(
    str(default_path),
    str(bitmap_path),
    {"channels": channels},
)

print(converted)