import typer
import sys
import requests
import importlib.metadata

def get_version():
    try:
        version_str = importlib.metadata.version("modelhubxc-tool")
        return version_str
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"  # fallback version


def get_version_from_pipy():
    # TODO 为了防止 block 从 阿里云的镜像爬虫吧 https://mirrors.aliyun.com/pypi/simple/requests/
    try:
        response = requests.get("https://pypi.org/pypi/modelhubxc-tool/json")
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except requests.RequestException:
        return "0.0.0"  # fallback version


def check_version():
    version_str = get_version()
    version_from_pipy = get_version_from_pipy()
    if version_str == "0.0.0" or version_from_pipy == "0.0.0":
        return
    
    if version_from_pipy.split(".")[0] != version_str.split(".")[0] or version_from_pipy.split(".")[1] != version_str.split(".")[1]:
        typer.echo(f"🔥🔥🔥 modelhubxc-tool 最新版本{version_from_pipy} 在 pypi 发布了, 与本地版本差距大，请更新后使用", err=True)
        sys.exit(1)
    
    if version_from_pipy.split(".")[2] != version_str.split(".")[2]:
        typer.echo(f"🔥🔥🔥 modelhubxc-tool 最新版本{version_from_pipy} 在 pypi 发布了")
    return
