from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button
from gsuid_core.utils.message import send_diff_msg

from .add_ck import add_cookie
from ..utils.error_reply import get_error
from ..utils.database.models import VABind
from .search_player import search_player_with_name

va_user_bind = SV('VA用户绑定')
va_add_ck = SV('VA添加CK', area='DIRECT')
va_add_uids = SV('VA添加UID', area='DIRECT')
va_add_sk = SV('VA添加UID', area='DIRECT')


@va_add_ck.on_prefix(('添加CK', '添加ck'))
async def send_va_add_ck_msg(bot: Bot, ev: Event):
    ck = ev.text.strip()
    uid = ev.text.strip().split("userId=")[-1].strip().split(";")[0].strip()
    if not uid.startswith('JA-'):
        await bot.send('uid格式错误')
    if not ("tid" in ck or "access_token" in ck or "openid" in ck):
        return await bot.send('ck格式错误')
    await bot.send(await add_cookie(ev, uid, ck))


# @va_add_sk.on_prefix(('添加scene', '添加SCENE'))
# async def send_va_add_sk_msg(bot: Bot, ev: Event):
#     sk = ev.text.strip()
#     await bot.send(await add_scene(ev, sk))


@va_user_bind.on_command(
    (
        '绑定uid',
        '绑定UID',
        '绑定',
        '切换uid',
        '切换UID',
        '切换',
        '删除uid',
        '删除UID',
    ),
    block=True,
)
async def send_va_bind_uid_msg(bot: Bot, ev: Event):
    uid = ev.text.strip()

    await bot.logger.info('[VA] 开始执行[绑定/解绑用户信息]')
    qid = ev.user_id
    await bot.logger.info('[VA] [绑定/解绑]UserID: {}'.format(qid))

    if uid and len(uid.split('-')) != 3:
        return await bot.send(
            '你输入了错误的格式!\n请使用va搜索命令获取正确的UID'
        )

    if '绑定' in ev.command:
        if not uid:
            return await bot.send(
                '该命令需要带上正确的uid!\n如果不知道, 可以使用va搜索命令查询\n如 va搜索爱丽数码'
            )
        data = await VABind.insert_uid(
            qid, ev.bot_id, uid, ev.group_id, is_digit=False
        )
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'[VA] 绑定UID{uid}成功！',
                -1: f'[VA] UID{uid}的位数不正确！',
                -2: f'[VA] UID{uid}已经绑定过了！',
                -3: '[VA] 你输入了错误的格式!',
            },
        )
    elif '切换' in ev.command:
        retcode = await VABind.switch_uid_by_game(qid, ev.bot_id, uid)
        if retcode == 0:
            return await bot.send(f'[VA] 切换UID{uid}成功！')
        else:
            return await bot.send(f'[VA] 尚未绑定该UID{uid}')
    else:
        data = await VABind.delete_uid(qid, ev.bot_id, uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'[VA] 删除UID{uid}成功！',
                -1: f'[VA] 该UID{uid}不在已绑定列表中！',
            },
        )


@va_user_bind.on_command(('搜索'), block=True)
async def send_va_search_msg(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send('必须输入完整的名称噢！\n例如：va搜索恶意引航者')

    players = await search_player_with_name(name)
    print(players)
    if not players or players == 8000004:
        return await bot.send(
            '未找到用户！\n请确认名称是否完整, 以及无畏契约设置是否允许他人搜索！'
        )
    if isinstance(players, int):
        buttons = None
        im = get_error(players)
        await bot.send_option(im, buttons)
    else:

        buttons = [
            Button(
                f"✏️绑定{one_player['userId']}", f"va绑定{one_player['userId']}"
            )
            for one_player in players
        ]
        out_msg = []
        for one_player in players:
            out_msg.append(
                f"""昵称: {one_player['userName']} | {one_player['userAppNum']})
uid: {one_player['userId']}"""
            )
        print(out_msg)
        im = '\n'.join(out_msg)
        print(im)
    await bot.send_option(im, buttons)
