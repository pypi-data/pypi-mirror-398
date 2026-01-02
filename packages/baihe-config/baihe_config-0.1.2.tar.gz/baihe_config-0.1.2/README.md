# baihe-config

基于 Pydantic 的结构化配置管理工具，支持配置的持久化与自动保存，适用于需要高可靠性和易用性的 Python 应用配置场景。

## 特性

- 基于 Pydantic，类型安全、易于扩展
- 支持配置自动持久化到本地 JSON 文件
- 支持自动加载和保存配置变更
- 适用于需要高可靠性和易用性的 Python 应用

## 安装

建议使用 [uv](https://github.com/astral-sh/uv) 或 [pip](https://pip.pypa.io/) 进行安装：

```bash
# 使用pip
pip install baihe-config

# 使用uv
uv add baihe-config
# 或
uv pip install baihe-config
```

## 快速开始

```python
from baihe_config import BaseConfig

class AppConfig(BaseConfig):
    username: str = "admin"
    password: str = "123456"

# 创建配置对象，启用持久化
config = AppConfig(persistent=True, filepath="app_config.json")

# 修改配置会自动保存到文件
config.username = "new_user"

# 重新加载配置
config.load()
```

## 参数说明

- `persistent`：是否启用持久化（bool，默认 False）
- `filepath`：持久化文件路径（str or Path，可选，默认以类名生成到当前工作目录）

## 依赖

- Python >= 3.11
- pydantic >= 2.11.7

## 作者

- jiangbaihe <baiheqiuhan@qq.com>
