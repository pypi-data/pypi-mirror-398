from pathlib import Path
from typing import List, Union

import i18n

from .locales import *

INNER_LOCALES_DIR = Path(__file__).parent.joinpath("locales")

# 设置默认语言
i18n.set("locale", "zh")
i18n.set("fallback", "en")
i18n.set("filename_format", "{locale}.{format}")
i18n.set("skip_locale_root_data", True)
if INNER_LOCALES_DIR.exists():
    i18n.load_path.append(str(INNER_LOCALES_DIR))


def add_locale_dir(path: Union[str, List[str]]):
    """
    添加语言包目录
    Args:
        path: 语言包目录
    """
    if isinstance(path, (str, Path)):
        paths = [path]
    else:
        paths = path

    for p in paths:
        i18n.load_path.append(p)
