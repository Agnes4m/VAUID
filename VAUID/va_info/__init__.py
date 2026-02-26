from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .va_info import get_va_info_img, get_va_asset_img
from ..utils.error_reply import UID_HINT
from ..utils.database.models import ValBind

va_user_info = SV("VA 用户信息查询")


@va_user_info.on_command(("查询"), block=True)
async def send_va_info_msg(bot: Bot, ev: Event):
    tag = ev.text.strip()
    logger.info(f"[val]查询 VA 用户信息: {tag}")
    uid = tag if tag else await get_uid(ev)

    if not uid:
        return await bot.send(UID_HINT)

    img = await get_va_info_img(ev, uid)
    await bot.send(img)


@va_user_info.on_command(("资产"), block=True)
async def send_va_asset_msg(bot: Bot, ev: Event):
    tag = ev.text.strip()
    logger.info(f"[val]查询 VA 用户资产: {tag}")
    uid = tag if tag else await get_uid(ev)

    if not uid:
        return await bot.send(UID_HINT)

    img = await get_va_asset_img(ev, uid)
    await bot.send(img)


async def get_uid(ev: Event):
    """获取用户 ID，优先使用 @ 的 ID 或者用户 ID"""
    user_id = ev.at if ev.at else ev.user_id
    # 确保 bot_id 是字符串类型
    bot_id = ev.bot_id[0] if isinstance(ev.bot_id, list) else ev.bot_id
    return await ValBind.get_uid_by_game(user_id, bot_id)
