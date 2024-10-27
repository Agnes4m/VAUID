from typing import Optional

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.database.api import get_uid

from .va_info import get_va_info_img
from ..utils.database.models import VABind
from .va_search import draw_va_battle_list_img
from ..utils.error_reply import UID_HINT, TEXT_HINT

va_user_info = SV('VA用户信息查询')


# @va_user_info.on_command(('搜索'), block=True)
# async def va_search_info(bot: Bot, ev: Event):
#     tag = ev.text.strip()
#     if not tag :
#         return await bot.send(TEXT_HINT)
#     await bot.send(await draw_va_battle_list_img(tag))


@va_user_info.on_command(('查询'), block=True)
async def send_va_info_msg(bot: Bot, ev: Event):
    if ev.text.strip():
        uid = ev.text.strip()
    else:
        uid = await VABind.get_uid_by_game(
            ev.user_id,
            ev.bot_id,
        )
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.send(await get_va_info_img(uid))
