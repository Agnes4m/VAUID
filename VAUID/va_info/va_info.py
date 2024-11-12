import math
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
    Vive,
    Battle,
    PFInfo,
    GunInfo,
    CardInfo,
    CardOnline,
    SummonerInfo,
)

TEXTURE = Path(__file__).parent / 'texture2d'


async def get_va_info_img(uid: str) -> Union[str, bytes]:
    detail = await va_api.get_player_info(uid)

    if isinstance(detail, int):
        return get_error(detail)
    if isinstance(detail, str):
        return detail

    sence = detail['gameInfoList'][0]['scene']

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card['role_info']['friend_scene']

    cardetail = await va_api.get_detail_card(scene)
    if isinstance(cardetail, int):
        logger.info(cardetail)
        cardetail = None
    if isinstance(cardetail, str):
        logger.info(cardetail)
        cardetail = None

    # logger.info(f'scene: {scene}')
    seeson_id = card['role_info']['session_id']
    logger.info(f'seeson_id: {seeson_id}')
    online = await va_api.get_online(uid, sence)

    if isinstance(online, int):
        logger.error(get_error(online))
        online = None

    gun = await va_api.get_gun(scene)
    if isinstance(gun, int):
        return get_error(gun)

    # map_ = await va_api.get_map(scene)
    # if isinstance(map_, int):
    #     logger.error(get_error(map_))
    #     map_ = None
    hero = await va_api.get_pf(scene)
    if isinstance(hero, int):
        return get_error(hero)

    vive = await va_api.get_vive(scene)
    if isinstance(vive, int):
        return get_error(vive)

    if len(detail) == 0:
        return "报错了，检查控制台"
    return await draw_va_info_img(
        detail, card, cardetail, online, gun, hero, vive
    )


