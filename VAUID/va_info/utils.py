import math
import asyncio
from typing import Dict, List, Tuple, Literal, Optional
from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw
from PIL.ImageDraw import ImageDraw as ImageDrawType

from gsuid_core.logger import logger
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.image.utils import download_pic_to_image
from gsuid_core.utils.image.image_tools import easy_paste

from ..utils.va_font import va_font_20, va_font_30, va_font_42
from ..utils.api.models import (
    Vive,
    Battle,
    PFInfo,
    GunInfo,
)

TEXTURE = Path(__file__).parent / "texture2d"


# 图片缓存字典
_image_cache: Dict[str, Image.Image] = {}


async def save_img(
    img_url: str,
    img_type: str,
    size: Optional[Tuple[int, int]] = None,
    rename: Optional[str] = None,
):
    """下载图片并缓存以读取"""
    img_path = get_res_path("VAUID") / img_type / img_url.split("/")[-1]
    img_path.parent.mkdir(parents=True, exist_ok=True)
    if rename is not None:
        img_path = img_path.parent / rename
    map_img = Image.new("RGBA", (200, 600), (0, 0, 0, 255))

    if not img_path.is_file():
        for i in range(3):
            try:
                map_img = await download_pic_to_image(img_url)
                if map_img.mode != "RGBA":
                    map_img = map_img.convert("RGBA")
                if map_img:
                    map_img.save(img_path, "PNG")
                    break
                logger.warning(f"图片下载错误，正在尝试第{i + 2}次")
                if i == 2:
                    raise Exception("图片下载失败！")
                map_img = Image.open(img_path)
            except Exception:
                continue

    else:
        map_img = Image.open(img_path)
        if map_img.mode != "RGBA":
            map_img = map_img.convert("RGBA")
    if size:
        map_img.resize(size)
    return map_img


def get_cached_texture(filename: str) -> Image.Image:
    """缓存纹理图片加载，避免重复读取磁盘"""
    if filename not in _image_cache:
        _image_cache[filename] = Image.open(TEXTURE / filename)
    return _image_cache[filename].copy()


