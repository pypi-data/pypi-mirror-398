import logging
from http.cookiejar import FileCookieJar
from modelhubxc_tool.enums import SourceEnum
from pathlib import Path
from modelhubxc_tool.service.downloader.modelscope_downloader import ModelScopeDownloader
from modelhubxc_tool.service.downloader.huggingface_downloader import HuggingFaceDownloader

logger = logging.getLogger(__name__)

def do_download(model_id: str, download_path: Path, source: SourceEnum, **kwargs):
    """
    Download model by model ID from specified source platform
    """
    logger.info(f"Downloading model {model_id} from {source.value} to {download_path}")

    DownloaderClass = { # NOQA
        SourceEnum.huggingface: HuggingFaceDownloader,
        SourceEnum.modelscope: ModelScopeDownloader,
    }[source]

    cookies = None
    if kwargs.get("cookie_file", None):
        cookies = FileCookieJar()
        cookies.load(kwargs["cookie_file"])

    if not download_path.exists():
        download_path.mkdir(parents=True, exist_ok=True)

    DownloaderClass.snapshot_download(
        repo_id = model_id,
        revision = kwargs.get("revision", None) or None,
        cache_dir = kwargs.get("cache_dir", None) or None,
        local_dir = download_path,
        repo_type = 'model',
        allow_patterns = kwargs.get("allow_patterns", None) or None,
        ignore_patterns = kwargs.get("ignore_patterns", None) or None,
        headers = None,
        local_files_only = False,
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        max_workers = int(kwargs.get("max_workers", None) or 8),
        force_download = False,
        token = kwargs.get("token", None) or None,
        library_name = None,
        library_version = None,
        dry_run = bool(kwargs.get("dry_run", False)),
        etag_timeout = 10,
        endpoint = "https://hf-mirror.com",
        cookies = cookies
    )
