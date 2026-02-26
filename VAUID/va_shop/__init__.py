from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .shop_info import get_va_shop_img
from ..utils.error_reply import UID_HINT
from ..utils.database.models import ValBind

va_user_info = SV("VA商店查询")


@va_user_info.on_command(("商店"), block=True)
async def send_va_info_msg(bot: Bot, ev: Event):
    tag = ev.text.strip()

    uid = tag if tag else await get_uid(ev)

    if not uid:
        return await bot.send(UID_HINT)

    img = await get_va_shop_img(ev, uid)
    await bot.send(img)


async def get_uid(ev: Event):
    """获取用户 ID，优先使用 @ 的 ID 或者用户 ID"""
    user_id = ev.at if ev.at else ev.user_id
    return await ValBind.get_uid_by_game(user_id, ev.bot_id)
