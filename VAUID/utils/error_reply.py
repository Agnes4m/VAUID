from typing import Union

TEXT_HINT = "[va] 请输入正确的参数"
UID_HINT = "[va] 你还没有绑定UID，请先使用[va绑定]命令进行绑定"
CK_HINT = "[va] 你还没有添加可用CK，请先使用[va添加ck]命令进行绑定"
UNLOGIN_HINT = "[va] 你还没有登录，请先使用[va登录]命令进行登录"
FR_HINT = "[va] 未添加Bot为好友，无法查询战绩信息"
OUTLOGIN_HINT: str = "[va] 登录信息已过期，请重新登录"

error_dict = {
    -51: UID_HINT,
    -511: CK_HINT,
    100: FR_HINT,
    1001: UNLOGIN_HINT,
    1003: OUTLOGIN_HINT,
}


def get_error(retcode: Union[int, str]) -> str:
    return error_dict.get(
        int(retcode),
        f"未知错误, 错误码为{retcode}, 可能由于未开启Wegame召唤师搜索!",
    )
