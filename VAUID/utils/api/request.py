import json as js
import time
from typing import Any, Dict, List, Union, Literal, Callable, Optional, cast

from httpx import AsyncClient

from gsuid_core.logger import logger
from gsuid_core.models import Event

from .api import (
    PFAPI,
    GunAPI,
    MapAPI,
    CardAPI,
    ShopAPI,
    ViveAPI,
    AssetAPI,
    OnlineAPI,
    SearchAPI,
    ValCardAPI,
    SummonerAPI,
)
from .models import (
    Shop,
    Vive,
    Battle,
    PFInfo,
    GunInfo,
    MapInfo,
    CardInfo,
    InfoBody,
    CardOnline,
    SummonerInfo,
)
from .model.asset import AssetData
from ..database.models import ValUser

SEASON_ID = "dcde7346-4085-de4f-c463-2489ed47983b"
DEFAULT_TIMEOUT = 300


class ValQueryContext:
    """实例化"""

    def __init__(self, user_id: str, bot_id: str):
        self.user_id = user_id
        self.bot_id = bot_id
        self._opuid: Optional[str] = None
        self._cookie: Optional[str] = None
        self._random_cookie: Optional[str] = None

    async def init(self):
        """初始化，获取查询者的 Cookie"""
        opuid, ck = await WeGameApi._get_cookie_by_id(self.user_id, self.bot_id)
        self._opuid = opuid
        self._cookie = ck
        return self

    @property
    def opuid(self) -> Optional[str]:
        """获取操作者 UUID"""
        return self._opuid

    @property
    def cookie(self) -> Optional[str]:
        """获取查询者 Cookie"""
        return self._cookie

    async def get_random_cookie(self) -> Optional[str]:
        """获取随机用户 Cookie（用于备用）"""
        if self._random_cookie is None:
            _, self._random_cookie = await WeGameApi.get_sence()
        return self._random_cookie


