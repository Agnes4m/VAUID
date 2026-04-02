from typing import Optional

from gsuid_core.models import Event

from ..utils.database.models import ValBind


async def get_bind_uid(ev: Event) -> Optional[str]:
    user_id = ev.at if ev.at else ev.user_id
    bot_id = ev.bot_id[0] if isinstance(ev.bot_id, list) else ev.bot_id
    return await ValBind.get_uid_by_game(user_id, bot_id)
