import asyncio
from email import message
from typing import List, Union, Optional, cast

from PIL import Image, ImageDraw

from gsuid_core.logger import logger

from .utils import time_delta

# from gsuid_core.logger import logger
# from gsuid_core.utils.image.convert import convert_img
# from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring
from ..utils.va_api import va_api
from ..utils.api.models import (
    Shop,
    ShopDay,
    SummonerInfo,
)
from ..utils.error_reply import get_error


async def get_va_shop_img(uid: str) -> Union[str, bytes]:
    # 基础信息
    detail = await va_api.get_player_info(uid)

    if isinstance(detail, (int, str)):
        return get_error(detail) if isinstance(detail, int) else detail

    # sence = detail["gameInfoList"][0]["scene"]

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card["role_info"]["friend_scene"]
    shop_list = await va_api.get_shop(uid, scene)
    if isinstance(shop_list, int):
        return get_error(shop_list)
    if isinstance(shop_list, str):
        return shop_list

    if len(detail) == 0:
        return "报错了，检查控制台"

    return await draw_va_shop_img(detail, shop_list)


async def draw_va_shop_img(
    detail: SummonerInfo,
    shop_list: List[Shop],
):
    msg: str = "--今日商店--"
    day_list = next((i for i in shop_list if i["key"] == "dailystore"), None)
    king_list = next((i for i in shop_list if i["key"] == "kingdomstore"), None)
    if day_list is not None:
        day_time = await time_delta(day_list["time"])
        msg += f"""[每日商店] {day_time}分
        1、{day_list[0]["goods_name"]} {day_list[0]["rmb_price"]}r
        2、{day_list[1]["goods_name"]} {day_list[1]["rmb_price"]}r
        3、{day_list[2]["goods_name"]} {day_list[2]["rmb_price"]}r
        4、{day_list[3]["goods_name"]} {day_list[3]["rmb_price"]}r
        """
    if king_list is not None:
        msg += f"""[王国商店]
        1、{king_list[0]["goods_name"]} {king_list[0]["rmb_price"]}b
        2、{king_list[1]["goods_name"]} {king_list[1]["rmb_price"]}b
        3、{king_list[2]["goods_name"]} {king_list[2]["rmb_price"]}b
        4、{king_list[3]["goods_name"]} {king_list[3]["rmb_price"]}b
        """
    return msg
