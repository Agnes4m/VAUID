from gsuid_core.models import Event

from ..utils.database.models import VAUser


async def add_cookie(ev: Event, uid: str, ck: str):
    if VAUser.data_exist(user_id=ev.user_id, bot_id=ev.bot_id):
        await VAUser.insert_data(ev.user_id, ev.bot_id, cookie=ck, uid=uid)
    else:
        await VAUser.update_data(ev.user_id, ev.bot_id, cookie=ck)
    return '[VA]添加ck成功！'
