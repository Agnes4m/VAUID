# from pathlib import Path
from typing import List, Union

from gsuid_core.logger import logger

# from PIL import Image, ImageDraw
# from gsuid_core.logger import logger
# from gsuid_core.utils.image.convert import convert_img
# from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring
from gsuid_core.utils.image.convert import text2pic

from .utils import save_img
from ..utils.va_api import va_api
from ..utils.error_reply import get_error
from ..utils.api.models import (
    GunInfo,
    MapInfo,
    CardInfo,
    CardOnline,
    SummonerInfo,
)

# from ..utils.va_font import va_font_20, va_font_30, va_font_42


async def get_va_info_img(uid: str) -> Union[str, bytes]:
    detail = await va_api.get_player_info(uid)

    logger.debug(detail)
    if isinstance(detail, int):
        return get_error(detail)
    if isinstance(detail, str):
        return detail

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card['role_info']['friend_scene']
    logger.info(f'scene: {scene}')
    seeson_id = card['role_info']['session_id']
    logger.info(f'seeson_id: {seeson_id}')
    online = await va_api.get_online(uid, scene)

    if isinstance(online, int):
        return get_error(online)

    gun = await va_api.get_gun(scene, seeson_id)
    if isinstance(gun, int):
        return get_error(gun)

    map_ = await va_api.get_map(scene, seeson_id)
    if isinstance(map_, int):
        return get_error(map_)

    if len(detail) == 0:
        return "报错了，检查控制台"
    return await draw_va_info_img(detail, card, online, gun, map_)


async def draw_va_info_img(
    detail: SummonerInfo,
    card: CardInfo,
    online: CardOnline,
    gun: List[GunInfo],
    map_: List[MapInfo],
) -> bytes | str:
    if not card:
        return "token已过期"
    # logger.info(detail)
    # game_info = detail['gameInfoList'][0]
    card_info = card['card']
    if (
        card_info['left_data'] is None
        or card_info['middle_data'] is None
        or card_info['right_data'] is None
    ):
        return "未能查到战绩"

    # 图片相关 card
    await save_img(card['layer_big'], "bg")
    await save_img(card['layer_small'], "bg")
    await save_img(card['bg_header_layer_url'], "bg")
    await save_img(card_info['bg_main_url'], "bg")
    await save_img(card_info['bg_bottom_layer_url'], "bg")  # 评价
    logger.info(card_info['bg_bottom_layer_url'])
    await save_img(card_info['bg_good_red_url'], "bg")
    await save_img(card_info['bg_hero_name_url'], "bg")
    await save_img(card_info['head_url'], "head")
    await save_img(card_info['hero_url'], "hero1")
    await save_img(card_info['left_data']['image_url'], "rank")
    await save_img(card_info['right_data']['image_url'], "weapon")

    # 武器图片
    if gun:
        gun_msg = "--武器--"
        for index, one in enumerate(gun, start=1):
            await save_img(
                one['image_url'], "weapon", rename=f"{one['name']}.png"
            )
            gun_msg += f"""
{index}、名称: {one['name']} | 击杀数: {one['kill']} | 爆头率: {one['kill_head']}
回合击杀: {one['kill_round']} | 最远击杀: {one['kill_farthest']}"""
    else:
        gun_msg = "未能查到武器信息"

    # 地图
    logger.info(map_)
    if map_:
        map_msg = "--地图--"
        for index, one in enumerate(map_, start=1):
            await save_img(one['map_icon'], "map", rename=f"{one['name']}.png")
            await save_img(one['best_hero_url'], "hero2")
            map_msg += f"""
{index}、名称: {one['name']} | 英雄胜率: {one['best_hero_win_rate']}
胜率: {one['win_rate']} | KD: {one['kd']} | 回合评分: {one['round_score']}"""
    else:
        map_msg = "未能查到地图信息"

    msg = f"""--无畏契约个人信息--
掌萌昵称: {detail['nickName']}
是否在线: {online['online_text'] if online.get('online_text') else '未知'}
游戏昵称: {card_info['name']}
当前段位: {card_info['left_data']['title']}
游戏时长: {card_info['left_data']['list'][1]['content']}
赛季KDA: {card_info['right_data']['list'][0]['content']}
赛季胜率: {card_info['right_data']['list'][1]['content']}
赛季爆头: {card_info['right_data']['list'][2]['content']}
擅长武器: {card_info['right_data']['high_light']}
ACS: {card_info['left_data']['list'][2]['content']}
KAST: {card_info['middle_data']['content']}

{map_msg}

{gun_msg}
"""
    return await text2pic(msg)

    # return await convert_img(img)
