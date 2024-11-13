from gsuid_core.models import Event

from ..utils.database.models import VAUser


async def add_cookie(ev: Event, ck: str, uid: str):
    if VAUser.data_exists(ev.user_id, ev.bot_id):
        await VAUser.insert_data(ev.user_id, ev.bot_id, cookie=ck, uid=uid)
    else:
        await VAUser.update_data(ev.user_id, ev.bot_id, cookie=ck)
    return '[VA]添加ck成功！'
