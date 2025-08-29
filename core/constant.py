from pathlib import Path
from typing import Literal

project_root = Path(__file__).parent.parent

# 输出数据
data_path = project_root / "data"

support_language = Literal["zh_CN", "ja_JP", "en_US"]
default_lang = "zh_CN"
