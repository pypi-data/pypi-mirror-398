import abc
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
from http.cookiejar import CookieJar

from huggingface_hub import DryRunFileInfo


class BaseDownloader(abc.ABC):
    """
    抽象类，定义了基础的下载接口
    """
    @classmethod
    @abc.abstractmethod
    def snapshot_download(
        cls,
        repo_id: str,  # HuggingFace Hub 参数, ModelScope 中对应 model_id (当 repo_id 不存在时)
        *,
        revision: Optional[str] = None,  # 两个库都有
        cache_dir: Optional[Union[str, 'Path']] = None,  # 两个库都有
        local_dir: Optional[Union[str, 'Path']] = None,  # 两个库都有
        repo_type: Optional[str] = 'model',  # HuggingFace Hub 参数, ModelScope 也有
        allow_patterns: Optional[Union[List[str], str]] = None,  # 两个库都有 (ModelScope 为了兼容 HuggingFace)
        ignore_patterns: Optional[Union[List[str], str]] = None,  # 两个库都有 (ModelScope 为了兼容 HuggingFace)
        headers: Optional[Dict] = None,  # 两个库都有
        local_files_only: bool = False,  # 两个库都有
        user_agent: Optional[Union[str, Dict]] = None,  # 两个库都有
        max_workers: int = 8,  # HuggingFace Hub 参数 (默认值8), ModelScope 默认值8

        force_download: bool = False,  # HuggingFace Hub 参数
        token: Optional[Union[bool, str]] = None,  # HuggingFace Hub 参数
        library_name: Optional[str] = None,  # HuggingFace Hub 参数
        library_version: Optional[str] = None,  # HuggingFace Hub 参数
        dry_run: bool = False,  # HuggingFace Hub 参数
        etag_timeout: float = 10,  # HuggingFace Hub 参数 (默认值10)
        endpoint: Optional[str] = "https://hf-mirror.com",  # HuggingFace Hub 参数

        cookies: Optional[CookieJar] = None,  # ModelScope 特有参数
    ) -> Union[str, List['DryRunFileInfo']]:  # HuggingFace 返回 str 或 DryRunFileInfo 列表, ModelScope 返回 str
        """
        下载模型仓库的快照
        
        Args:
            repo_id (str): 模型仓库 ID，格式为 "user/repo_name"
                           在 ModelScope 中对应 model_id 参数
            revision (str, optional): Git 版本，分支名或标签
            cache_dir (str, Path, optional): 缓存目录，用于保存模型
            local_dir (str, Path, optional): 本地存储路径，指定模型下载到的目录
            repo_type (str, optional): 仓库类型，可选 "model", "dataset", "space"
            allow_patterns (list[str] or str, optional): 允许下载的文件模式
                                       HuggingFace Hub 参数, ModelScope 为了兼容也支持
            ignore_patterns (list[str] or str, optional): 忽略下载的文件模式
                                        HuggingFace Hub 参数, ModelScope 为了兼容也支持
            headers (dict, optional): HTTP 请求头
            local_files_only (bool, optional): 是否仅使用本地文件
            force_download (bool, optional): 是否强制下载，即使本地缓存已存在
            token (str, bool, optional): 认证令牌
            library_name (str, optional): 库名称
            library_version (str, optional): 库版本
            user_agent (str, dict, optional): 用户代理信息
            max_workers (int, optional): 最大并发数，默认为 8
            cookies (CookieJar, optional): Cookie 信息 (ModelScope 特有)
            etag_timeout (float, optional): 获取 ETag 超时时间 (HuggingFace Hub 特有)
            endpoint (str, optional): HuggingFace Hub 端点
            dry_run (bool, optional): 是否进行预演，不实际下载文件 (HuggingFace Hub 特有)
        
        Returns:
            str or list of DryRunFileInfo: 下载文件的本地路径，或 DryRunFileInfo 对象列表（dry_run 模式）
        """
        pass