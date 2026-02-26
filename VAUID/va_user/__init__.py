import re
import sys
import asyncio
import urllib.parse
from typing import cast

if sys.version_info >= (3, 11):
    from asyncio import timeout
else:
    from async_timeout import timeout
# 导入 Playwright
from playwright.async_api import async_playwright

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

# 导入 gsuid_core 组件
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.message import send_diff_msg
from gsuid_core.message_models import Button
from gsuid_core.utils.image.convert import convert_img

from .login import exchange_val_token
from .add_ck import add_cookie
from .search_player import search_player_with_name
from ..utils.api.models import LoginData
from ..utils.error_reply import get_error
from ..utils.database.models import ValBind, ValUser

va_user_bind = SV("VA用户绑定")
va_add_ck = SV("VA添加CK", area="DIRECT")
va_add_uids = SV("VA添加UID", area="DIRECT")
va_add_sk = SV("VA添加UID", area="DIRECT")


@va_add_ck.on_prefix(("添加CK", "添加ck"))
async def send_va_add_ck_msg(bot: Bot, ev: Event):
    ck = ev.text.strip()
    uid = ev.text.strip().split("userId=")[-1].strip().split(";")[0].strip()
    if not uid.startswith("JA-"):
        await bot.send("uid格式错误")
    if not ("tid" in ck or "access_token" in ck or "openid" in ck):
        return await bot.send("ck格式错误")
    await bot.send(await add_cookie(ev, uid, ck))


@va_user_bind.on_command(("扫码登录"))
async def on_valo_login(bot: Bot, ev: Event):
    await bot.send("正在获取登录二维码，请稍候...")
    LOGIN_URL = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin?pt_enable_pwd=1&appid=716027609&pt_3rd_aid=102061775&daid=381&pt_skey_valid=0&style=35&force_qr=1&autorefresh=1&s_url=http%3A%2F%2Fconnect.qq.com&refer_cgi=m_authorize&ucheck=1&fall_to_wv=1&status_os=12&redirect_uri=auth%3A%2F%2Ftauth.qq.com%2F&client_id=102061775&pf=openmobile_android&response_type=token&scope=all&sdkp=a&sdkv=3.5.17.lite&sign=a6479455d3e49b597350f13f776a6288&status_machine=MjMxMTdSSzY2Qw%3D%3D&switch=1&time=1763280194&show_download_ui=true&h5sig=trobryxo8IPM0GaSQH12mowKG-CY65brFzkK7_-9EW4&loginty=6"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
                "Mobile/15E148 Safari/604.1 MVAL/2.4.0"
            )
        )
        page = await context.new_page()

        login_temp_data = {}
        login_success_event = asyncio.Event()

        async def handle_response(response):
            if "ptqrlogin" in response.url:
                res_text = await response.text()
                if "登录成功" in res_text:
                    url_match = re.search(r"ptuiCB\('0','0','([^']+)'", res_text)
                    if url_match:
                        callback_url = url_match.group(1)

                        fragment = callback_url.split("#")[-1]
                        params = cast(LoginData, urllib.parse.parse_qs(fragment))
                        logger.info(params)

                        openid = params.get("openid", [""])[0]
                        access_token = params.get("access_token", [""])[0]
                        appid = params.get("appid", [""])[0]

                        if openid and access_token:
                            login_temp_data["openid"] = openid
                            login_temp_data["access_token"] = access_token
                            login_temp_data["appid"] = appid
                            logger.info(f"[Val] 成功解析凭证: OpenID={openid[:5]}..., Token={access_token[:5]}...")
                            login_success_event.set()
                        else:
                            logger.error(f"[Val] 解析失败，URL内容: {fragment}")

        page.on("response", handle_response)

        # 截图
        await page.goto(LOGIN_URL)
        qr_element = await page.wait_for_selector("#qrimg")
        if qr_element is None:
            await bot.send("未能获取到二维码，请稍后重试。")
            await browser.close()
            return
        qr_bytes = await qr_element.screenshot()

        await bot.send(
            [
                MessageSegment.at(ev.user_id),
                MessageSegment.text("\n请使用手机QQ扫描二维码登录："),
                MessageSegment.image(await convert_img(qr_bytes)),
                MessageSegment.text("\n有效期为30秒，扫码成功后请稍等..."),
            ]
        )

        try:
            async with timeout(30):
                await login_success_event.wait()
        except asyncio.TimeoutError:
            await browser.close()
            return await bot.send("登录超时，二维码已过期。")

        await browser.close()

        # 获取信息
        final_info = await exchange_val_token(login_temp_data["openid"], login_temp_data["access_token"])
        if not final_info:
            return await bot.send("获取游戏凭证失败，请重试。")
        uid = final_info["userId"]
        # await ValBind.insert_uid(
        #     bot_id=bot.bot_id,
        #     user_id=ev.user_id,
        #     uid=uid,
        # )

        cookie_str = (
            f"clientType=9; uin=o1123159457; appid={login_temp_data['appid']}; acctype=qc; "
            f"openid={login_temp_data['openid']}; "
            f"access_token={login_temp_data['access_token']}; "
            f"userId={uid}; "
            f"accountType=5; "
            f"tid={final_info['tid']}"
        )
        await ValUser.insert_or_update_user(
            bot_id=bot.bot_id,
            user_id=ev.user_id,
            cookie=cookie_str,
            uid=uid,
        )
        data = await ValBind.insert_uid(ev.user_id, ev.bot_id, uid, ev.group_id, is_digit=False)
        return await send_diff_msg(
            bot,
            data,
            {
                0: "[Val] 绑定成功,请输入[va查询]查看信息",
                -1: f"[Val] UID{uid}的位数不正确！",
                -2: "[Val] 已更新登录信息",
                -3: "[Val] 你输入了错误的格式!",
            },
        )


