from nonebot import get_plugin_config, on_command, permission

from nonebot.params import CommandArg
from nonebot.adapters import Message
from nonebot_plugin_nearcade_reporter.config import Config
from nonebot_plugin_nearcade_reporter.network import NearcadeHttp

config = get_plugin_config(Config)
nearcade = NearcadeHttp(config.api_token)

search_arcade = on_command(
    "arcade_search", aliases={"查找机厅"}, permission=permission.SUPERUSER
)


@search_arcade.handle()
async def _(arg: Message = CommandArg()):
    keyword = arg.extract_plain_text().strip()
    await search_arcade.send("正在搜索机厅，请稍候...")
    if not keyword:
        await search_arcade.finish("请提供搜索关键词，例如：查找机厅 秋叶原")

    result = await nearcade.list_shops(keyword=keyword, page=1, limit=5)
    shops = result.get("shops", [])
    print(shops)
    if not shops:
        await search_arcade.finish(
            f"未找到包含关键词 '{keyword}' 的机厅，请尝试其他关键词"
        )

    reply_lines = [f"找到以下机厅包含关键词 '{keyword}':"]
    for shop in shops:
        reply_lines.append(f"- {shop.get('name')}")
        reply_lines.append(f"  source: {shop.get('source')} ID: {shop.get('id')}")
        for game in shop.get("games", []):
            reply_lines.append(
                f"       - {game.get('name')} (ID: {game.get('gameId')})"
            )

    await search_arcade.finish("\n".join(reply_lines))
