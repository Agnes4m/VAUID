from typing import Dict, Optional

import aiohttp

from gsuid_core.logger import logger

MVAL_API = "https://app.mval.qq.com/go/auth/login_by_qq?source_game_zone=agame&game_zone=agame"


async def exchange_val_token(openid: str, access_token: str) -> Optional[Dict]:
    payload = {
        "clienttype": 9,
        "config_params": {"client_dev_name": "23117RK66C", "lang_type": 0},
        "login_info": {
            "appid": 102061775,
            "openid": str(openid),
            "qq_info_type": 5,
            "sig": str(access_token),
            "uin": 0,
        },
        "mappid": 10200,
        "mcode": "132f0a77d34402abc8463d60100011d19b0e",
        "source_game_zone": "agame",
        "game_zone": "agame",
    }

    headers = {
        "Cookie": "clientType=9; openid=null; access_token=null;",
        "User-Agent": (
            "mval/2.4.0.10053 Channel/10068 Manufacturer/Redmi Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36"
        ),
        "Content-Type": "application/json",
        "Host": "app.mval.qq.com",
        "Connection": "Keep-Alive",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                MVAL_API, json=payload, headers=headers
            ) as resp:
                res_json = await resp.json()
                if res_json.get("result") == 0:
                    data = res_json.get("data", {}).get("login_info", {})
                    return {
                        "userId": data.get("user_id"),
                        "tid": data.get("wt"),
                    }
                else:
                    logger.error(f"[Val] 接口返回: {res_json}")
                    return None
        except Exception as e:
            logger.error(f"[Val] 网络请求异常: {e}")
            return None
