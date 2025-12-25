# FastAPI Toolbox

这是一个Python库，提供FastAPI开发时的常用工具和功能，包括静态文件缓存控制和高级日志系统。

## 安装

```bash
uv add fastapi-toolbox
```

```bash
pip install fastapi-toolbox
```

## 功能特性

### 运行服务器

`fastapi-toolbox` 提供了基于 loguru 的高级日志系统，支持多进程环境下的日志配置。

#### 基本用法

```python
from fastapi import FastAPI
from fastapi_toolbox import logger, run_server
import uvicorn
import logging

app = FastAPI()

@app.get("/")
async def read_root():
    logger.info("Hello World访问")
    return {"Hello": "World"}

if __name__ == "__main__":

    def filter_sqlalchemy(record):
        if record.name.startswith("sqlalchemy"):
            if record.levelno < logging.ERROR:
                return True

    run_server(
        "main:app",
        host="127.0.0.1",
        port=8000,
        workers=1,
        log_file="logs/app.log", # 日志轮转
        filter_callbacks=[filter_sqlalchemy]
    )
```


#### 环境变量配置

- `LOG_LEVEL`: 设置日志级别（DEBUG, INFO, WARNING, ERROR），默认INFO
- `JSON_LOGS`: 设置为"1"启用JSON格式日志，默认为标准格式

#### 主要特性

- **多进程支持**：`UvicornConfig` 确保多进程环境下日志正常工作
- **自动轮转**：支持按文件大小和时间进行日志轮转
- **统一拦截**：自动拦截标准库logging并转发到loguru
- **灵活配置**：支持环境变量和代码配置

### StaticFilesCache

`StaticFilesCache` 是 FastAPI StaticFiles 的增强版本，为静态文件提供可配置的缓存控制功能。

#### 基本用法

```python
from fastapi import FastAPI
from fastapi_toolbox import StaticFilesCache
import os

app = FastAPI()

# 示例1：使用默认缓存策略（禁用缓存）
front_folder = os.path.join(os.path.dirname(__file__), "frontend/dist")
app.mount("/", StaticFilesCache(directory=front_folder), name="static")

# 示例2：使用自定义缓存策略
app.mount("/static", StaticFilesCache(
    directory="static_files",
    cachecontrol="max-age=3600"  # 缓存1小时
), name="static")
```

#### 主要特性

- **自动缓存控制**：自动为 `.html` 和 `.txt` 文件添加 Cache-Control 响应头
- **可配置策略**：通过 `cachecontrol` 参数自定义缓存行为
- **完全兼容**：继承自 FastAPI StaticFiles，保留所有原有功能

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `directory` | 静态文件目录路径 | 必填 |
| `cachecontrol` | Cache-Control 头的值 | `"no-cache, no-store, must-revalidate"` |
| 其他参数 | 与标准 StaticFiles 相同 | - |

#### 常用缓存策略

```python
# 禁用缓存（适合开发环境）
cachecontrol="no-cache, no-store, must-revalidate"

# 短期缓存（适合经常更新的资源）
cachecontrol="max-age=3600"  # 1小时

# 长期缓存（适合不常变动的资源）
cachecontrol="public, max-age=86400"  # 1天

# 私有缓存，必须重新验证
cachecontrol="private, must-revalidate"
```

#### 实际应用场景

适用于需要为前端SPA应用提供静态文件服务的场景：

```python
# 访问 http://127.0.0.1:8000/index.html 即可访问前端页面
front_folder = os.path.join(os.path.dirname(__file__), "frontend/dist")
app.mount("/", StaticFilesCache(directory=front_folder), name="static")
```

这样配置后，HTML文件将不会被浏览器缓存，确保用户总是获取最新版本的前端应用。

## 构建

uv build

## 发布

uv publish

输入__token__作为用户名 然后输入pypi的token

## License

MIT