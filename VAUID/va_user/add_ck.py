from gsuid_core.models import Event

from ..utils.database.models import ValUser


async def add_cookie(ev: Event, uid: str, ck: str):
    if not await ValUser.data_exist(user_id=ev.user_id, bot_id=ev.bot_id):
        await ValUser.insert_data(ev.user_id, ev.bot_id, cookie=ck, uid=uid)
    else:
        await ValUser.update_data(ev.user_id, ev.bot_id, cookie=ck, uid=uid)
    return "[Val]添加ck成功！"
