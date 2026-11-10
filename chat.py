"""本地体验入口（零安装，直接跑）。

用法：
    python chat.py "我的快递到哪了 2024110001"
    python chat.py "双11买的衣服7天无理由退货吗"

说明：这个文件只做一件事——把 src 加进模块搜索路径，
让你不用 pip install 也能直接体验服务。生产环境不会这么干。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ecom_cs.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