class WeGameApi:
    """WeGame API 客户端，用于获取无畏契约玩家数据"""

    ssl_verify = False
    _HEADER: Dict[str, str] = {
        "User-Agent": (
            "mval/1.4.1.10011 Channel/3"
            "Mozilla/5.0 (Linux; Android 9; V2171A Build/PQ3A.190605.10171107; wv)"
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0"
            "Chrome/91.0.4472.114 Mobile Safari/537.36"
        ),
        "Content-Type": "application/json; charset=utf-8",
    }

    @classmethod
    async def create_context(cls, ev: Event) -> ValQueryContext:
        """创建查询上下文"""
        # 确保 bot_id 是字符串
        bot_id = ev.bot_id[0] if isinstance(ev.bot_id, list) else ev.bot_id
        ctx = ValQueryContext(ev.user_id, bot_id)
        await ctx.init()
        return ctx

    @staticmethod
    async def _get_cookie(uid: str) -> List[str]:
        """通过 uid 获取用户 token"""
        cookie = await ValUser.get_user_cookie_by_uid(uid)
        if cookie is None:
            raise Exception("No valid cookie")
        return [uid, cookie] if cookie else ["", ""]

    @staticmethod
    async def _get_cookie_by_id(user_id: str, bot_id: str) -> List[str]:
        """通过 user_id 获取 token"""
        data = await ValUser.select_data(user_id, bot_id)
        if data is None:
            raise Exception("No valid uid")
        return [data.uid, data.cookie] if data.cookie else ["", ""]

    @staticmethod
    async def get_sence() -> List[str]:
        """随机获取一个用户的 uid, token, stoken"""
        user_list = await ValUser.get_all_user()
        if not user_list:
            return ["", "", ""]

        user = user_list[0]
        if user.uid is None:
            raise Exception("No valid uid")

        token = await ValUser.get_user_cookie_by_uid(user.uid)
        stoken = await ValUser.get_user_stoken_by_uid(user.uid)
        if stoken is None or token is None:
            raise Exception("No valid cookie")
        return [user.uid, token, stoken]

    async def search_player(self, key_word: str):
        """使用名称来搜索玩家，可以获取 uid"""
        data = await self._va_request(
            SearchAPI,
            params={
                "keyWord": key_word,
                "app_scope": "lol",
                "searchType": "1",
                "page": "0",
                "pageSize": "10",
            },
        )
        if isinstance(data, int):
            return data
        return cast(List[InfoBody], data["data"]["userList"])

    async def get_player_info(self, ctx: ValQueryContext, uid_list: List[str]):
        """使用 uid 来获取玩家信息，可以获取 scene

        Args:
            ctx: 查询上下文（包含查询者信息）
            uid_list: 要查询的 UID 列表
        """
        if len(uid_list) < 1 or not ctx.cookie:
            return None

        uuidSceneList = [{"uuid": uid, "scene": ""} for uid in uid_list]

        data = await self._va_request(
            SummonerAPI,
            headers={"Cookie": ctx.cookie},
            json={
                "opUuid": ctx.opuid,
                "isNeedGameInfo": 1,
                "isNeedMedal": 0,
                "isNeedCommunityInfo": 1,
                "clientType": 9,
                "isNeedDress": 1,
                "isNeedRemark": 1,
                "uuidSceneList": uuidSceneList,
            },
        )
        if isinstance(data, int):
            return data
        if data.get("msg") != "success":
            logger.error(f"获取卡片信息失败：{data}")
            return cast(str, data.get("data", ""))
        return cast(SummonerInfo, data["data"][0])

    async def get_player_card(self, uid: str):
        """获取玩家卡片信息，可以获取 scene"""
        uid, ck = await self._get_cookie(uid)
        data = await self._va_request(
            CardAPI,
            headers={"Cookie": ck},
            json={"uuid": uid, "jump_key": "mine"},
        )

        return self._parse_response(data, lambda d: cast(CardInfo, d["data"]), default_on_error="")

    async def get_detail_card(
        self,
        uid: str,
        secen: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """用 scene 获取玩家卡片信息

        Args:
            uid: 目标用户 UID（用于获取备用 cookie）
            secen: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
            get_random_cookie: 获取随机 cookie 的异步方法
        """
        json_data = {"scene": secen}

        # 优先使用提供的 cookie
        if cookie:
            data = await self._va_request(ValCardAPI, headers={"Cookie": cookie}, json=json_data)
            result = self._parse_response(
                data, lambda d: cast(List[Battle], d["data"]["battle_list"]), default_on_error=""
            )
            if not isinstance(result, int) or result >= 0:
                return result
            logger.debug(f"使用用户 cookie 请求失败，尝试使用随机 cookie: {result}")

        # 使用随机 cookie 重试
        if get_random_cookie:
            random_ck = await get_random_cookie()
        else:
            _, random_ck = await WeGameApi.get_sence()
        if not random_ck:
            return -511
        data = await self._va_request(ValCardAPI, headers={"Cookie": random_ck}, json=json_data)
        return self._parse_response(data, lambda d: cast(List[Battle], d["data"]["battle_list"]), default_on_error="")

    def _parse_response(
        self,
        data: Union[Dict, int],
        parser: Optional[Callable[[Dict], Any]] = None,
        default_on_error: Any = "",
    ) -> Union[Any, int]:
        """统一处理 API 响应"""
        if isinstance(data, int):
            return data
        if data.get("result", 0) != 0:
            return default_on_error
        return parser(data) if parser else data

    async def _va_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        need_ck: bool = True,
    ) -> Union[Dict, int]:
        """统一的 API 请求方法"""
        # 构建请求头
        req_headers = dict(self._HEADER)
        if headers:
            # 统一使用首字母大写的键
            headers = {k.capitalize() if k.lower() == "cookie" else k: v for k, v in headers.items()}
            req_headers.update(headers)

        # 自动添加 cookie
        if need_ck and "Cookie" not in req_headers and "cookie" not in req_headers:
            uid = json.get("id", "9999") if json else "9999"
            _, ck = await WeGameApi._get_cookie(uid)
            if ck:
                req_headers["Cookie"] = ck
            else:
                return -511

        # 有 json 数据时使用 POST 方法
        if json:
            method = "POST"

        async with AsyncClient(verify=self.ssl_verify) as client:
            resp = await client.request(
                method,
                url=url,
                headers=req_headers,
                params=params,
                json=json,
                timeout=DEFAULT_TIMEOUT,
            )
            try:
                raw_data = await resp.json()
            except Exception:
                _raw_data = resp.text
                try:
                    raw_data = js.loads(_raw_data)
                except Exception:
                    logger.error(f"API 响应解析失败：{_raw_data}")
                    return -999

            # 处理错误码
            if "result" in raw_data:
                result = raw_data["result"]
                if isinstance(result, dict) and result.get("error_code", 0) != 0:
                    return result["error_code"]
                if isinstance(result, int) and result != 0:
                    return result

            return raw_data

    async def _get_with_token(
        self,
        uid: str,
        scene: str,
        api_url: str,
        parser: Callable[[Dict], Any],
        extra_data: Optional[Dict[str, Any]] = None,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ) -> Union[Any, int]:
        """通用的带 token 请求方法，用于获取各种玩家数据

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            api_url: API URL
            parser: 数据解析函数
            extra_data: 额外的请求数据
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
            get_random_cookie: 获取随机 cookie 的异步方法
        """
        json_data = {"scene": scene, **(extra_data or {})}

        # 优先使用提供的 cookie
        if cookie:
            data = await self._va_request(
                api_url,
                headers={"Cookie": cookie},
                json=json_data,
            )
            result = self._parse_response(data, parser, default_on_error="")
            # logger.debug(f"使用用户 cookie 请求 {api_url} 成功: {result}")
            # 如果不是错误码，直接返回
            if not isinstance(result, int) or result >= 0:
                return result
            logger.debug(f"使用用户 cookie 请求失败，尝试使用随机 cookie: {result}")

        # 使用随机 cookie 重试
        if get_random_cookie:
            random_ck = await get_random_cookie()
        else:
            _, random_ck = await WeGameApi.get_sence()
        if not random_ck:
            return -511
        data = await self._va_request(
            api_url,
            headers={"Cookie": random_ck},
            json=json_data,
        )
        return self._parse_response(data, parser, default_on_error="")

    async def get_online(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """获取玩家在线信息

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
            get_random_cookie: 获取随机 cookie 的异步方法
        """
        json_data = {"uuid": uid, "scene": scene}

        # 优先使用提供的 cookie
        if cookie:
            data = await self._va_request(OnlineAPI, headers={"Cookie": cookie}, json=json_data)
            result = self._parse_response(data, lambda d: cast(CardOnline, d["data"]), default_on_error="")
            if not isinstance(result, int) or result >= 0:
                return result
            logger.debug(f"使用用户 cookie 请求失败，尝试使用随机 cookie: {result}")

        # 使用随机 cookie 重试
        if get_random_cookie:
            random_ck = await get_random_cookie()
        else:
            _, random_ck = await WeGameApi.get_sence()
        if not random_ck:
            return -511
        data = await self._va_request(OnlineAPI, headers={"Cookie": random_ck}, json=json_data)
        return self._parse_response(data, lambda d: cast(CardOnline, d["data"]), default_on_error="")

    async def get_gun(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """获取玩家枪械信息

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
        """
        return await self._get_with_token(
            uid,
            scene,
            GunAPI,
            lambda d: cast(List[GunInfo], d["data"]["list"]),
            {"season_id": SEASON_ID, "queue_id": "255"},
            cookie,
            get_random_cookie,
        )

    async def get_map(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """获取玩家地图信息

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
        """
        return await self._get_with_token(
            uid,
            scene,
            MapAPI,
            lambda d: cast(List[MapInfo], d["data"]["list"]),
            {"season_id": SEASON_ID, "queue_id": "255"},
            cookie,
            get_random_cookie,
        )

    async def get_vive(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """获取玩家 Vive 信息

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
        """
        return await self._get_with_token(
            uid,
            scene,
            ViveAPI,
            lambda d: cast(List[Vive], d["data"]["list"]),
            cookie=cookie,
            get_random_cookie=get_random_cookie,
        )

    async def get_pf(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """获取玩家 PF 信息

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
        """
        return await self._get_with_token(
            uid,
            scene,
            PFAPI,
            lambda d: cast(List[PFInfo], d["data"]["list"]),
            {"season_id": SEASON_ID, "queue_id": "255"},
            cookie,
            get_random_cookie,
        )

    async def get_shop(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ):
        """获取玩家商店信息

        Args:
            uid: 目标用户 UID
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
        """
        json_data = {
            "_t": int(time.time()),
            "scene": scene,
            "source_game_zone": "agame",
            "game_zone": "agame",
        }

        # 优先使用提供的 cookie
        if cookie:
            data = await self._va_request(ShopAPI, headers={"Cookie": cookie}, json=json_data)
            result = self._parse_response(data, lambda d: cast(List[Shop], d["data"]), default_on_error="")
            if not isinstance(result, int) or result >= 0:
                return result
            logger.debug(f"使用用户 cookie 请求失败，尝试使用随机 cookie: {result}")

        # 使用随机 cookie 重试
        if get_random_cookie:
            random_ck = await get_random_cookie()
        else:
            _, random_ck = await WeGameApi.get_sence()
        if not random_ck:
            return -511
        data = await self._va_request(ShopAPI, headers={"Cookie": random_ck}, json=json_data)
        return self._parse_response(data, lambda d: cast(List[Shop], d["data"]), default_on_error="")

    async def get_asset(
        self,
        scene: str,
        cookie: Optional[str] = None,
        get_random_cookie: Optional[Callable[[], Any]] = None,
    ) -> AssetData | int:
        """获取玩家资产信息（皮肤、配件等）

        Args:
            scene: 场景 ID
            cookie: 可选的 cookie，优先使用此 cookie，失败后使用随机 cookie
            get_random_cookie: 获取随机 cookie 的异步方法
        """
        json_data = {
            "scene": scene,
            "source_game_zone": "agame",
            "game_zone": "agame",
        }

        # 优先使用提供的 cookie
        if cookie:
            data = await self._va_request(AssetAPI, headers={"Cookie": cookie}, json=json_data)
            result = self._parse_response(data, lambda d: cast(AssetData, d["data"]), default_on_error="")
            if not isinstance(result, int) or result >= 0:
                return result
            logger.debug(f"使用用户 cookie 请求失败，尝试使用随机 cookie: {result}")

        # 使用随机 cookie 重试
        if get_random_cookie:
            random_ck = await get_random_cookie()
        else:
            _, random_ck = await WeGameApi.get_sence()
        if not random_ck:
            return -511
        data = await self._va_request(AssetAPI, headers={"Cookie": random_ck}, json=json_data)
        return self._parse_response(data, lambda d: cast(AssetData, d["data"]), default_on_error="")
