import typer
from pathlib import Path
from typer import Context
from .commands import download, query, download_by_csv
from modelhubxc_tool.service.version_check import check_version


def version_callback(value: bool):
    if value:
        import importlib.metadata
        try:
            version_str = importlib.metadata.version("modelhubxc-tool")
            typer.echo(f"modelhubxc-tool {version_str}")
        except importlib.metadata.PackageNotFoundError:
            typer.echo("modelhubxc-tool 0.1.0")  # fallback version
        raise typer.Exit()


def config_callback(
    ctx: Context,
    config_file: Path = typer.Option(
        Path.home() / ".config" / "modelhubxc" / "config.yaml",
        "--config-file",
        "-c",
        help="Configuration file path",
        exists=False,
        dir_okay=False,
        writable=False,
        readable=True
    ),
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback, help="Show version and exit") # NOQA
):
    # Store the config file path in the context so it can be accessed by commands
    ctx.obj = {"config_file": config_file}
    
    # Print info about the config file
    if config_file.exists():
        typer.echo(f"配置文件路径: {config_file}")
    else:
        typer.echo(f"配置文件路径不存在将使用默认路径: {config_file}")

# check_version()

app = typer.Typer(callback=config_callback)
app.command()(download)
app.command()(query)
app.command()(download_by_csv)


if __name__ == "__main__":
    app()
