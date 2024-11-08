# from pathlib import Path
from pathlib import Path
from typing import List, Union, Optional

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
    Battle,
    GunInfo,
    MapInfo,
    CardInfo,
    CardOnline,
    SummonerInfo,
)

TEXTURE = Path(__file__).parent / 'texture2d'


async def get_va_info_img(uid: str) -> Union[str, bytes]:
    detail = await va_api.get_player_info(uid)

    # logger.debug(detail)
    if isinstance(detail, int):
        return get_error(detail)
    if isinstance(detail, str):
        return detail

    logger.info(detail['gameInfoList'])
    sence = detail['gameInfoList'][0]['scene']

    card = await va_api.get_player_card(uid)
    # logger.info(card)
    if isinstance(card, int):
        logger.info("card")
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card['role_info']['friend_scene']

    cardetail = await va_api.get_detail_card(scene)
    if isinstance(cardetail, int):
        logger.info("cardetail")
        return get_error(cardetail)
    if isinstance(cardetail, str):
        logger.info("cardetail")
        return cardetail

    logger.info(f'scene: {scene}')
    seeson_id = card['role_info']['session_id']
    logger.info(f'seeson_id: {seeson_id}')
    online = await va_api.get_online(uid, sence)

    if isinstance(online, int):
        logger.error(get_error(online))
        online = None
        pass

    gun = await va_api.get_gun(scene)
    if isinstance(gun, int):
        logger.error(get_error(gun))
        gun = None

    map_ = await va_api.get_map(scene)
    if isinstance(map_, int):
        logger.error(get_error(map_))
        map_ = None

    if len(detail) == 0:
        return "报错了，检查控制台"
    return await draw_va_info_img(detail, card, cardetail, online, gun, map_)


