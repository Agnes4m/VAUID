# from pathlib import Path
from pathlib import Path
from typing import List, Union

from PIL import Image, ImageDraw
from gsuid_core.logger import logger

# from gsuid_core.logger import logger
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring

from .utils import save_img
from ..utils.va_api import va_api
from ..utils.error_reply import get_error
from ..utils.va_font import va_font_20, va_font_30, va_font_42
from ..utils.api.models import (
    GunInfo,
    MapInfo,
    CardInfo,
    CardOnline,
    SummonerInfo,
)

TEXTURE = Path(__file__).parent / 'texture2d'


async def get_va_info_img(uid: str) -> Union[str, bytes]:
    detail = await va_api.get_player_info(uid)

    logger.debug(detail)
    if isinstance(detail, int):
        return get_error(detail)
    if isinstance(detail, str):
        return detail

    card = await va_api.get_player_card(uid)
    logger.info(card)
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
    try:
        if (
            card_info['left_data'] is None
            or card_info['middle_data'] is None
            or card_info['right_data'] is None
            or card_info['round_win_rate'] is None
        ):
            return "未能查到战绩"
    except KeyError as e:
        logger.error(e)
        return "未能查到战绩"

    img = Image.new('RGBA', (1500, 2000), (15, 25, 35, 255))
    img_draw = ImageDraw.Draw(img)
    # 头部信息
    head_img = await draw_pic_with_ring(
        await save_img(detail['headUrl'], "head"),
        size=140,
        is_ring=True,
    )  # 128*128
    easy_paste(img, head_img, (120, 140), direction="cc")

    if online.get('online_text'):
        if "在线" in online['online_text']:
            online_img = Image.open(TEXTURE / "online" / 'online.png')
        else:
            online_img = Image.open(TEXTURE / "online" / 'offline.png')
        easy_paste(img, online_img, (180, 210), direction="cc")

    line2 = Image.open(TEXTURE / 'line2.png')
    easy_paste(img, line2, (220, 88))

    img_draw.text(
        (240, 80), detail['nickName'], (255, 255, 255, 255), va_font_42
    )
    img_draw.text(
        (450, 88), card_info['name'], (200, 200, 200, 255), va_font_30
    )
    img_draw.text(
        (240, 160), f"UID {detail['appNum']}", (200, 200, 200, 255), va_font_30
    )

    # 综合信息
    rank_bg = await save_img(card_info['bg_main_url'], "bg")
    rank_draw = ImageDraw.Draw(rank_bg)
    rank_small = await save_img(card['layer_small'], "bg")
    rank_bg.paste(rank_small, (0, 610), rank_small)

    bg_hero = await save_img(card_info['hero_url'], "hero1")
    easy_paste(rank_bg, bg_hero, (0, 0), "lt")
    # 左侧
    rank_url = card_info['left_data']['image_url']
    # rank_img = await save_img(rank_url,"rank",rename=rank_url.split("/")[-1].replace(".webp",".png"))
    rank_img = await save_img(rank_url, "rank")
    logger.info(card_info)
    rank_draw.text(
        (100, 170),
        card_info['left_data']['title'],
        (255, 255, 255, 255),
        va_font_20,
        "mm",
    )
    easy_paste(rank_bg, rank_img.resize((80, 80)), (100, 100), "cc")

    rank_draw.text(
        (100, 270),
        f"Lv{detail['gameInfoList'][0]['level']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (100, 310),
        "游戏等级",
        (255, 255, 255, 255),
        va_font_20,
        "mm",
    )

    rank_draw.text(
        (100, 410),
        f"{card_info['left_data']['list'][1]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (100, 450), "游戏时长", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (100, 550),
        f"{card_info['left_data']['list'][2]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text((100, 590), "ACS", (255, 255, 255, 255), va_font_20, "mm")

    rank_draw.text(
        (280, 550),
        f"{card_info['middle_data']['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text((280, 590), "KAST", (255, 255, 255, 255), va_font_20, "mm")

    rank_draw.text(
        (460, 550),
        f"{card_info['round_win_rate']['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (460, 590), "回合胜率", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (640, 550),
        f"{card_info['right_data']['list'][2]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (640, 590), "赛季精准击败", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (640, 410),
        f"{card_info['right_data']['list'][1]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (640, 450), "赛季胜率", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (640, 270),
        f"{card_info['right_data']['list'][0]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (640, 310), "赛季KDA", (255, 255, 255, 255), va_font_20, "mm"
    )

    weapon_img = await save_img(card_info['right_data']['image_url'], "weapon")
    easy_paste(rank_bg, weapon_img.resize((150, 82)), (640, 100), "cc")
    rank_draw.text(
        (640, 170), "最佳武器", (255, 255, 255, 255), va_font_20, "mm"
    )

    img.paste(
        rank_bg,
        (0, 200),
        rank_bg,
    )

    # 图片相关 card
    await save_img(card['layer_big'], "bg")
    await save_img(card['layer_small'], "bg")
    await save_img(card['bg_header_layer_url'], "bg")
    await save_img(card_info['bg_main_url'], "bg")  # 评价
    await save_img(card_info['bg_bottom_layer_url'], "bg")
    logger.info(card_info['left_data']['image_url'])
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
    # return await text2pic(msg)
    if msg:
        pass
    return await convert_img(img)
