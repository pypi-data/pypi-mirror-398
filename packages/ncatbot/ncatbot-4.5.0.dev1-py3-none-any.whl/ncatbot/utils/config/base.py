import copy
import os
import yaml
from dataclasses import fields
from typing import Any, Dict, TextIO, TypeVar

from ncatbot.utils.logger import get_log

logger = get_log("Config")

T = TypeVar("T", bound="BaseConfig")


class BaseConfig:
    """基础配置类，提供通用功能。"""

    @classmethod
    def from_dict(cls, data: Dict[str, Any], /, **kwargs: Any) -> T:
        """从字典创建新实例。"""
        # 延迟导入以避免循环依赖
        from .config import ATTRIBUTE_RECURSIVE, ATTRIBUTE_IGNORE

        data, kwargs = {**data, **kwargs}, {}
        for f in fields(cls):
            if f.name in data and f.init:
                if f.name in ATTRIBUTE_RECURSIVE:
                    if isinstance(data[f.name], list):
                        kwargs[f.name] = [
                            ATTRIBUTE_RECURSIVE[f.name].from_dict(d)
                            for d in data.pop(f.name)
                        ]
                    else:
                        kwargs[f.name] = ATTRIBUTE_RECURSIVE[f.name].from_dict(
                            data.pop(f.name)
                        )
                else:
                    kwargs[f.name] = data.pop(f.name)

        self = cls(**kwargs)
        sentinel = object()
        for key, value in data.items():
            if key in ATTRIBUTE_IGNORE:
                continue
            self_value = getattr(self, key, sentinel)
            if self_value is sentinel:
                # 使用 logger 而不是 warnings，集中输出
                logger.warning(f"Unexpected key: {key!r}")
                setattr(self, key, value)
            elif self_value != value:
                raise ValueError(
                    f"Conflicting values for key: {key!r}, got {value!r} and already had {self_value!r}."
                )

        return self

    def asdict(self) -> Dict[str, Any]:
        """将实例转换为字典。"""
        from .config import ATTRIBUTE_IGNORE

        data = {
            k: v
            for k, v in self.__dict__.items()
            if isinstance(v, (str, int, bool, type(None), tuple, list))
            and not k.startswith("_")
            and k not in ATTRIBUTE_IGNORE
        }
        return data

    def save(self, redact_secrets: bool = True) -> None:
        """保存当前配置到默认路径（原子写入并设置权限）。"""
        from .constants import CONFIG_PATH
        from .utils import redact_sensitive

        data = self.asdict()
        data_to_write = (
            redact_sensitive(copy.deepcopy(data)) if redact_secrets else data
        )

        tmp_path = f"{CONFIG_PATH}.tmp"
        cfg_dir = os.path.dirname(CONFIG_PATH) or "."
        try:
            os.makedirs(cfg_dir, exist_ok=True)
        except Exception:
            pass

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                yaml.dump(data_to_write, f, allow_unicode=True, sort_keys=False)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            os.replace(tmp_path, CONFIG_PATH)
            try:
                os.chmod(CONFIG_PATH, 0o600)
            except Exception as e:
                logger.warning(f"无法设置配置文件权限: {e}")
            logger.info(f"配置已保存到 {CONFIG_PATH}")
        except Exception as e:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            logger.error(f"保存配置失败: {e}")
            raise ValueError(f"保存配置失败: {e}") from e

    def __replace__(self, **kwargs: Any) -> T:
        """替换属性值并返回副本。"""
        replaced = copy.copy(self)
        for key, value in kwargs.items():
            setattr(replaced, key, value)
        return replaced

    def pprint(self, file: TextIO = None) -> None:
        """美化打印实例。"""
        import rich

        rich.print(self, file=file)

    def update_value(self, key, value) -> None:
        """更新配置属性，支持递归子属性更新。"""
        from .config import ATTRIBUTE_RECURSIVE

        if hasattr(self, key):
            setattr(self, key, value)
            return True
        else:
            for attr in ATTRIBUTE_RECURSIVE:
                if hasattr(getattr(self, attr), key):
                    setattr(getattr(self, attr), key, value)
                    return True
        return False
