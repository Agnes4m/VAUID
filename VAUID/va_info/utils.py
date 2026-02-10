from typing import Tuple, Optional

from PIL import Image

from gsuid_core.logger import logger

# from gsuid_core.logger import logger
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.image.utils import download_pic_to_image


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
