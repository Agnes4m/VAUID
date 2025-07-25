import json
from typing import Dict
from pathlib import Path

import aiofiles
from PIL import Image
from gsuid_core.sv import get_plugin_prefix
from gsuid_core.help.model import PluginHelp
from gsuid_core.help.draw_new_plugin_help import get_new_help

from ..version import VAUID_version

HELP_DATA = Path(__file__).parent / 'help.json'
ICON_PATH = Path(__file__).parent / 'icon_path'
TEXT_PATH = Path(__file__).parent / 'texture2d'
ICON = TEXT_PATH / 'icon.png'

PREFIX = get_plugin_prefix('VAUID')


def get_footer():
    return Image.open(TEXT_PATH / 'footer.png')


async def get_help_data() -> Dict[str, PluginHelp]:
    async with aiofiles.open(HELP_DATA, 'rb') as file:
        return json.decode(await file.read())


async def get_help():
    return await get_new_help(
        plugin_name='VAUID',
        plugin_info={f'v{VAUID_version}': ''},
        plugin_icon=Image.open(ICON),
        plugin_help=await get_help_data(),
        plugin_prefix=PREFIX,
        help_mode='dark',
        banner_bg=Image.open(
            TEXT_PATH / 'banner_bg.png',
        ),
        banner_sub_text='恭喜EDG荣获2024年VCT CN总冠军',
        help_bg=Image.open(TEXT_PATH / 'bg.png'),
        cag_bg=Image.open(TEXT_PATH / 'cag_bg.png'),
        item_bg=Image.open(TEXT_PATH / 'item.png'),
        icon_path=ICON_PATH,
        footer=get_footer(),
        enable_cache=True,
    )
