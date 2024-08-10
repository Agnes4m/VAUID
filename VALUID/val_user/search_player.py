from ..utils.va_api import wg_api


async def search_player_with_name(name: str):
    msg_list = await wg_api.search_player(name)
