# Crawlerd Web

**Crawlerd Web** 是分布式 `crawlframe` 系统的“总控塔”。它提供了一个集中的管理界面和 API，用于编排爬虫节点、管理项目、调度任务以及监控系统状态。该项目基于 **FastAPI** 构建，既作为 RESTful API 后端，也作为 React 前端仪表盘的宿主。

## ✨ 功能特性

- **集中式仪表盘**：提供现代化的 React 前端界面，用于可视化和管理您的爬虫基础设施。
- **节点管理**：注册、监控和管理分布式的爬虫节点 (Agent)。
- **项目编排**：管理爬虫项目的上传、版本和部署。
- **任务调度**：使用 `APScheduler` 调度和分发爬虫任务。
- **系统监控**：实时检查系统健康状态和节点连通性。
- **RESTful API**：提供全面的 API 接口，便于自动化和集成。

## 📦 安装与构建

本项目已采用现代 Python 包结构，支持直接安装或打包分发。

### 1. 源码直接安装

在 `crawlerd_web` 目录下直接安装：

```bash
pip install .
```

### 2. 打包为 Wheel

如果您需要分发安装包，可以使用 `build` 或 `uv` 工具进行打包：

```bash
# 安装打包工具
pip install build

# 执行打包
python -m build
# 或者如果您使用 uv
uv build
```

打包完成后，`.whl` 文件将生成在 `dist/` 目录下，您可以将该文件分发到服务器上安装：

```bash
pip install dist/crawlerd_web-0.1.0-py3-none-any.whl
```

## 🚀 启动与使用

安装完成后，系统会自动注册 `crawlerd-web` 命令行工具。

### 基本启动

**注意**：启动时**必须**指定 SQLite 数据库的存储路径。程序会自动创建所需的目录和数据库文件。

```bash
crawlerd-web --db-path ./crawlerd_data.db
```

默认监听端口为 **80**，启动后直接访问：[http://localhost](http://localhost)

### 自定义端口与地址

```bash
# 绑定到 8080 端口，监听所有网卡
crawlerd-web --db-path ./data.db --port 8080 --host 0.0.0.0
```

### 参数说明

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `--db-path` | SQLite 数据库文件路径 (必须) | 无 |
| `--port` | 服务监听端口 | 80 |
| `--host` | 服务绑定地址 | 0.0.0.0 |


## 🛠️ 开发指南

### 开发模式安装

如果您正在开发此项目，建议使用“可编辑模式”安装，这样修改代码后无需重新安装：

```bash
pip install -e .
```


## 🔌 API 文档

- **详细设计文档** [项目详细文档](./document.md)

## 📂 项目结构

```
crawlerd_web/
├── src/
│   └── crawlerd_web/
│       ├── api/            # API 路由定义
│       ├── static/         # 编译后的 React 前端资源 (自动打包)
│       ├── main.py         # 程序入口与 CLI 定义
│       └── database.py     # 数据库连接与初始化
├── pyproject.toml          # 项目构建配置与依赖
├── MANIFEST.in             # 资源文件包含规则
└── README.md               # 说明文档
```