async def draw_va_info_img(
    detail: SummonerInfo,
    card: CardInfo,
    valcard: List[Battle],
    online: Optional[CardOnline],
    gun: Optional[List[GunInfo]],
    map_: Optional[List[MapInfo]],
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

    if online is not None and online.get('online_text'):
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
        (100, 260),
        f"Lv{detail['gameInfoList'][0]['level']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (100, 300),
        "游戏等级",
        (255, 255, 255, 255),
        va_font_20,
        "mm",
    )

    rank_draw.text(
        (100, 390),
        f"{card_info['left_data']['list'][1]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (100, 430), "游戏时长", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (100, 520),
        f"{card_info['left_data']['list'][2]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text((100, 560), "ACS", (255, 255, 255, 255), va_font_20, "mm")

    rank_draw.text(
        (280, 520),
        f"{card_info['middle_data']['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text((280, 560), "KAST", (255, 255, 255, 255), va_font_20, "mm")

    rank_draw.text(
        (460, 520),
        f"{card_info['round_win_rate']['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (460, 560), "回合胜率", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (640, 520),
        f"{card_info['right_data']['list'][2]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (640, 560), "赛季精准击败", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (640, 390),
        f"{card_info['right_data']['list'][1]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (640, 430), "赛季胜率", (255, 255, 255, 255), va_font_20, "mm"
    )

    rank_draw.text(
        (640, 260),
        f"{card_info['right_data']['list'][0]['content']}",
        (255, 255, 255, 255),
        va_font_42,
        "mm",
    )
    rank_draw.text(
        (640, 300), "赛季KDA", (255, 255, 255, 255), va_font_20, "mm"
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

    # 左下信息

    left_bg = Image.open(TEXTURE / 'base1.png')
    # 武器信息

    if gun is not None:
        for index, one_gun in enumerate(gun, start=1):
            if index == 9:
                break
            weapon_bg = Image.open(TEXTURE / 'weapon.png')
            weapon_draw = ImageDraw.Draw(weapon_bg)
            one_weapon = await save_img(one_gun['image_url'], "weapon")
            easy_paste(
                weapon_bg, one_weapon.resize((180, 99)), (50, -10), "lt"
            )
            weapon_draw.text(
                (20, 100), one_gun['kill'], (255, 255, 255, 255), va_font_20
            )
            weapon_draw.text(
                (50, 100),
                one_gun['kill_head'],
                (255, 255, 255, 255),
                va_font_20,
            )
            weapon_draw.text(
                (110, 100),
                one_gun['kill_round'],
                (255, 255, 255, 255),
                va_font_20,
            )
            weapon_draw.text(
                (150, 100),
                f"最远击杀: {one_gun['kill_farthest']}",
                (255, 255, 255, 255),
                va_font_20,
            )
            weapon_x = 20
            weapon_y = 350
            while index > 2:
                index -= 2
                weapon_y += 180
            weapon_x += (index - 1) * 350
            easy_paste(left_bg, weapon_bg, (weapon_x, weapon_y), "lt")

        easy_paste(img, left_bg, (20, 810), "lt")

    # 右下信息

    right_bg = Image.open(TEXTURE / 'base2.png')
    right_draw = ImageDraw.Draw(right_bg)

    # 战绩
    if valcard is not None:
        battle_y = 150
        for index, one_valcard in enumerate(valcard, start=1):
            if index == 7:
                break
            battle_bg = Image.new('RGBA', (750, 150), (0, 0, 0, 0))
            battle_draw = ImageDraw.Draw(battle_bg)

            # 基础赋值
            if one_valcard['result_title'] == '胜利':
                result = "win"
            elif one_valcard['result_title'] == '失败':
                result = "fail"
            else:
                result = "draw"

            result_color = one_valcard['result_color']
            logger.info(result_color)
            score_color = one_valcard['score_color']
            logger.info(score_color)

            head2_bg = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
            head2_draw = ImageDraw.Draw(head2_bg)
            head2_draw.rounded_rectangle(
                (0, 0, 150, 150),
                radius=75,
                fill=hex_to_rgba(result_color, alpha=255),
            )
            head2_img: Image.Image = (
                await save_img(one_valcard['image_url'], "head2")
            ).resize((150, 150))
            easy_paste(head2_bg, head2_img, (30, 25), "lt")

            battle_draw.text(
                (100, 20),
                one_valcard['result_title'],
                result_color,
                va_font_42,
            )

            battle_rank_bg = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
            battle_rank_draw = ImageDraw.Draw(battle_rank_bg)
            battle_rank_draw.rounded_rectangle(
                (0, 0, 50, 50),
                radius=25,
                fill=hex_to_rgba(score_color, alpha=255),
            )

            battle_rank_img = (
                await save_img(
                    one_valcard['score_level'][f'head_icon_{result}'], "rank"
                )
            ).resize((50, 50))
            easy_paste(battle_rank_bg, battle_rank_img, (180, 20), "lt")

            battle_draw.text(
                (220, 20), one_valcard['hero_name'], "white", va_font_42
            )
            battle_draw.text(
                (100, 80), one_valcard['content'], "white", va_font_20
            )

            battle_draw.text(
                (500, 20), one_valcard['kda'], "white", va_font_20
            )
            score_bg = Image.new('RGBA', (100, 50), (0, 0, 0, 0))
            score_draw = ImageDraw.Draw(score_bg)
            score_draw.rounded_rectangle(
                (0, 0, 50, 50),
                radius=25,
                fill=hex_to_rgba(result_color, alpha=255),
            )
            score_img = (
                await save_img(
                    one_valcard['score_level']['head_icon_win'], "score"
                )
            ).resize((50, 50))
            score_draw.text(
                (500, 20), one_valcard['score'], "white", va_font_20
            )
            easy_paste(score_bg, score_img, (200, 20), "lt")

            if one_valcard['is_friend'] == 1:
                friend_img = Image.open(TEXTURE / 'friend.png')
                easy_paste(battle_bg, friend_img, (500, 80), "lt")

            battle_draw.text(
                (550, 80), one_valcard['time'], "white", va_font_20
            )

            # 成就
            if one_valcard.get('achievement') is not None:
                x = 400
                for inde, one in enumerate(
                    one_valcard['achievement'], start=1
                ):
                    ach_bg = await save_img(one['icon'], "icon")
                    easy_paste(battle_bg, ach_bg, (x, 20), "lt")
                    x -= (ach_bg.size[0] + 10) * inde
            easy_paste(right_bg, battle_bg, (0, battle_y + index * 150), "lt")
        easy_paste(img, right_bg, (780, 810), "lt")

    return await convert_img(img)


def hex_to_rgba(hex_color, alpha=255):
    # 将十六进制颜色转换为 RGBA
    hex_color = hex_color.lstrip('#')  # 去掉开头的 #
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)
