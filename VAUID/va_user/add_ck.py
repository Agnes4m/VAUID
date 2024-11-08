from gsuid_core.models import Event

from ..utils.database.models import VAUser


async def add_cookie(ev: Event, ck: str):
    await VAUser.insert_data(ev.user_id, ev.bot_id, cookie=ck)
    return '添加成功！'


async def add_uid(ev: Event, uid: str):
    await VAUser.insert_data(ev.user_id, ev.bot_id, uid=uid)
    return '添加成功！'


# async def add_scene(ev: Event, stoken: str):
#     await VAUser.insert_data(ev.user_id, ev.bot_id, stoken=stoken)
#     return '添加成功！'
