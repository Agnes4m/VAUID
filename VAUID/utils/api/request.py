import json as js
import time
from typing import Any, Dict, List, Union, Literal, Callable, Optional, cast
from dataclasses import field, dataclass

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


@dataclass
class ApiRequest:
    url: str
    method: Literal["GET", "POST"] = "GET"
    params: Optional[Dict[str, Any]] = None
    json: Optional[Dict[str, Any]] = None
    need_cookie: bool = True


@dataclass
class QueryContext:
    user_id: str
    bot_id: str
    cookie: Optional[str] = None
    opuid: Optional[str] = None
    _random_cookie: Optional[str] = field(default=None, repr=False)

    async def init(self):
        opuid, ck = await WeGameApi._get_cookie_by_id(self.user_id, self.bot_id)
        self.opuid = opuid
        self.cookie = ck
        return self

    async def get_random_cookie(self) -> Optional[str]:
        if self._random_cookie is None:
            _, self._random_cookie = await WeGameApi.get_sence()
        return self._random_cookie


class WeGameApi:
    ssl_verify: bool = False
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
    async def create_context(cls, ev: Event) -> QueryContext:
        bot_id = ev.bot_id[0] if isinstance(ev.bot_id, list) else ev.bot_id
        ctx = QueryContext(ev.user_id, bot_id)
        _ = await ctx.init()
        return ctx

    @staticmethod
    async def _get_cookie(uid: str) -> List[str]:
        cookie = await ValUser.get_user_cookie_by_uid(uid)
        if cookie is None:
            raise Exception("No valid cookie")
        return [uid, cookie] if cookie else ["", ""]

    @staticmethod
    async def _get_cookie_by_id(user_id: str, bot_id: str) -> List[str]:
        data = await ValUser.select_data(user_id, bot_id)
        if data is None:
            raise Exception("No valid uid")
        return [data.uid or "", data.cookie] if data.cookie else ["", ""]

    @staticmethod
    async def get_sence() -> List[str]:
        user_list = await ValUser.get_all_user()
        if not user_list:
            return ["", ""]

        user = cast(ValUser, user_list[0])
        if user.uid is None:
            raise Exception("No valid uid")

        cookie = await ValUser.get_user_cookie_by_uid(user.uid)
        if cookie is None:
            raise Exception("No valid cookie")
        return [user.uid, cookie]

    async def _va_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict, int]:
        req_headers = dict(self._HEADER)
        if headers:
            headers = {
                k.capitalize() if k.lower() == "cookie" else k: v
                for k, v in headers.items()
            }
            req_headers.update(headers)

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

            if "result" in raw_data:
                result = raw_data["result"]
                if isinstance(result, dict) and result.get("error_code", 0) != 0:
                    return result["error_code"]
                if isinstance(result, int) and result != 0:
                    return result

            return raw_data

    def _parse_response(
        self,
        data: Union[Dict, int],
        parser: Optional[Callable[[Dict], Any]] = None,
        default_on_error: Any = "",
    ) -> Union[Any, int]:
        if isinstance(data, int):
            return data
        if data.get("result", 0) != 0:
            return default_on_error
        return parser(data) if parser else data

    async def _request_with_fallback(
        self,
        request: ApiRequest,
        parser: Callable[[Dict], Any],
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[Any, int]:
        if cookie:
            data = await self._va_request(
                request.url,
                request.method,
                {"Cookie": cookie},
                request.params,
                request.json,
            )
            result = self._parse_response(data, parser, default_on_error="")
            if not isinstance(result, int) or result >= 0:
                return result

        if not random_cookie:
            _, random_cookie = await self.get_sence()
        if not random_cookie:
            return -511

        data = await self._va_request(
            request.url,
            request.method,
            {"Cookie": random_cookie},
            request.params,
            request.json,
        )
        return self._parse_response(data, parser, default_on_error="")

    async def search_player(self, key_word: str) -> Union[List[InfoBody], int]:
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

    async def get_player_info(
        self, ctx: QueryContext, uid_list: List[str]
    ) -> Union[SummonerInfo, int, str, None]:
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

    async def get_player_card(self, uid: str) -> Union[CardInfo, int, str]:
        uid, ck = await self._get_cookie(uid)
        data = await self._va_request(
            CardAPI, headers={"Cookie": ck}, json={"uuid": uid, "jump_key": "mine"}
        )
        return self._parse_response(
            data, lambda d: cast(CardInfo, d["data"]), default_on_error=""
        )

    async def get_detail_card(
        self,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[List[Battle], int]:
        request = ApiRequest(url=ValCardAPI, json={"scene": scene})
        return await self._request_with_fallback(
            request,
            lambda d: cast(List[Battle], d["data"]["battle_list"]),
            cookie,
            random_cookie,
        )

    async def get_online(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[CardOnline, int]:
        request = ApiRequest(url=OnlineAPI, json={"uuid": uid, "scene": scene})
        return await self._request_with_fallback(
            request,
            lambda d: cast(CardOnline, d["data"]),
            cookie,
            random_cookie,
        )

    async def get_gun(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[List[GunInfo], int]:
        request = ApiRequest(
            url=GunAPI,
            json={"scene": scene, "season_id": SEASON_ID, "queue_id": "255"},
        )
        return await self._request_with_fallback(
            request,
            lambda d: cast(List[GunInfo], d["data"]["list"]),
            cookie,
            random_cookie,
        )

    async def get_map(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[List[MapInfo], int]:
        request = ApiRequest(
            url=MapAPI,
            json={"scene": scene, "season_id": SEASON_ID, "queue_id": "255"},
        )
        return await self._request_with_fallback(
            request,
            lambda d: cast(List[MapInfo], d["data"]["list"]),
            cookie,
            random_cookie,
        )

    async def get_vive(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[List[Vive], int]:
        request = ApiRequest(url=ViveAPI, json={"scene": scene})
        return await self._request_with_fallback(
            request,
            lambda d: cast(List[Vive], d["data"]["list"]),
            cookie,
            random_cookie,
        )

    async def get_pf(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[List[PFInfo], int]:
        request = ApiRequest(
            url=PFAPI,
            json={"scene": scene, "season_id": SEASON_ID, "queue_id": "255"},
        )
        return await self._request_with_fallback(
            request,
            lambda d: cast(List[PFInfo], d["data"]["list"]),
            cookie,
            random_cookie,
        )

    async def get_shop(
        self,
        uid: str,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[List[Shop], int]:
        request = ApiRequest(
            url=ShopAPI,
            json={
                "_t": int(time.time()),
                "scene": scene,
                "source_game_zone": "agame",
                "game_zone": "agame",
            },
        )
        return await self._request_with_fallback(
            request,
            lambda d: cast(List[Shop], d["data"]),
            cookie,
            random_cookie,
        )

    async def get_asset(
        self,
        scene: str,
        cookie: Optional[str] = None,
        random_cookie: Optional[str] = None,
    ) -> Union[AssetData, int]:
        request = ApiRequest(
            url=AssetAPI,
            json={
                "scene": scene,
                "source_game_zone": "agame",
                "game_zone": "agame",
            },
        )
        return await self._request_with_fallback(
            request,
            lambda d: cast(AssetData, d["data"]),
            cookie,
            random_cookie,
        )
