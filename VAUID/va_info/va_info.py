import math
import asyncio
from typing import List, Union, Optional

from PIL import Image, ImageDraw

from gsuid_core.logger import logger
from gsuid_core.models import Event
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
from ..utils.api.model.asset import (
    SkinData,
    AgentData,
    CollectionData,
)


async def get_va_info_img(ev: Event, uid: str) -> Union[str, bytes]:
    # 创建查询上下文 - 使用查询人自身的 cookie
    ctx = await va_api.create_context(ev)

    # 基础信息
    detail = await va_api.get_player_info(ctx, [uid])

    if isinstance(detail, (int, str)):
        return get_error(detail) if isinstance(detail, int) else detail

    sence = detail["gameInfoList"][0]["scene"]

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card["role_info"]["friend_scene"]

    # 并发请求所有数据，使用查询上下文中的 cookie
    results = await asyncio.gather(
        va_api.get_detail_card(uid, scene, ctx.cookie, ctx.get_random_cookie),
        va_api.get_online(uid, sence, ctx.cookie, ctx.get_random_cookie),
        va_api.get_gun(uid, scene, ctx.cookie, ctx.get_random_cookie),
        va_api.get_pf(uid, scene, ctx.cookie, ctx.get_random_cookie),
        va_api.get_vive(uid, scene, ctx.cookie, ctx.get_random_cookie),
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
        logger.error(f"online error: {get_error(online_raw) if isinstance(online_raw, int) else online_raw}")
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
        return "获取 vive 数据失败"
    if isinstance(vive_raw, int):
        return get_error(vive_raw)
    vive: List[Vive] = vive_raw

    # seeson_id = card["role_info"]["session_id"]
    # logger.info(f"seeson_id: {seeson_id}")

    if len(detail) == 0:
        return "报错了，检查控制台"

    return await draw_va_info_img(detail, card, cardetail, online, gun, hero, vive)


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
        return "token 已过期"

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
        online_filename = "online.png" if "在线" in online["online_text"] else "offline.png"
        online_img = get_cached_texture(f"online/{online_filename}")
        easy_paste(img, online_img, (180, 190), direction="cc")

    # 分割线
    line2 = get_cached_texture("line2.png")
    easy_paste(img, line2, (220, 68))

    # 文字信息
    img_draw.text((240, 60), detail["nickName"], (255, 255, 255, 255), va_font_42)
    img_draw.text((240, 120), card_info["name"], (200, 200, 200, 255), va_font_30)
    img_draw.text((240, 160), f"UID {detail['appNum']}", (200, 200, 200, 255), va_font_20)

    # === 综合信息 ===
    rank_bg = images["bg"]
    rank_draw = ImageDraw.Draw(rank_bg)
    rank_bg.paste(images["rank_small"], (0, 610), images["rank_small"])
    easy_paste(rank_bg, images["bg_hero"], (0, 0), "lt")

    # 使用辅助函数绘制文本，减少重复代码
    def draw_stat(x: int, y: int, value: str, label: str):
        rank_draw.text((x, y), value, (255, 255, 255, 255), va_font_42, "mm")
        rank_draw.text((x, y + 40), label, (255, 255, 255, 255), va_font_20, "mm")

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
    draw_stat(100, 390, card_info["left_data"]["list"][1]["content"], "游戏时长")
    draw_stat(100, 520, card_info["left_data"]["list"][2]["content"], "ACS")
    draw_stat(280, 520, card_info["middle_data"]["content"], "KAST")
    draw_stat(460, 520, card_info["round_win_rate"]["content"], "回合胜率")
    draw_stat(640, 520, card_info["right_data"]["list"][2]["content"], "赛季精准击败")
    draw_stat(640, 390, card_info["right_data"]["list"][1]["content"], "赛季胜率")
    draw_stat(640, 260, card_info["right_data"]["list"][0]["content"], "赛季 KDA")

    # 最佳武器
    easy_paste(rank_bg, images["weapon"].resize((150, 82)), (640, 100), "cc")
    rank_draw.text((640, 170), "最佳武器", (255, 255, 255, 255), va_font_20, "mm")

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

    # 调试：打印两组数据
    logger.info(f"标准值 proportion_array: {six_info['proportion_array']}")
    logger.info(f"玩家值 proportion_array: {p_six_info['proportion_array']}")

    base_image = get_cached_texture("six_bg.png")

    # 1. 先绘制标准六边形（灰色细线，作为背景基准）
    DrawUtils.draw_hexagonal_panel(
        [float(x) for x in six_info["proportion_array"]],
        base_image,
        fill_color=None,
        outline_color=(150, 150, 150, 200),  # 灰色，半透明
    )

    # 2. 再绘制玩家六边形（蓝色填充 + 蓝色边框，突出显示）
    DrawUtils.draw_hexagonal_panel(
        [float(x) for x in p_six_info["proportion_array"]],
        base_image,
        fill_color=(100, 149, 237, 180),  # 半透明蓝色填充
        outline_color=(65, 105, 225, 255),  # 蓝色边框
    )

    # 绘制数据标签 - 固定位置，向外偏离中心 20 像素
    # 数据数组顺序：从上方开始逆时针 - 上，左上，左下，下，右下，右上
    draw_base = ImageDraw.Draw(base_image)
    center_x, center_y = (
        base_image.size[0] // 2 + 20,
        base_image.size[1] // 2 - 50,
    )

    # 标签位置（按数据顺序：上，左上，左下，下，右下，右上）
    data_positions = [
        (365, 88),  # 上方
        (135, 210),  # 左上
        (135, 392),  # 左下
        (365, 480),  # 下方
        (590, 392),  # 右下
        (590, 210),  # 右上
    ]

    for pos, (six_val, p_six_val) in zip(data_positions, zip(six_info["data_array"], p_six_info["data_array"])):
        # 计算从中心到标签位置的方向向量
        dx = pos[0] - center_x
        dy = pos[1] - center_y
        distance = math.sqrt(dx**2 + dy**2)
        # 向外移动 20 像素
        new_x = pos[0] + (dx / distance) * 20
        new_y = pos[1] + (dy / distance) * 20
        draw_base.text((new_x, new_y), f"{p_six_val} | {six_val}", "white", va_font_20, "mm")

    draw_base.text((465, 628), six_info["sub_tab_name"], "white", va_font_30, "mm")

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


async def draw_asset_section(
    img: Image.Image,
    img_draw: ImageDraw.ImageDraw,
    section_data: Union[SkinData, AgentData, CollectionData],
    section_name: str,
    y_offset: int,
    size: tuple[int, int] = (80, 80),
    icon_key: str = "icon",
    name_key: str = "name",
    title_offset: int = 50,  # 标题下方间距
    row_offset: int = 120,  # 每行物品下方间距
    max_items: int = 20,  # 最多显示物品数
    items_per_row: int = 5,  # 每行物品数
    item_spacing: int = 220,  # 物品之间水平间距
    section_bottom_offset: int = 50,  # 分类底部间距
) -> int:
    """绘制资产分类区域

    Args:
        img: 主画布
        img_draw: 画布绘制对象
        section_data: 分类数据
        section_name: 分类名称
        y_offset: 当前 Y 坐标
        size: 图标大小 (宽，高)
        icon_key: 图标字段名
        name_key: 名称字段名
        title_offset: 标题下方间距
        row_offset: 每行物品下方间距
        max_items: 最多显示物品数
        items_per_row: 每行物品数
        item_spacing: 物品之间水平间距
        section_bottom_offset: 分类底部间距

    Returns:
        更新后的 Y 坐标
    """
    items = section_data.get("list", [])
    if not items:
        return y_offset

    # 分类标题
    img_draw.text((100, y_offset), section_name, (255, 255, 255, 255), va_font_30)
    y_offset += title_offset

    # 绘制物品
    for i, item in enumerate(items[:max_items]):
        if i % items_per_row == 0:
            y_offset += row_offset

        x = 100 + (i % items_per_row) * item_spacing
        y = y_offset

        # 绘制物品图标
        try:
            icon_url = item.get(icon_key, "") or item.get("avatar", "")
            if icon_url:
                item_icon = await save_img(icon_url, "asset_icon")
                item_icon = item_icon.resize(size)
                easy_paste(img, item_icon, (x, y), "lt")
        except Exception:
            pass

        # 绘制物品名称
        item_name = item.get(name_key, "未知物品")
        img_draw.text((x + 50, y + 90), item_name, (255, 255, 255, 255), va_font_20, "mm")

    y_offset += section_bottom_offset
    return y_offset


async def get_va_asset_img(ev: Event, uid: str) -> Union[str, bytes]:
    """获取玩家资产信息图片

    Args:
        ev: 事件对象
        uid: 目标用户 UID

    Returns:
        图片字节或错误信息字符串
    """
    # 创建查询上下文 - 使用查询人自身的 cookie
    ctx = await va_api.create_context(ev)

    # 获取玩家信息以获取 scene
    detail = await va_api.get_player_info(ctx, [uid])
    if isinstance(detail, (int, str)):
        return get_error(detail) if isinstance(detail, int) else detail
    if detail is None:
        return "未查询到玩家信息"
    scene = detail["gameInfoList"][0]["scene"]

    # 获取资产数据
    asset_data = await va_api.get_asset(scene, ctx.cookie, ctx.get_random_cookie)
    if isinstance(asset_data, int):
        return get_error(asset_data)
    if isinstance(asset_data, str):
        return asset_data
    if not asset_data or not isinstance(asset_data, dict):
        return "未查询到资产数据"

    # 创建画布
    img = Image.new("RGBA", (1200, 1600), (15, 25, 35, 255))
    img_draw = ImageDraw.Draw(img)

    # 标题
    img_draw.text((600, 30), f"UID {detail['nickName']} 的资产", (255, 255, 255, 255), va_font_42, "mm")

    # 绘制各分类
    y_offset = 100

    # 1. 皮肤 (Skin)
    skin_data = asset_data.get("skin", {})
    if skin_data:
        y_offset = await draw_asset_section(
            img, img_draw, skin_data, "皮肤", y_offset, icon_key="icon", name_key="name", size=(150, 80)
        )

    # 2. 英雄 (Agent)
    agent_data = asset_data.get("agent", {})
    if agent_data:
        y_offset = await draw_asset_section(
            img, img_draw, agent_data, "英雄", y_offset, icon_key="icon", name_key="name"
        )

    # 3. 喷漆 (Spray)
    spray_data = asset_data.get("spray", {})
    if spray_data:
        y_offset = await draw_asset_section(
            img, img_draw, spray_data, "喷漆", y_offset, icon_key="icon", name_key="name"
        )

    # 4. 卡面 (Card)
    card_data = asset_data.get("card", {})
    if card_data:
        y_offset = await draw_asset_section(
            img, img_draw, card_data, "卡面", y_offset, icon_key="icon", name_key="name", size=(80, 150)
        )

    # 5. 挂饰 (Charm)
    charm_data = asset_data.get("charm", {})
    if charm_data:
        y_offset = await draw_asset_section(
            img, img_draw, charm_data, "挂饰", y_offset, icon_key="icon", name_key="name"
        )

    return await convert_img(img)
