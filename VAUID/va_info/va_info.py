import asyncio
from typing import List, Union, Optional

from PIL import Image, ImageDraw

from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import easy_paste, draw_pic_with_ring

from .draw import draw_va_info_img, draw_asset_section
from .utils import save_img, get_cached_texture
from ..utils.va_api import va_api
from ..utils.va_font import va_font_20, va_font_42
from ..utils.api.models import Vive, Battle, PFInfo, GunInfo, CardOnline
from ..utils.error_reply import get_error


async def get_va_info_img(ev: Event, uid: str) -> Union[str, bytes]:
    ctx = await va_api.create_context(ev)

    detail = await va_api.get_player_info(ctx, [uid])
    if isinstance(detail, (int, str)):
        return get_error(detail) if isinstance(detail, int) else detail
    if detail is None:
        return "未查询到玩家信息"

    sence = detail["gameInfoList"][0]["scene"]

    card = await va_api.get_player_card(uid)
    if isinstance(card, int):
        return get_error(card)
    if isinstance(card, str):
        return card

    scene = card["role_info"]["friend_scene"]
    random_cookie = await ctx.get_random_cookie()

    results = await asyncio.gather(
        va_api.get_detail_card(scene, ctx.cookie, random_cookie),
        va_api.get_online(uid, sence, ctx.cookie, random_cookie),
        va_api.get_gun(uid, scene, ctx.cookie, random_cookie),
        va_api.get_pf(uid, scene, ctx.cookie, random_cookie),
        va_api.get_vive(uid, scene, ctx.cookie, random_cookie),
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

    if not detail.get("gameInfoList"):
        return "报错了，检查控制台"

    return await draw_va_info_img(detail, card, cardetail, online, gun, hero, vive)


async def get_va_asset_img(ev: Event, uid: str) -> Union[str, bytes]:
    ctx = await va_api.create_context(ev)

    detail = await va_api.get_player_info(ctx, [uid])
    if isinstance(detail, (int, str)):
        return get_error(detail) if isinstance(detail, int) else detail
    if detail is None:
        return "未查询到玩家信息"
    scene = detail["gameInfoList"][0]["scene"]

    random_cookie = await ctx.get_random_cookie()

    asset_data = await va_api.get_asset(scene, ctx.cookie, random_cookie)
    if isinstance(asset_data, int):
        return get_error(asset_data)
    if isinstance(asset_data, str):
        return asset_data
    if not asset_data:
        return "未查询到资产数据"

    image_tasks = {"head": save_img(detail["headUrl"], "head")}
    image_results = await asyncio.gather(*image_tasks.values())
    images = dict(zip(image_tasks.keys(), image_results))

    img = Image.new("RGBA", (1200, 1600), (15, 25, 35, 255))
    img_draw = ImageDraw.Draw(img)

    head_img = await draw_pic_with_ring(images["head"], size=140, is_ring=True)
    easy_paste(img, head_img, (120, 120), direction="cc")

    line2 = get_cached_texture("line2.png")
    easy_paste(img, line2, (220, 68))

    img_draw.text((240, 60), detail["nickName"], (255, 255, 255, 255), va_font_42)
    img_draw.text((240, 160), f"UID {detail['appNum']}", (200, 200, 200, 255), va_font_20)

    y_offset = 100

    skin_data = asset_data.get("skin", {})
    if skin_data:
        y_offset = await draw_asset_section(
            img,
            img_draw,
            skin_data,
            "皮肤",
            y_offset,
            icon_key="icon",
            name_key="name",
            size=(180, 80),
        )

    agent_data = asset_data.get("agent", {})
    if agent_data:
        y_offset = await draw_asset_section(
            img, img_draw, agent_data, "英雄", y_offset, icon_key="icon", name_key="name"
        )

    spray_data = asset_data.get("spray", {})
    if spray_data:
        y_offset = await draw_asset_section(
            img, img_draw, spray_data, "喷漆", y_offset, icon_key="icon", name_key="name"
        )

    card_data = asset_data.get("card", {})
    if card_data:
        y_offset = await draw_asset_section(
            img,
            img_draw,
            card_data,
            "卡面",
            y_offset,
            icon_key="icon",
            name_key="name",
            size=(80, 150),
        )

    charm_data = asset_data.get("charm", {})
    if charm_data:
        y_offset = await draw_asset_section(
            img,
            img_draw,
            charm_data,
            "挂饰",
            y_offset + 50,
            icon_key="icon",
            name_key="name",
        )

    return await convert_img(img)