async def draw_va_info_img(
    detail: SummonerInfo,
    card: CardInfo,
    valcard: Optional[List[Battle]],
    online: Optional[CardOnline],
    gun: List[GunInfo],
    hero: List[PFInfo],
    vive: List[Vive],
) -> bytes | str:
    if not card:
        return "token已过期"
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
        (240, 140), card_info['name'], (200, 200, 200, 255), va_font_30
    )
    img_draw.text(
        (240, 180), f"UID {detail['appNum']}", (200, 200, 200, 255), va_font_20
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
    # logger.info(card_info)
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

    hero_bg = Image.open(TEXTURE / 'bg_val_mine_header.png')
    # 750*368
    hero_draw = ImageDraw.Draw(hero_bg)
    hero_draw.text(
        (100, 20),
        "英雄",
        (255, 255, 255, 255),
        va_font_30,
        "mm",
    )
    hero_draw.text(
        (300, 20),
        "时长",
        (255, 255, 255, 255),
        va_font_30,
        "mm",
    )
    hero_draw.text(
        (400, 20),
        "对局数",
        (255, 255, 255, 255),
        va_font_30,
        "mm",
    )
    hero_draw.text(
        (500, 20),
        "胜率",
        (255, 255, 255, 255),
        va_font_30,
        "mm",
    )
    hero_draw.text(
        (600, 20),
        "KD",
        (255, 255, 255, 255),
        va_font_30,
        "mm",
    )

    for index, one_hero in enumerate(hero, start=1):
        if index == 4:
            break
        hero_one = Image.new('RGBA', (700, 70), (0, 0, 0, 0))
        hero_img = await save_img(one_hero['image_url'], "hero2")

        head_bg = Image.new('RGBA', (50, 50), "orange")
        head_draw = ImageDraw.Draw(head_bg)
        head_draw.rounded_rectangle((0, 0, 50, 50), radius=5, fill="orange")
        easy_paste(head_bg, hero_img.resize((50, 50)), (0, 0), "lt")
        easy_paste(hero_one, head_bg, (50, 35), "cc")

        one_draw = ImageDraw.Draw(hero_one)
        one_draw.text(
            (110, 35),
            one_hero['agent_name'],
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
        one_draw.text(
            (380, 35),
            one_hero['part'],
            "white",
            va_font_30,
            "mm",
        )
        one_draw.text(
            (460, 35),
            one_hero['win_rate'],
            "white",
            va_font_30,
            "mm",
        )
        one_draw.text(
            (580, 35),
            one_hero['kd'],
            "white",
            va_font_30,
            "mm",
        )
        easy_paste(hero_bg, hero_one, (20, index * 80 - 20))

    easy_paste(left_bg, hero_bg, (20, 40), "lt")

    # 武器信息

    if gun is not None:
        for index, one_gun in enumerate(gun, start=1):
            if index == 9:
                break
            weapon_bg = Image.open(TEXTURE / 'weapon.png')
            weapon_draw = ImageDraw.Draw(weapon_bg)
            one_weapon = await save_img(one_gun['image_url'], "weapon")
            easy_paste(
                weapon_bg, one_weapon.resize((190, 99)), (50, -10), "lt"
            )
            weapon_draw.text(
                (35, 110),
                one_gun['kill'],
                (255, 255, 255, 255),
                va_font_20,
                "mm",
            )
            weapon_draw.text(
                (95, 110),
                one_gun['kill_head'],
                (255, 255, 255, 255),
                va_font_20,
                "mm",
            )
            weapon_draw.text(
                (172, 110),
                one_gun['kill_round'],
                (255, 255, 255, 255),
                va_font_20,
                "mm",
            )
            weapon_draw.text(
                (240, 100),
                f"{one_gun['kill_farthest']}",
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

    # 右上信息

    img_draw.text((800, 100), "能力图❔", (255, 255, 255, 255), va_font_42)
    six_info = vive[1]['body']['radar_chart']["tabs"][0]
    tab_name = six_info['sub_tab_name']
    data_array = six_info['data_array']
    proportion_array = six_info['proportion_array']
    """矢量长度，0-100范围长度"""
    desc_array = six_info['desc_array']

    # width, height = 800, 1000
    # background_color = (0, 0, 0, 0)  # 透明背景
    # border_color = "white"
    # font_color = "white"

    # six_img = Image.new('RGBA', (width, height), background_color)
    # draw = ImageDraw.Draw(six_img)

    # center_x, center_y = width // 2, height // 2
    # hexagon_points = []

    # # 计算六边形的顶点
    # for i in range(6):
    #     angle = math.pi / 3 * i
    #     length = proportion_array[i] / 100 * 300  # 将比例转换为长度
    #     x = center_x + length * math.cos(angle)
    #     y = center_y + length * math.sin(angle)
    #     hexagon_points.append((x, y))

    # # 绘制六边形
    # draw.polygon(hexagon_points, fill=(255, 255, 255, 0), outline=border_color)  # 透明填充

    # # 绘制数据值和描述
    # for i in range(len(data_array)):
    #     x, y = hexagon_points[i]
    #     draw.line((center_x, center_y, x, y), fill=border_color, width=2)  # 连接中心点到顶点

    #     # 根据位置调整文本位置，避免重叠并拉远位置
    #     text_offset_x = 40 * math.cos(math.pi / 3 * i)
    #     text_offset_y = 40 * math.sin(math.pi / 3 * i)

    #     draw.text((x + text_offset_x, y + text_offset_y), f"{data_array[i]}",  font_color,va_font_20, "mm")
    #     draw.text((x + text_offset_x, y + text_offset_y + 25), f"{desc_array[i]}",  font_color,va_font_20, "mm")

    # # 绘制标题
    # draw.text((center_x, height - 200), tab_name, font=va_font_20, fill=font_color)
    # easy_paste(img, six_img,(800, 0))

    p_six_info = vive[1]['body']['radar_chart']["player_dict"]
    p_data_array = p_six_info['data_array']
    p_proportion_array = p_six_info['proportion_array']
    """矢量长度，0-100范围长度"""

    # 创建基础图像
    base_image = Image.open(TEXTURE / 'six_bg.png')

    # 绘制第一个六边形
    draw_hexagonal_panel(
        six_info['proportion_array'],
        base_image,
        fill_color=(255, 255, 255, 100),  # 透明填充
    )

    # 绘制第二个白色实心六边形
    draw_hexagonal_panel(
        p_six_info['proportion_array'],
        base_image,
        fill_color=(255, 255, 255, 255),  # 白色实心填充
    )

    # 文字部分
    draw_base = ImageDraw.Draw(base_image)
    draw_base.text(
        (365, 88),
        f"{p_six_info['data_array'][0]} | {six_info['data_array'][0]}",
        "white",
        va_font_20,
        "mm",
    )
    draw_base.text(
        (135, 210),
        f"{p_six_info['data_array'][1]} | {six_info['data_array'][1]}",
        "white",
        va_font_20,
        "mm",
    )
    draw_base.text(
        (135, 392),
        f"{p_six_info['data_array'][2]} | {six_info['data_array'][2]}",
        "white",
        va_font_20,
        "mm",
    )
    draw_base.text(
        (365, 480),
        f"{p_six_info['data_array'][3]} | {six_info['data_array'][3]}",
        "white",
        va_font_20,
        "mm",
    )
    draw_base.text(
        (590, 392),
        f"{p_six_info['data_array'][4]} | {six_info['data_array'][4]}",
        "white",
        va_font_20,
        "mm",
    )
    draw_base.text(
        (590, 210),
        f"{p_six_info['data_array'][5]} | {six_info['data_array'][5]}",
        "white",
        va_font_20,
        "mm",
    )

    draw_base.text(
        (460, 628), six_info['sub_tab_name'], "white", va_font_30, "mm"
    )

    easy_paste(img, base_image, (800, 0))

    # 右下信息

    right_bg = Image.open(TEXTURE / 'base2.png')
    right_draw = ImageDraw.Draw(right_bg)
    if vive is not None:
        right_draw.text(
            (370, 45),
            f"{vive[1]['body']['shooting'][0]['content']}",
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
        right_draw.text(
            (650, 45),
            f"{vive[1]['body']['shooting'][0]['sub_content']}",
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
        right_draw.text(
            (370, 120),
            f"{vive[1]['body']['shooting'][1]['content']}",
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
        right_draw.text(
            (650, 120),
            f"{vive[1]['body']['shooting'][1]['sub_content']}",
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
        right_draw.text(
            (370, 195),
            f"{vive[1]['body']['shooting'][2]['content']}",
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
        right_draw.text(
            (650, 195),
            f"{vive[1]['body']['shooting'][2]['sub_content']}",
            (255, 255, 255, 255),
            va_font_30,
            "mm",
        )
    # 战绩
    if valcard is not None and not isinstance(valcard, int):
        battle_y = 110
        for index, one_valcard in enumerate(valcard, start=1):
            if index == 7:
                break
            battle_bg = Image.new('RGBA', (750, 150), (0, 0, 0, 0))
            battle_draw = ImageDraw.Draw(battle_bg)

            # 基础赋值
            if one_valcard['result_title'] == '胜利':
                head2_bg = Image.open(TEXTURE / 'green_head.png')
                result = "win"
            elif one_valcard['result_title'] == '失败':
                head2_bg = Image.open(TEXTURE / 'red_head.png')

                result = "fail"
            else:
                head2_bg = Image.open(TEXTURE / 'grey_head.png')

                result = "draw"

            result_color = one_valcard['result_color']
            # logger.info(result_color)
            score_color = one_valcard['score_color']
            # logger.info(score_color)

            head2_img: Image.Image = (
                await save_img(one_valcard['image_url'], "head2")
            ).resize((82, 82))
            easy_paste(head2_bg, head2_img, (0, 0), "lt")
            easy_paste(battle_bg, head2_bg, (20, 25), "lt")

            battle_draw.text(
                (120, 20),
                one_valcard['result_title'],
                result_color,
                va_font_42,
            )
            if one_valcard['score_level'].get("level").strip():
                hero_name = 280
                ranks_bg = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
                ranks_draw = ImageDraw.Draw(ranks_bg)
                ranks_draw.rounded_rectangle(
                    (0, 0, 50, 50),
                    radius=5,
                    fill=hex_to_rgba(result_color, alpha=255),
                )
                ranks_img = await save_img(
                    one_valcard['score_level'][f'head_icon_{result}'], "rank"
                )
                easy_paste(ranks_bg, ranks_img.resize((50, 50)), (0, 0), "lt")

                easy_paste(battle_bg, ranks_bg, (215, 22), "lt")
            else:
                hero_name = 220

            battle_draw.text(
                (hero_name, 20), one_valcard['hero_name'], "white", va_font_42
            )
            battle_draw.text(
                (120, 80), one_valcard['content'], "white", va_font_30
            )

            battle_draw.text(
                (485, 25), one_valcard['kda'], "white", va_font_30
            )

            if one_valcard['score']:
                score_bg = Image.new('RGBA', (80, 40), (0, 0, 0, 0))
                score_draw = ImageDraw.Draw(score_bg)
                score_draw.rounded_rectangle(
                    (0, 0, 80, 40),
                    radius=15,
                    fill=hex_to_rgba(score_color, alpha=255),
                )

                score_draw.text(
                    (40, 20), one_valcard['score'], "white", va_font_20, "mm"
                )
                easy_paste(battle_bg, score_bg, (610, 25), "lt")
                # logger.info(one_valcard['score'])

            if one_valcard['is_friend'] == 1:
                friend_img = Image.open(TEXTURE / 'friend.png')
                easy_paste(battle_bg, friend_img, (485, 80), "lt")

            battle_draw.text(
                (520, 80), one_valcard['time'], "white", va_font_20
            )

            # 成就
            if one_valcard.get('achievement') is not None:
                x = 360
                for inde, one in enumerate(
                    one_valcard['achievement'], start=1
                ):
                    ach_bg = await save_img(one['icon'], "icon")
                    easy_paste(battle_bg, ach_bg, (x, 22), "lt")
                    x -= (ach_bg.size[0] + 5) * inde
            easy_paste(right_bg, battle_bg, (0, battle_y + index * 150), "lt")
    easy_paste(img, right_bg, (780, 800), "lt")

    return await convert_img(img)


def hex_to_rgba(hex_color, alpha=255):
    # 将十六进制颜色转换为 RGBA
    hex_color = hex_color.lstrip('#')  # 去掉开头的 #
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def draw_hexagonal_panel(
    proportion_array, image, fill_color=(255, 255, 255, 0)
):
    width, height = 600, 600
    draw = ImageDraw.Draw(image)

    center_x, center_y = width // 2 + 50, height // 2 + 50
    hexagon_points = []

    # 计算六边形的顶点（从正上方开始，逆时针）
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 2  # 从正上方开始
        length = proportion_array[i] / 100 * 300  # 将比例转换为长度
        x = center_x + length * math.cos(angle)
        y = center_y + length * math.sin(angle)
        hexagon_points.append((x, y))

    # 绘制六边形
    draw.polygon(
        hexagon_points, fill=fill_color, outline=(0, 0, 0)
    )  # 白色实心填充
