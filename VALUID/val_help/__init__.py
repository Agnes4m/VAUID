from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

va_user_info = SV('VAL帮助')


@va_user_info.on_command(('帮助'), block=True)
async def send_va_info_msg(bot: Bot, ev: Event):
    await bot.send('to do')
