from nonebot import get_plugin_config, on_regex
from nonebot.params import RegexDict

from nonebot_plugin_nearcade_reporter.config import Config
from nonebot_plugin_nearcade_reporter.network import NearcadeHttp

config = get_plugin_config(Config)
nearcade = NearcadeHttp(config.api_token)

arcade_attendance = on_regex(config.update_attendance_match.pattern)


@arcade_attendance.handle()
async def _(args: dict[str, str] = RegexDict()):
    arcade_name = args.get("arcade")
    if not arcade_name:
        ...  # Should not happen due to regex
    count = args.get("count")
    if not count:
        ...  # Should not happen due to regex
    if not count.isdigit():
        await arcade_attendance.finish("人数必须是数字!")
    if not (0 <= int(count) <= 100):
        await arcade_attendance.finish("人数必须在0到100之间!")
    arcades = config.find_arcade_by_alias(arcade_name)
    if not arcades:
        await arcade_attendance.finish(f"未找到机厅：{arcade_name}")
    if len(arcades) > 1:
        names = [arcade.name for arcade in arcades.values()]
        await arcade_attendance.finish(
            f"找到多个同名机厅：{', '.join(names)}，请使用更具体的名称或别名"
        )
    arcade_id, arcade = next(iter(arcades.items()))
    success, message = await nearcade.update_attendance(
        arcade_id=arcade_id,
        game_id=config.arcades[arcade_id].default_game_id,
        count=int(count),
        source=config.arcades[arcade_id].arcade_source,
        comment="Update from Nearcade Reporter Bot",
    )
    if not success:
        await arcade_attendance.finish(f"更新失败：{message or '未知错误'}")
    reply_msg = config.update_attendance_match.reply_message.format(
        arcade=arcade.name,
        count=count,
    )
    if config.update_attendance_match.enable_reply:
        await arcade_attendance.finish(f"{reply_msg}")
