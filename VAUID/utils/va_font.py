from pathlib import Path

from PIL import ImageFont
from gsuid_core.utils.fonts.fonts import core_font as va_font

FONT_MAIN_PATH = Path(__file__).parent / 'fonts/loli.ttf'
FONT_TIELE_PATH = Path(__file__).parent / 'fonts/title.ttf'


def va_font_main(size: int) -> ImageFont.FreeTypeFont:
    return va_font(size)


va_font_12 = va_font_main(12)
va_font_14 = va_font_main(14)
va_font_15 = va_font_main(15)
va_font_18 = va_font_main(18)
va_font_20 = va_font_main(20)
va_font_22 = va_font_main(22)
va_font_23 = va_font_main(23)
va_font_24 = va_font_main(24)
va_font_25 = va_font_main(25)
va_font_26 = va_font_main(26)
va_font_28 = va_font_main(28)
va_font_30 = va_font_main(30)
va_font_32 = va_font_main(32)
va_font_34 = va_font_main(34)
va_font_36 = va_font_main(36)
va_font_38 = va_font_main(38)
va_font_40 = va_font_main(40)
va_font_42 = va_font_main(42)
va_font_44 = va_font_main(44)
va_font_50 = va_font_main(50)
va_font_58 = va_font_main(58)
va_font_60 = va_font_main(60)
va_font_62 = va_font_main(62)
va_font_70 = va_font_main(70)
va_font_84 = va_font_main(84)