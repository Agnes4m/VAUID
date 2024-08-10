from ..utils.va_api import va_api


async def draw_va_battle_list_img(uid: str):
    msg_dict = await va_api.get_player_card(uid)
    print(msg_dict)
