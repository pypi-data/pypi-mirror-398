# Zampie Utils

一个实用的Python工具包，提供了一系列常用的工具函数。

## 功能特性

- 文件操作工具
- 计时器上下文管理器
- 表情符号和表情识别
- 概率触发器
- 会话保存功能
- 智能日志系统（支持自动滚动日志）

## 安装

```bash
pip install zampie_utils
```

## 使用示例

```python
from zampie_utils import ContextTimer, read_file
from zampie_utils.logger import Logger

# 使用计时器
with ContextTimer("my_task", "s"):
    # 你的代码
    pass

# 读取文件
content = read_file("path/to/your/file.txt")

# 使用滚动日志
logger = Logger()
# 添加文件处理器，设置最大文件大小为10MB，保留5个备份文件
logger.add_file_handler("app.log", max_bytes=10*1024*1024, backup_count=5)
logger.info("这是一条日志消息")
```

## PyPi

https://pypi.org/project/zampie-utils/
