import os
import re
from typing import Tuple

import typer
from pathlib import Path
from typer import Context
from modelhubxc_tool.enums import SourceEnum
from modelhubxc_tool.cli.config import Config
from modelhubxc_tool.service.download import do_download


def get_check_download_path_and_config(ctx: Context, model_id: str) -> Tuple[Path, Config]:
    if not re.match(r"^[\w.-]+/[\w.-]+$", model_id):
        typer.echo(f"模型ID {model_id} 格式错误，必须为 owner/model-name 格式", color=typer.colors.RED)
        raise typer.Exit(code=1)

    # Access the config file from context
    config_file = ctx.obj.get("config_file", Path.home() / ".config" / "modelhubxc" / "config.yaml") if ctx.obj else Path.home() / ".config" / "modelhubxc" / "config.yaml"
    
    # 加载配置
    config = Config.load(config_file)
    
    # 检查下载目录是否已配置
    if not config.download_dir:
        # 如果下载目录为空，提示用户输入
        default_download_dir = str(Path.home() / "Downloads")
        download_dir_input = typer.prompt(
            "请输入下载路径", 
            default=default_download_dir,
            type=Path
        )
        config.download_dir = str(download_dir_input)
        
        # 保存配置到文件
        if config.save(config_file):
            typer.echo(f"配置已保存到 {config_file}")
        else:
            typer.echo(f"保存配置到 {config_file} 失败")
    
    download_base_path = Path(config.download_dir)
    if not download_base_path.exists():
        typer.echo(f"下载路径 {download_base_path} 不存在")
        raise typer.Exit(code=1)
    if not download_base_path.is_dir():
        typer.echo(f"下载路径 {download_base_path} 不是目录")
        raise typer.Exit(code=1)
    if not os.access(download_base_path, os.W_OK):
        typer.echo(f"下载路径 {download_base_path} 没有写入权限")
        raise typer.Exit(code=1)

    download_path = Path(config.download_dir) / model_id
    typer.echo(f"下载路径: {download_path}")
    typer.echo(f"提示: 您可以直接修改配置文件 {config_file} 来更改下载路径")
    
    return download_path, config


def download(
    ctx: Context,
    source: SourceEnum = typer.Option(..., help="Source platform for the model"),
    model_id: str = typer.Argument(..., help="Model ID in format owner/model-name"),
):
    """
    Download model by model ID from specified source platform
    """
    # 检查并获取下载路径
    download_path, config = get_check_download_path_and_config(ctx, model_id.strip().strip("/"))
    do_download(
        model_id,
        download_path,
        source,
        cache_dir=config.cache_dir,
        max_workers=config.max_workers,
        cookie_file=config.cookie_file,
        token=config.token,
    )


def download_by_csv(
    ctx: Context,
    csv_file: Path = typer.Argument(..., help="Path to the CSV file containing model IDs"),
):
    """
    Download models by model IDs from specified source platform listed in a CSV file
    """
    # 检查并获取下载路径
    with open(csv_file, 'r', encoding='utf-8') as f:
        for line in f:
            row = line.strip()
            if not row:
                continue
            if "," not in row:
                typer.echo(f"跳过无效行: {row}", color=typer.colors.YELLOW)
                continue
            model_id = line.strip().split(',')[0].strip().strip("/")
            source = line.strip().split(',')[1]
            try:
                source_enum = SourceEnum(source)
            except ValueError:
                typer.echo(f"跳过无效行: {row}，源平台 {source} 无效", color=typer.colors.YELLOW)
                continue

            download_path, config = get_check_download_path_and_config(ctx, model_id)
            do_download(
                model_id,
                download_path,
                source_enum,
                cache_dir=config.cache_dir,
                max_workers=config.max_workers,
                cookie_file=config.cookie_file,
                token=config.token,
            )
