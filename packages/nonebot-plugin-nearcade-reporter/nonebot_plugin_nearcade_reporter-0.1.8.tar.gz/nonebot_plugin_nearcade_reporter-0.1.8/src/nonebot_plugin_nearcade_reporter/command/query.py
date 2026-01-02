from nonebot import get_plugin_config, on_regex
from nonebot.params import RegexDict

from nonebot_plugin_nearcade_reporter.config import Config
from nonebot_plugin_nearcade_reporter.network import NearcadeHttp
from nonebot_plugin_nearcade_reporter.safe_dict import SafeDict

config = get_plugin_config(Config)
nearcade = NearcadeHttp(config.api_token)

arcade_attendance = on_regex(config.query_attendance_match.pattern)


@arcade_attendance.handle()
async def _(args: dict[str, str] = RegexDict()):
    arcade_name = args.get("arcade")
    if not arcade_name:
        ...  # Should not happen due to regex
    arcades = config.find_arcade_by_alias(arcade_name)
    if not arcades:
        await arcade_attendance.finish(f"未找到机厅：{arcade_name}")
    if len(arcades) > 1:
        names = [arcade.name for arcade in arcades.values()]
        await arcade_attendance.finish(
            f"找到多个同名机厅：{', '.join(names)}，请使用更具体的名称或别名"
        )
    arcade_id, arcade = next(iter(arcades.items()))
    success, message, data = await nearcade.get_attendance(
        arcade_id=arcade_id,
        source=arcade.arcade_source,
    )
    if not success or not data:
        await arcade_attendance.finish(f"查询失败：{message or '未知错误'}")
    game_count = None
    for game in data.get("games", []):
        if game.get("gameId") == arcade.default_game_id:
            game_count = game.get("total")
            break
    if game_count is None:
        await arcade_attendance.finish(f"获取 {arcade.name} 人数失败!")
    reply_msg = config.query_attendance_match.reply_message.format(
        SafeDict(
            arcade=arcade.name,
            count=game_count,
            arcade_id=arcade_id,
            source=arcade.arcade_source,
        )
    )
    await arcade_attendance.finish(reply_msg)
