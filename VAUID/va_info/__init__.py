from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.database.api import get_uid
from typing import Optional
from ..utils.error_reply import TEXT_HINT, UID_HINT
from ..utils.database.models import VALBind
from .va_search import draw_va_battle_list_img

va_user_info = SV('VA用户信息查询')


@va_user_info.on_command(('搜索'), block=True)
async def va_search_info(bot: Bot, ev: Event):
    tag = ev.text.strip()
    if not tag :
        return await bot.send(TEXT_HINT)
    await bot.send(await draw_va_battle_list_img(tag))

@va_user_info.on_command(('查询'), block=True)
async def send_va_info_msg(bot: Bot, ev: Event):
    uid: Optional[str] = await get_uid(bot, ev, VALBind)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.send(await draw_va_battle_list_img(uid))
