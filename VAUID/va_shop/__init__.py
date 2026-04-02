from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .shop_info import get_va_shop_img
from ..utils.helper import get_bind_uid
from ..utils.error_reply import UID_HINT

va_shop_query = SV("VA 商店查询")


@va_shop_query.on_command(("商店"), block=True)
async def send_va_shop_msg(bot: Bot, ev: Event):
    tag = ev.text.strip()
    logger.info(f"[val] 查询 VA 商店信息：{tag}")
    uid = tag if tag else await get_bind_uid(ev)

    if not uid:
        return await bot.send(UID_HINT)

    img = await get_va_shop_img(ev, uid)
    await bot.send(img)
