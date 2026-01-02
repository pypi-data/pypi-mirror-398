from dataclasses import dataclass, field
import os
from typing import List
from .base import BaseConfig
from ncatbot.utils.logger import get_log

logger = get_log("Config")


@dataclass(frozen=False)
class PluginConfig(BaseConfig):
    """插件配置类。"""

    plugins_dir: str = "plugins"
    plugin_whitelist: List[str] = field(default_factory=list)
    plugin_blacklist: List[str] = field(default_factory=list)
    skip_plugin_load: bool = False

    def validate(self) -> None:
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"插件目录 {self.plugins_dir} 不存在，将自动创建")
            os.makedirs(self.plugins_dir)
