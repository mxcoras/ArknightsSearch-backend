import os
from typing import Literal

cwd = os.getcwd()

# 输出数据
data_path = os.path.join(cwd, 'data')

support_language = Literal['zh_CN']
