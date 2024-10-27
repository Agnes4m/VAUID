from ..utils.va_api import va_api
from ..utils.error_reply import get_error


async def draw_va_battle_list_img(tag: str):
    msg_dict = await va_api.search_player(tag)
    print(msg_dict)
    if isinstance(msg_dict, int):
        return get_error(msg_dict)
    msg = "-搜索到以下玩家-\n"
    for index, one_player in enumerate(msg_dict):
        msg += f"{index+1}.{one_player['userName']}({one_player['userId']})\n"

    return msg