@va_user_bind.on_command(
    (
        "绑定uid",
        "绑定UID",
        "绑定",
        "切换uid",
        "切换UID",
        "切换",
        "删除uid",
        "删除UID",
    ),
    block=True,
)
async def send_va_bind_uid_msg(bot: Bot, ev: Event):
    uid = ev.text.strip()

    await bot.logger.info("[Val] 开始执行[绑定/解绑用户信息]")
    qid = ev.user_id
    await bot.logger.info("[Val] [绑定/解绑]UserID: {}".format(qid))

    if uid and len(uid.split("-")) != 3:
        return await bot.send("你输入了错误的格式!\n请使用va搜索命令获取正确的UID")

    if "绑定" in ev.command:
        if not uid:
            return await bot.send("该命令需要带上正确的uid!\n如果不知道, 可以使用va搜索命令查询\n如 va搜索爱丽数码")
        data = await ValBind.insert_uid(qid, ev.bot_id, uid, ev.group_id, is_digit=False)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f"[Val] 绑定UID{uid}成功！",
                -1: f"[Val] UID{uid}的位数不正确！",
                -2: f"[Val] UID{uid}已经绑定过了！",
                -3: "[Val] 你输入了错误的格式!",
            },
        )
    elif "切换" in ev.command:
        retcode = await ValBind.switch_uid_by_game(qid, ev.bot_id, uid)
        if retcode == 0:
            return await bot.send(f"[Val] 切换UID{uid}成功！")
        else:
            return await bot.send(f"[Val] 尚未绑定该UID{uid}")
    else:
        data = await ValBind.delete_uid(qid, ev.bot_id, uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f"[Val] 删除UID{uid}成功！",
                -1: f"[Val] 该UID{uid}不在已绑定列表中！",
            },
        )


@va_user_bind.on_command(("搜索"), block=True)
async def send_va_search_msg(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send("必须输入完整的名称噢！\n例如：va搜索恶意引航者")

    players = await search_player_with_name(name)
    print(players)
    if not players or players == 8000004:
        return await bot.send("未找到用户！\n请确认名称是否完整, 以及无畏契约设置是否允许他人搜索！")
    if isinstance(players, int):
        buttons = None
        im = get_error(players)
        await bot.send_option(im, buttons)
    else:
        buttons = [Button(f"✏️绑定{one_player['userId']}", f"va绑定{one_player['userId']}") for one_player in players]
        out_msg = []
        for one_player in players:
            out_msg.append(
                f"""昵称: {one_player["userName"]} | {one_player["userAppNum"]})
uid: {one_player["userId"]}"""
            )
        print(out_msg)
        im = "\n".join(out_msg)
        print(im)
    await bot.send_option(im, buttons)
