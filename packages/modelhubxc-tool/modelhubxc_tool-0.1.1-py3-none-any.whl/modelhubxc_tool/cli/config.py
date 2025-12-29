from pathlib import Path
import yaml
from typing import Optional
from dataclasses import dataclass, fields


@dataclass
class Config:
    """
    配置类，用于管理应用配置
    """
    username: Optional[str] = None
    email: Optional[str] = None
    download_dir: Optional[str] = None
    cache_dir: Optional[str] = None
    max_workers: Optional[int] = None
    cookie_file: Optional[str] = None
    token: Optional[str] = None

    @classmethod
    def load(cls, config_path: Path) -> "Config":
        """
        从 YAML 文件加载配置
        - 文件中不存在的字段，自动设为 None
        """
        config_path = Path(config_path)

        if not config_path.exists():
            # 文件不存在，返回一个所有字段为 None 的实例
            return cls(**{f.name: None for f in fields(cls)})

        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # 只取 dataclass 中定义的字段
        values = {
            f.name: data.get(f.name, None)
            for f in fields(cls)
        }

        return cls(**values)

    def save(self, config_path: Path) -> None:
        """
        将配置保存为 YAML 文件
        - 字段值为 None 时不会报错
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            f.name: getattr(self, f.name)
            for f in fields(self)
        }

        with config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False
            )
