from http.cookiejar import CookieJar
from pathlib import Path
from typing import Optional, Union, List, Dict

from modelscope import snapshot_download

from modelhubxc_tool.service.downloader.downloader import BaseDownloader


class ModelScopeDownloader(BaseDownloader):

    @classmethod
    def snapshot_download(cls, repo_id: str, *, revision: Optional[str] = None,
                          cache_dir: Optional[Union[str, 'Path']] = None,
                          local_dir: Optional[Union[str, 'Path']] = None, repo_type: Optional[str] = 'model',
                          allow_patterns: Optional[Union[List[str], str]] = None,
                          ignore_patterns: Optional[Union[List[str], str]] = None, headers: Optional[Dict] = None,
                          local_files_only: bool = False, user_agent: Optional[Union[str, Dict]] = None,
                          max_workers: int = 8, force_download: bool = False, token: Optional[Union[bool, str]] = None,
                          library_name: Optional[str] = None, library_version: Optional[str] = None,
                          dry_run: bool = False, etag_timeout: float = 10,
                          endpoint: Optional[str] = "https://hf-mirror.com", cookies: Optional[CookieJar] = None) -> str:
        return snapshot_download(
            model_id = repo_id,
            revision = revision,
            cache_dir = cache_dir,
            user_agent = user_agent,
            local_files_only = local_files_only,
            cookies = cookies,
            local_dir = local_dir,
            allow_patterns = allow_patterns,
            ignore_patterns = ignore_patterns,
            max_workers = max_workers,
            repo_type = repo_type,
            enable_file_lock = True,
        )
