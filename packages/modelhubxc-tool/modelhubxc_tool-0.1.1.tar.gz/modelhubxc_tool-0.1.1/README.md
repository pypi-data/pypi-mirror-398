# modelhubxc-tool

一个用于从 ModelScope 和 Hugging Face 等平台下载模型的命令行工具。

## 简介

`modelhubxc-tool` 是一个命令行工具，旨在简化从 ModelScope 和 Hugging Face 等模型平台下载模型的过程。它支持从多个平台下载模型，并提供了便捷的查询功能来获取模型信息。

## 功能

- 从 ModelScope 和 Hugging Face 下载模型
- 查询模型信息
- 支持批量下载（通过 CSV 文件）
- 配置文件管理
- 可自定义下载路径和缓存目录

## 安装

使用 pip 安装：

```bash
pip install modelhubxc-tool
```

## 使用方法

### 1. 下载模型

从 ModelScope 下载模型：

```bash
modelhubxc-tool download --source modelscope owner/model-name
```

从 Hugging Face 下载模型：

```bash
modelhubxc-tool download --source huggingface owner/model-name
```

### 2. 查询模型信息

查询模型的详细信息：

```bash
modelhubxc-tool query owner/model-name
```

### 3. 批量下载

通过 CSV 文件批量下载模型，CSV 文件格式为：

```
model-id,source
owner/model1,modelscope
owner/model2,huggingface
```

批量下载命令：

```bash
modelhubxc-tool download-by-csv path/to/your/csv/file.csv
```

### 4. 查看版本

查看工具版本：

```bash
modelhubxc-tool --version
```

## 配置

工具会在 `~/.config/modelhubxc/config.yaml` 创建配置文件，包含以下可配置项：

- `download_dir`: 下载目录路径
- `cache_dir`: 缓存目录路径
- `max_workers`: 最大并发下载线程数
- `cookie_file`: Cookie 文件路径
- `token`: 认证令牌

首次运行时，如果下载目录未配置，工具会提示输入下载路径。

## 依赖

- typer (>=0.20.1,<0.21.0)
- pyyaml (>=6.0.3,<7.0.0)
- requests (>=2.31.0,<3.0.0)
- rich (>=13.0.0,<14.0.0)
- modelscope (>=1.33.0,<2.0.0)
- huggingface-hub (>=1.2.3,<2.0.0)

## 开发

```bash
git clone <repository-url>
cd modelhubxc-tool
pip install -e .
```

## 许可证

此项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 作者

张宇 <v-zhangyu03@4paradigm.com>