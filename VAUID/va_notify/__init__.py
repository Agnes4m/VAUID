"""VA 战绩定时推送模块"""

import random
import asyncio

from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.subscribe import gs_subscribe

from ..va_subscribe import check_new_battle


def format_battle_message(battle: dict) -> str:
    """格式化战绩消息"""
    hero_name = battle.get("hero_name", "未知")
    result = battle.get("result_title", "")
    kda = battle.get("kda", "")
    map_name = (
        battle.get("used_map", {}).get("name", "未知地图") if isinstance(battle.get("used_map"), dict) else "未知地图"
    )
    time_str = battle.get("time", "")

    return f"[VA战绩推送]\n英雄: {hero_name}\n结果: {result}\nKDA: {kda}\n地图: {map_name}\n时间: {time_str}"


@scheduler.scheduled_job("cron", minute="*/5")
async def va_notify_match():
    """定时检查并推送新战绩"""
    times = 0
    logger.info("[VA] 正在执行战绩推送功能")
    await asyncio.sleep(random.randint(0, 3))  # 随机延迟避免同时请求

    try:
        datas = await gs_subscribe.get_subscribe("va战绩订阅")
        if not datas:
            return

        for subscribe in datas:
            try:
                uid = subscribe.extra_message
                if not uid:
                    logger.debug(f"[VA] 用户 {subscribe.user_id} 未绑定UID，跳过")
                    continue

                has_new, battle = await check_new_battle(uid, subscribe.user_id, subscribe.bot_id)
                if has_new and battle:
                    msg = format_battle_message(battle)
                    await subscribe.send(msg)
                    times += 1
                    logger.info(f"[VA] 为用户 {subscribe.user_id} 推送了新战绩")
                else:
                    logger.debug(f"[VA] 用户 {subscribe.user_id} 没有新战绩")

            except Exception as e:
                logger.error(f"[VA] 处理订阅用户 {subscribe.user_id} 时出错: {e}")
                continue

        if times > 0:
            logger.info(f"[VA] 共为 {times} 个用户推送了新战绩")

    except Exception as e:
        logger.error(f"[VA] 战绩推送任务出错: {e}")
