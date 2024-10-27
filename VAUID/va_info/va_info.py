# from pathlib import Path
from typing import Union

from loguru import logger

from ..utils.va_api import va_api
from ..utils.error_reply import get_error
from ..utils.api.models import CardInfo, SummonerInfo

# from PIL import Image, ImageDraw
# from gsuid_core.logger import logger
# from gsuid_core.utils.image.convert import convert_img
# from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring

# from ..utils.va_font import va_font_20, va_font_30, va_font_42


async def get_va_info_img(uid: str) -> Union[str, bytes]:
    detail = await va_api.get_player_info(uid)

    # logger.info(detail)
    if isinstance(detail, int):
        return get_error(detail)
    if isinstance(detail, str):
        return detail

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    if len(detail) == 0:
        return "报错了，检查控制台"
    return await draw_va_info_img(detail, card)


async def draw_va_info_img(
    detail: SummonerInfo, card: CardInfo
) -> bytes | str:
    if not detail:
        return "token已过期"
    logger.info(detail)

    # game_info = detail['gameInfoList'][0]
    card_info = card['card']
    if (
        card_info['left_data'] is None
        or card_info['middle_data'] is None
        or card_info['right_data'] is None
    ):
        return "未能查到战绩"
    return f"""--无畏契约个人信息--
掌萌昵称: {detail['nickName']}
游戏昵称: {card_info['name']}
当前段位: {card_info['left_data']['title']}
游戏时长: {card_info['left_data']['list'][1]['content']}
赛季KDA: {card_info['right_data']['list'][0]['content']}
赛季胜率: {card_info['right_data']['list'][1]['content']}
赛季爆头: {card_info['right_data']['list'][2]['content']}
擅长武器: {card_info['right_data']['high_light']}
ACS: {card_info['left_data']['list'][2]['content']}
KAST: {card_info['middle_data']['content']}
"""
    # return "输出了"

    # return await convert_img(img)
