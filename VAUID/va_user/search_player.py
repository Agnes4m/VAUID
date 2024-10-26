from ..utils.va_api import va_api


async def search_player_with_name(name: str):
    msg_list = await va_api.search_player(name)
    print(msg_list)
    return msg_list