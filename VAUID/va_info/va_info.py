import asyncio
from typing import List, Union, Optional

from PIL import Image, ImageDraw

from gsuid_core.logger import logger

# from gsuid_core.logger import logger
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring

from .utils import DrawUtils, save_img, get_cached_texture
from ..utils.va_api import va_api
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
from ..utils.error_reply import get_error


async def get_va_info_img(uid: str) -> Union[str, bytes]:
    # 基础信息
    detail = await va_api.get_player_info(uid)

    if isinstance(detail, (int, str)):
        return get_error(detail) if isinstance(detail, int) else detail

    sence = detail["gameInfoList"][0]["scene"]

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card["role_info"]["friend_scene"]
    # 并发请求所有数据
    results = await asyncio.gather(
        va_api.get_detail_card(scene),
        va_api.get_online(uid, sence),
        va_api.get_gun(uid, scene),
        va_api.get_pf(uid, scene),
        va_api.get_vive(uid, scene),
        return_exceptions=True,
    )

    cardetail_raw, online_raw, gun_raw, hero_raw, vive_raw = results

    cardetail: Optional[List[Battle]] = None
    if isinstance(cardetail_raw, (int, str, BaseException)):
        logger.info(f"cardetail error: {cardetail_raw}")
    else:
        cardetail = cardetail_raw

    online: Optional[CardOnline] = None
    if isinstance(online_raw, (int, BaseException)):
        logger.error(
            f"online error: {get_error(online_raw) if isinstance(online_raw, int) else online_raw}"
        )
    else:
        online = online_raw

    if isinstance(gun_raw, BaseException):
        logger.error(f"gun error: {gun_raw}")
        return "获取武器数据失败"
    if isinstance(gun_raw, int):
        return get_error(gun_raw)
    gun: List[GunInfo] = gun_raw

    if isinstance(hero_raw, BaseException):
        logger.error(f"hero error: {hero_raw}")
        return "获取英雄数据失败"
    if isinstance(hero_raw, int):
        return get_error(hero_raw)
    hero: List[PFInfo] = hero_raw

    if isinstance(vive_raw, BaseException):
        logger.error(f"vive error: {vive_raw}")
        return "获取vive数据失败"
    if isinstance(vive_raw, int):
        return get_error(vive_raw)
    vive: List[Vive] = vive_raw

    # seeson_id = card["role_info"]["session_id"]
    # logger.info(f"seeson_id: {seeson_id}")

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

    card_info = card["card"]
    try:
        if (
            card_info["left_data"] is None
            or card_info["middle_data"] is None
            or card_info["right_data"] is None
            or card_info["round_win_rate"] is None
        ):
            return "未能查到战绩"
    except KeyError as e:
        logger.error(e)
        return "未能查到战绩"

    # 并发加载所有需要的远程图片
    image_tasks = {
        "head": save_img(detail["headUrl"], "head"),
        "bg": save_img(card_info["bg_main_url"], "bg"),
        "rank_small": save_img(card["layer_small"], "bg"),
        "bg_hero": save_img(card_info["hero_url"], "hero1"),
        "rank": save_img(card_info["left_data"]["image_url"], "rank"),
        "weapon": save_img(card_info["right_data"]["image_url"], "weapon"),
    }
    image_results = await asyncio.gather(*image_tasks.values())
    images = dict(zip(image_tasks.keys(), image_results))

    # 创建主画布
    img = Image.new("RGBA", (1500, 2000), (15, 25, 35, 255))
    img_draw = ImageDraw.Draw(img)

    # === 头部信息 ===
    head_img = await draw_pic_with_ring(
        images["head"],
        size=140,
        is_ring=True,
    )
    easy_paste(img, head_img, (120, 120), direction="cc")

    # 在线状态
    if online is not None and online.get("online_text"):
        online_filename = (
            "online.png" if "在线" in online["online_text"] else "offline.png"
        )
        online_img = get_cached_texture(f"online/{online_filename}")
        easy_paste(img, online_img, (180, 190), direction="cc")

    # 分割线
    line2 = get_cached_texture("line2.png")
    easy_paste(img, line2, (220, 68))

    # 文字信息
    img_draw.text(
        (240, 60), detail["nickName"], (255, 255, 255, 255), va_font_42
    )
    img_draw.text(
        (240, 120), card_info["name"], (200, 200, 200, 255), va_font_30
    )
    img_draw.text(
        (240, 160), f"UID {detail['appNum']}", (200, 200, 200, 255), va_font_20
    )

    # === 综合信息 ===
    rank_bg = images["bg"]
    rank_draw = ImageDraw.Draw(rank_bg)
    rank_bg.paste(images["rank_small"], (0, 610), images["rank_small"])
    easy_paste(rank_bg, images["bg_hero"], (0, 0), "lt")

    # 使用辅助函数绘制文本，减少重复代码
    def draw_stat(x: int, y: int, value: str, label: str):
        rank_draw.text((x, y), value, (255, 255, 255, 255), va_font_42, "mm")
        rank_draw.text(
            (x, y + 40), label, (255, 255, 255, 255), va_font_20, "mm"
        )

    # 左侧信息
    rank_draw.text(
        (100, 170),
        card_info["left_data"]["title"],
        (255, 255, 255, 255),
        va_font_20,
        "mm",
    )
    easy_paste(rank_bg, images["rank"].resize((80, 80)), (100, 100), "cc")

    draw_stat(100, 260, f"Lv{detail['gameInfoList'][0]['level']}", "游戏等级")
    draw_stat(
        100, 390, card_info["left_data"]["list"][1]["content"], "游戏时长"
    )
    draw_stat(100, 520, card_info["left_data"]["list"][2]["content"], "ACS")
    draw_stat(280, 520, card_info["middle_data"]["content"], "KAST")
    draw_stat(460, 520, card_info["round_win_rate"]["content"], "回合胜率")
    draw_stat(
        640, 520, card_info["right_data"]["list"][2]["content"], "赛季精准击败"
    )
    draw_stat(
        640, 390, card_info["right_data"]["list"][1]["content"], "赛季胜率"
    )
    draw_stat(
        640, 260, card_info["right_data"]["list"][0]["content"], "赛季KDA"
    )

    # 最佳武器
    easy_paste(rank_bg, images["weapon"].resize((150, 82)), (640, 100), "cc")
    rank_draw.text(
        (640, 170), "最佳武器", (255, 255, 255, 255), va_font_20, "mm"
    )

    img.paste(rank_bg, (0, 180), rank_bg)

    # === 左下信息 ===
    left_bg = get_cached_texture("base1.png")
    # left_draw = ImageDraw.Draw(left_bg)

    # 绘制英雄/武器数据
    await DrawUtils.draw_hero_section(left_bg, hero)
    await DrawUtils.draw_weapon_section(left_bg, gun)

    easy_paste(img, left_bg, (20, 790), "lt")

    # === 右上信息 - 能力图 ===
    img_draw.text((800, 100), "能力图❔", (255, 255, 255, 255), va_font_42)

    six_info = vive[1]["body"]["radar_chart"]["tabs"][0]
    p_six_info = vive[1]["body"]["radar_chart"]["player_dict"]

    base_image = get_cached_texture("six_bg.png")

    # 绘制六边形
    DrawUtils.draw_hexagonal_panel(
        [float(x) for x in six_info["proportion_array"]],
        base_image,
        fill_color=(255, 255, 255, 100),
    )

    # 绘制数据标签
    draw_base = ImageDraw.Draw(base_image)
    data_positions = [
        (365, 88),
        (135, 210),
        (135, 392),
        (365, 480),
        (590, 392),
        (590, 210),
    ]
    for pos, (six_val, p_six_val) in zip(
        data_positions, zip(six_info["data_array"], p_six_info["data_array"])
    ):
        draw_base.text(
            pos, f"{p_six_val} | {six_val}", "white", va_font_20, "mm"
        )

    draw_base.text(
        (465, 628), six_info["sub_tab_name"], "white", va_font_30, "mm"
    )

    easy_paste(img, base_image, (750, 50))

    # === 右下信息 ===
    right_bg = get_cached_texture("base2.png")
    right_draw = ImageDraw.Draw(right_bg)

    # 绘制射击数据
    DrawUtils.draw_vive_section(right_bg, right_draw, vive)

    # 绘制战绩
    await DrawUtils.draw_battle_section(right_bg, right_draw, valcard)

    easy_paste(img, right_bg, (750, 780), "lt")

    # === 页脚 ===
    footer = get_cached_texture("footer.png")
    easy_paste(img, footer, (750, 1980), "cc")

    return await convert_img(img)
