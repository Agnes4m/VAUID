# from pathlib import Path
from typing import Union, List

# from PIL import Image, ImageDraw
# from gsuid_core.logger import logger
# from gsuid_core.utils.image.convert import convert_img
# from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring

from ..utils.va_api import va_api
from ..utils.api.models import SummonerInfo
from ..utils.error_reply import get_error
# from ..utils.va_font import va_font_20, va_font_30, va_font_42


async def get_csgo_info_img(uid: str, season: str = "") -> Union[str, bytes]:
    detail = await va_api.get_player_info(uid)

    # logger.info(detail)
    if isinstance(detail, int):
        return get_error(detail)
    if isinstance(detail, str):
        return detail
    # try:
    #     if detail['statusCode'] != 0:
    #         return f"数据过期，错误代码为{detail['statusCode']}"
    # except Exception:
    #     logger.warning("获取用户详情失败！")

    if len(detail) == 0:
        return "报错了，检查控制台"
    return await draw_va_info_img(detail)


async def draw_va_info_img(detail: List[SummonerInfo]) -> bytes | str:
    if not detail:
        return "token已过期"

    return "输出了"
    # return await convert_img(img)

