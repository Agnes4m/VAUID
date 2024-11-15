from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .va_info import get_va_info_img
from ..utils.error_reply import UID_HINT
from ..utils.database.models import VABind

va_user_info = SV('VA用户信息查询')


@va_user_info.on_command(('查询'), block=True)
async def send_va_info_msg(bot: Bot, ev: Event):
    tag = ev.text.strip()
    uid = tag if tag else await get_uid(ev)

    if uid is None:
        return await bot.send(UID_HINT)

    await bot.send(await get_va_info_img(uid))


async def get_uid(ev: Event):
    """获取用户 ID，优先使用 @ 的 ID 或者用户 ID"""
    if ev.at is not None:
        user_id = ev.at
    else:
        user_id = ev.user_id
    return await VABind.get_uid_by_game(user_id, ev.bot_id)
