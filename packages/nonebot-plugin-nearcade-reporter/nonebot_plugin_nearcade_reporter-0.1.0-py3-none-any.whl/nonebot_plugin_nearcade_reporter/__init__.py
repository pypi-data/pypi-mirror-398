from pathlib import Path

import nonebot
from nonebot import get_plugin_config, logger
from nonebot.plugin import PluginMetadata

from . import command  # noqa: F401
from nonebot_plugin_nearcade_reporter.config import Config

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-nearcade-reporter",
    description="用于管理和查询机厅人数，接入 Nearcade API",
    usage="使用help nearcade查看帮助",
    type="application",
    homepage="https://github.com/jiyun233/nonebot-plugin-nearcade-reporter",
    supported_adapters={"~onebot.v11"},
    config=Config,
)

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)

config = get_plugin_config(Config)
logger.info(f"Loaded Nearcade config: {config.model_dump()}")