class DrawUtils:
    @staticmethod
    async def draw_hero_section(left_bg: Image.Image, hero: List[PFInfo]):
        """绘制英雄信息部分"""
        hero_bg = get_cached_texture("bg_val_mine_header.png")
        hero_draw = ImageDraw.Draw(hero_bg)

        # 绘制表头
        headers = [
            (100, 20, "英雄"),
            (300, 20, "时长"),
            (400, 20, "对局数"),
            (500, 20, "胜率"),
            (600, 20, "KD"),
        ]
        for x, y, text in headers:
            hero_draw.text((x, y), text, (255, 255, 255, 255), va_font_30, "mm")

        # 并发加载所有英雄图片
        hero_tasks = [save_img(one_hero["image_url"], "hero2") for one_hero in hero[:3]]
        hero_images = await asyncio.gather(*hero_tasks)

        for index, (one_hero, hero_img) in enumerate(zip(hero[:3], hero_images), start=1):
            hero_one = Image.new("RGBA", (700, 70), (0, 0, 0, 0))

            # 创建圆角头像背景
            head_bg = Image.new("RGBA", (50, 50), "orange")
            head_draw = ImageDraw.Draw(head_bg)
            head_draw.rounded_rectangle((0, 0, 50, 50), radius=5, fill="orange")
            easy_paste(head_bg, hero_img.resize((50, 50)), (0, 0), "lt")
            easy_paste(hero_one, head_bg, (50, 35), "cc")

            # 绘制英雄数据
            one_draw = ImageDraw.Draw(hero_one)
            one_draw.text(
                (110, 35),
                one_hero["agent_name"],
                (255, 255, 255, 255),
                va_font_30,
                "mm",
            )
            one_draw.text((380, 35), one_hero["part"], "white", va_font_30, "mm")
            one_draw.text((460, 35), one_hero["win_rate"], "white", va_font_30, "mm")
            one_draw.text((580, 35), one_hero["kd"], "white", va_font_30, "mm")

            easy_paste(hero_bg, hero_one, (20, index * 80 - 20))

        easy_paste(left_bg, hero_bg, (20, 40), "lt")

    @staticmethod
    async def draw_weapon_section(left_bg: Image.Image, gun: List[GunInfo]):
        """绘制武器信息部分"""
        if gun is None:
            return

        # 并发加载所有武器图片
        weapon_tasks = [save_img(one_gun["image_url"], "weapon") for one_gun in gun[:8]]
        weapon_images = await asyncio.gather(*weapon_tasks)

        for index, (one_gun, one_weapon) in enumerate(zip(gun[:8], weapon_images), start=1):
            weapon_bg = get_cached_texture("weapon.png")
            weapon_draw = ImageDraw.Draw(weapon_bg)

            easy_paste(weapon_bg, one_weapon.resize((190, 99)), (50, -10), "lt")

            # 绘制武器数据
            weapon_draw.text(
                (35, 110),
                one_gun["kill"],
                (255, 255, 255, 255),
                va_font_20,
                "mm",
            )
            weapon_draw.text(
                (95, 110),
                one_gun["kill_head"],
                (255, 255, 255, 255),
                va_font_20,
                "mm",
            )
            weapon_draw.text(
                (172, 110),
                one_gun["kill_round"],
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

            # 计算位置
            weapon_x = 20
            weapon_y = 370
            temp_index = index
            while temp_index > 2:
                temp_index -= 2
                weapon_y += 190
            weapon_x += (temp_index - 1) * 350

            easy_paste(left_bg, weapon_bg, (weapon_x, weapon_y), "lt")

    @staticmethod
    def draw_vive_section(right_bg: Image.Image, right_draw: ImageDrawType, vive: List[Vive]):
        """绘制射击数据部分"""
        if vive is None:
            return

        shooting_data = vive[1]["body"]["shooting"]
        positions = [(370, 45), (370, 120), (370, 195)]

        for data, pos in zip(shooting_data[:3], positions):
            right_draw.text(pos, data["content"], (255, 255, 255, 255), va_font_30, "mm")
            right_draw.text(
                (pos[0] + 280, pos[1]),
                data["sub_content"],
                (255, 255, 255, 255),
                va_font_30,
                "mm",
            )

    @staticmethod
    async def draw_battle_section(
        right_bg: Image.Image,
        right_draw: ImageDrawType,
        valcard: Optional[List[Battle]],
    ):
        """绘制战绩部分"""
        if valcard is None or isinstance(valcard, int):
            return

        battle_y = 90

        # 限制最多6场战绩
        battles_to_show = valcard[:6]

        image_tasks = []
        for battle in battles_to_show:
            image_tasks.append(save_img(battle["image_url"], "head2"))
            if battle["score_level"].get("level", "").strip():
                icon_key_map: Dict[
                    str,
                    Literal["head_icon_win", "head_icon_fail", "head_icon_draw"],
                ] = {
                    "胜利": "head_icon_win",
                    "失败": "head_icon_fail",
                    "平局": "head_icon_draw",
                }
                icon_key: Literal["head_icon_win", "head_icon_fail", "head_icon_draw"] = icon_key_map.get(
                    battle["result_title"], "head_icon_draw"
                )
                if icon_key in battle["score_level"]:
                    image_tasks.append(save_img(battle["score_level"][icon_key], "rank"))
            if battle.get("achievement"):
                for ach in battle["achievement"]:
                    image_tasks.append(save_img(ach["icon"], "icon"))

        loaded_images = await asyncio.gather(*image_tasks)
        img_idx = 0

        for index, one_valcard in enumerate(battles_to_show, start=1):
            battle_bg = Image.new("RGBA", (750, 150), (0, 0, 0, 0))
            battle_draw = ImageDraw.Draw(battle_bg)

            result_map = {
                "胜利": ("win", "green_head.png"),
                "失败": ("fail", "red_head.png"),
            }
            result, head_file = result_map.get(one_valcard["result_title"], ("draw", "grey_head.png"))

            head2_bg = get_cached_texture(head_file)
            result_color = one_valcard["result_color"]
            score_color = one_valcard["score_color"]

            # 头像
            head2_img = loaded_images[img_idx].resize((82, 82))
            img_idx += 1
            easy_paste(head2_bg, head2_img, (0, 0), "lt")
            easy_paste(battle_bg, head2_bg, (20, 25), "lt")

            # 胜负
            battle_draw.text(
                (120, 20),
                one_valcard["result_title"],
                result_color,
                va_font_42,
            )

            hero_name_x = 280

            # 评级
            if one_valcard["score_level"].get("level", "").strip():
                hero_name_x = 280
                ranks_bg = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
                ranks_draw = ImageDraw.Draw(ranks_bg)
                ranks_draw.rounded_rectangle(
                    (0, 0, 50, 50),
                    radius=5,
                    fill=hex_to_rgba(result_color, alpha=255),
                )

                ranks_img = loaded_images[img_idx].resize((50, 50))
                img_idx += 1
                easy_paste(ranks_bg, ranks_img, (0, 0), "lt")
                easy_paste(battle_bg, ranks_bg, (215, 22), "lt")
            else:
                hero_name_x = 220

            # 英雄名称和内容
            battle_draw.text(
                (hero_name_x, 20),
                one_valcard["hero_name"],
                "white",
                va_font_42,
            )
            battle_draw.text((120, 80), one_valcard["content"], "white", va_font_30)
            battle_draw.text(
                (510 - len(one_valcard["kda"] * 5), 25),
                one_valcard["kda"],
                "white",
                va_font_30,
            )

            # 评分
            if one_valcard["score"]:
                score_bg = Image.new("RGBA", (80, 40), (0, 0, 0, 0))
                score_draw = ImageDraw.Draw(score_bg)
                score_draw.rounded_rectangle(
                    (0, 0, 80, 40),
                    radius=15,
                    fill=hex_to_rgba(score_color, alpha=255),
                )
                score_draw.text((40, 20), one_valcard["score"], "white", va_font_20, "mm")
                easy_paste(battle_bg, score_bg, (610, 25), "lt")

            if one_valcard["is_friend"] == 1:
                friend_img = get_cached_texture("friend.png")
                easy_paste(battle_bg, friend_img, (485, 80), "lt")

            battle_draw.text((520, 80), one_valcard["time"], "white", va_font_20)

            if one_valcard.get("achievement"):
                x = 360
                for ach_idx, ach in enumerate(one_valcard["achievement"], start=1):
                    ach_bg = loaded_images[img_idx]
                    img_idx += 1
                    easy_paste(battle_bg, ach_bg, (x, 22), "lt")
                    x -= (ach_bg.size[0] + 5) * ach_idx

            easy_paste(right_bg, battle_bg, (0, battle_y + index * 150), "lt")

    @staticmethod
    def draw_hexagonal_panel(
        proportion_array: List[float],
        image: Image.Image,
        fill_color: Optional[Tuple[int, int, int, int]] = (255, 255, 255, 100),
        outline_color: Optional[Tuple[int, int, int, int]] = (0, 0, 0, 255),
    ):
        """绘制六边形面板

        Args:
            proportion_array: 数据数组（6 个数值，从上方开始逆时针：上，左上，左下，下，右下，右上）
            image: 要绘制的图片
            fill_color: 填充颜色，None 表示无填充
            outline_color: 边框颜色，None 表示无边框
        """
        width, height = image.size
        draw = ImageDraw.Draw(image)
        center_x, center_y = width // 2 + 20, height // 2 - 50

        # 预计算六边形顶点（从上方开始逆时针：上，左上，左下，下，右下，右上）
        # 角度：270°, 210°, 150°, 90°, 30°, 330°
        hexagon_points = [
            (
                center_x + (proportion_array[i] / 100 * 200) * math.cos(-math.pi / 2 - math.pi / 3 * i),
                center_y + (proportion_array[i] / 100 * 200) * math.sin(-math.pi / 2 - math.pi / 3 * i),
            )
            for i in range(6)
        ]

        # 绘制六边形
        draw.polygon(hexagon_points, fill=fill_color, outline=outline_color)


@lru_cache(maxsize=256)
def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """将十六进制颜色转换为 RGBA，使用LRU缓存优化性能"""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)
