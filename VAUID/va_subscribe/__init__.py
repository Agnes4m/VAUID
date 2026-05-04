"""VA 战绩订阅模块"""

from typing import Any, Dict, Optional

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import gs_subscribe

from ..utils.va_api import va_api
from ..utils.database.models import ValBind, ValUser

va_watch_record = SV("VA战绩订阅")


def _parse_detail(detail: Any) -> Optional[Dict[str, Any]]:
    """安全解析detail响应"""
    if isinstance(detail, dict) and "gameInfoList" in detail:
        return detail
    return None


def _parse_card(card: Any) -> Optional[Dict[str, Any]]:
    """安全解析card响应"""
    if isinstance(card, dict) and "role_info" in card:
        return card
    return None


async def get_user_battle_id(uid: str, scene: str, cookie: str) -> str:
    """获取用户最新的battle_id"""
    try:
        battle_data = await va_api.get_detail_card(scene, cookie)
        if isinstance(battle_data, list) and len(battle_data) > 0:
            return battle_data[0].get("battle_id", "") or ""
    except Exception as e:
        logger.error(f"[VA] 获取battle_id失败: {e}")
    return ""


@va_watch_record.on_command(("订阅"), block=True)
async def subscribe_va_record(bot: Bot, ev: Event):
    """处理战绩订阅命令"""
    logger.info("[VA] 正在执行VA战绩订阅功能")

    raw_text = ev.text.strip() if ev.text else ""

    # 获取用户绑定的UID
    user_id = ev.at if ev.at else ev.user_id
    bot_id = ev.bot_id[0] if isinstance(ev.bot_id, list) else ev.bot_id
    uid = await ValBind.get_uid_by_game(user_id, bot_id)

    if not uid:
        await bot.send("[VA] 请先绑定UID再使用订阅功能！")
        return

    if raw_text == "开启" or raw_text == "":
        # 添加订阅
        await gs_subscribe.add_subscribe(
            "single",
            "va战绩订阅",
            ev,
            extra_message=uid,
        )

        # 获取当前最新战绩作为基准，避免误推历史战绩
        try:
            user_data = await ValUser.select_data(user_id, bot_id)
            if user_data and user_data.cookie:
                ctx = await va_api.create_context(ev)
                detail = await va_api.get_player_info(ctx, [uid])
                parsed_detail = _parse_detail(detail)
                if parsed_detail:
                    scene = parsed_detail["gameInfoList"][0]["scene"]
                    card = await va_api.get_player_card(uid)
                    parsed_card = _parse_card(card)
                    if parsed_card:
                        scene = parsed_card["role_info"]["friend_scene"]
                        latest_battle_id = await get_user_battle_id(
                            uid, scene, user_data.cookie
                        )
                        if latest_battle_id:
                            await ValUser.update_latest_battle(
                                user_id, bot_id, latest_battle_id, 0
                            )
                            logger.info(f"[VA] 已设置基准battle_id: {latest_battle_id}")
        except Exception as e:
            logger.error(f"[VA] 设置基准battle_id失败: {e}")

        await bot.send("[VA] VA战绩订阅成功！将每5分钟检查一次新战绩。")

    elif raw_text == "关闭":
        # 取消订阅
        await gs_subscribe.delete_subscribe(
            "single",
            "va战绩订阅",
            ev,
        )
        await bot.send("[VA] VA战绩订阅已关闭！")


@va_watch_record.on_command(("取消订阅"), block=True)
async def cancel_subscribe_va_record(bot: Bot, ev: Event):
    """处理取消战绩订阅命令"""
    logger.info("[VA] 正在执行取消VA战绩订阅功能")
    await gs_subscribe.delete_subscribe(
        "single",
        "va战绩订阅",
        ev,
    )
    await bot.send("[VA] VA战绩订阅已取消！")


async def check_new_battle(
    uid: str, user_id: str, bot_id: str
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    检查用户是否有新战绩

    Returns:
        tuple: (是否有新战绩, 最新战绩对象)
    """
    try:
        # 获取用户数据
        user_data = await ValUser.select_data(user_id, bot_id)
        if not user_data or not user_data.cookie:
            return False, None

        # 获取cookie
        cookie_uid, ck = await va_api._get_cookie_by_id(user_id, bot_id)
        if not ck:
            return False, None

        # 获取scene - 通过_get_cookie获取uid对应的信息
        cookie_uid, _ = await va_api._get_cookie(uid)
        if not cookie_uid:
            return False, None

        # 获取player_info
        detail = await va_api.get_player_info(
            type(
                "Ctx",
                (),
                {
                    "user_id": user_id,
                    "bot_id": bot_id,
                    "cookie": ck,
                    "opuid": cookie_uid,
                    "_random_cookie": None,
                },
            )(),
            [uid],
        )
        parsed_detail = _parse_detail(detail)
        if not parsed_detail:
            return False, None

        scene = parsed_detail["gameInfoList"][0]["scene"]

        # 获取card
        card = await va_api.get_player_card(uid)
        parsed_card = _parse_card(card)
        if not parsed_card:
            return False, None

        scene = parsed_card["role_info"]["friend_scene"]
        random_cookie = await va_api.get_sence()[1] if not user_data.cookie else None

        # 获取最新战绩
        battle_data = await va_api.get_detail_card(
            scene, user_data.cookie, random_cookie
        )
        if not isinstance(battle_data, list) or len(battle_data) == 0:
            return False, None

        latest_battle = battle_data[0]
        latest_battle_id = latest_battle.get("battle_id", "")

        if not latest_battle_id:
            return False, None

        # 比较battle_id
        if (
            user_data.latest_battle_id
            and user_data.latest_battle_id == latest_battle_id
        ):
            return False, None

        # 更新缓存
        await ValUser.update_latest_battle(
            user_id, bot_id, latest_battle_id, latest_battle.get("ts", 0)
        )

        return True, latest_battle

    except Exception as e:
        logger.error(f"[VA] 检查新战绩失败: {e}")
        return False, None
