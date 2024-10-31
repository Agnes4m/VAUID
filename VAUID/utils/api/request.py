import random
import json as js
from copy import deepcopy
from typing import Any, Dict, List, Union, Literal, Optional, cast

from aiohttp import FormData

# from gsuid_core.utils.download_resource.download_file import download
from httpx import AsyncClient
from gsuid_core.logger import logger

from ..database.models import VAUser
from .api import (
    GunAPI,
    MapAPI,
    CardAPI,
    OnlineAPI,
    SearchAPI,
    ValCardAPI,
    SummonerAPI,
)
from .models import (
    GunInfo,
    MapInfo,
    CardInfo,
    InfoBody,
    CardDetail,
    CardOnline,
    SummonerInfo,
)

season_id = "dcde7346-4085-de4f-c463-2489ed47983b"


class WeGameApi:
    ssl_verify = False
    _HEADER: Dict[str, str] = {
        'User-Agent': 'mval/1.4.1.10011 Channel/3'
        'Mozilla/5.0 (Linux; Android 9; V2171A Build/PQ3A.190605.10171107; wv)'
        'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0'
        'Chrome/91.0.4472.114 Mobile Safari/537.36',
        'Content-Type': 'application/json; charset=utf-8',
    }

    async def get_token(self) -> List[str]:
        user_list = await VAUser.get_all_user()
        if user_list:
            user: VAUser = random.choice(user_list)
            if user.uid is None:
                raise Exception('No valid uid')
            token = await VAUser.get_user_cookie_by_uid(user.uid)
            if token is None:
                raise Exception('No valid cookie')
            return [user.uid, token]
        return ["", ""]

    async def search_player(
        self,
        key_word: str,
    ):
        """使用名称来搜索玩家
        可以获取uid"""
        data_1 = await self._va_request(
            SearchAPI,
            params={
                'keyWord': key_word,
                'app_scope': 'lol',
                "searchType": "1",
                "page": "0",
                "pageSize": "10",
            },
        )

        if isinstance(data_1, int):
            return data_1
        return cast(List[InfoBody], data_1['data']['userList'])

    async def get_player_info(self, uid: str):
        """使用uid来获取玩家信息,可以获取secen"""
        opuid, ck = await self.get_token()
        header = self._HEADER
        header['cookie'] = ck
        data = await self._va_request(
            SummonerAPI,
            header=header,
            json={
                'opUuid': opuid,
                'isNeedGameInfo': 1,
                'isNeedMedal': 0,
                'isNeedCommunityInfo': 1,
                'clientType': 9,
                'isNeedDress': 1,
                'isNeedRemark': 1,
                'uuidSceneList': [
                    {
                        'uuid': uid,
                        'scene': "",
                    }
                ],
            },
        )
        if isinstance(data, int):
            return data
        if data["msg"] != 'success':
            logger.error(f"获取卡片信息失败：{data}")
            return cast(str, data['data'])
        return cast(SummonerInfo, data['data'][0])

    async def get_player_card(self, uid: str):
        """获取玩家卡片信息
        不过大多是图片的url
        可以获取secen
        """
        data = await self._va_request(
            CardAPI,
            json={
                'uuid': uid,
                'jump_key': 'mine',
            },
        )
        logger.info(data)
        if isinstance(data, int):
            return data
        if data["result"] != 0:
            return cast(str, data['data'])
        return cast(CardInfo, data['data'])

    async def get_detail_card(self, secen: str):
        """用secen获取玩家卡片信息"""
        data = await self._va_request(
            ValCardAPI,
            json={'scene': secen},
        )
        if isinstance(data, int):
            return data
        if data["result"] != 0:
            return cast(str, data['data'])
        return cast(CardDetail, data['data'])

    async def _va_request(
        self,
        url: str,
        method: Literal['GET', 'POST'] = 'GET',
        header: Dict[str, str] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[FormData] = None,
        need_ck: bool = True,
    ) -> Union[Dict, int]:
        header = deepcopy(self._HEADER)

        if need_ck and 'cookie' not in header:
            if json and 'id' in json:
                uid = json['id']
            else:
                uid = ' 9999'
            ck = await VAUser.get_random_cookie(uid)
            if ck:
                header['Cookie'] = ck
            else:
                return -511

        if json:
            method = 'POST'

        async with AsyncClient(verify=self.ssl_verify) as client:
            resp = await client.request(
                method,
                url=url,
                headers=header,
                params=params,
                json=json,
                timeout=300,
            )
            try:
                raw_data = await resp.json()
            except:  # noqa: E722
                _raw_data = resp.text
                try:
                    raw_data = js.loads(_raw_data)
                except:  # noqa: E722
                    raw_data = {
                        'result': {'error_code': -999, 'data': _raw_data}
                    }
            # print(raw_data)
            try:
                if (
                    'result' in raw_data
                    and 'error_code' in raw_data['result']
                    and raw_data['result']['error_code'] != 0
                ):
                    return raw_data['result']['error_code']

            except TypeError:
                pass
            if raw_data['result'] != 0:
                return raw_data['result']
            return raw_data

    async def get_online(self, uid: str, scene: str):

        _, ck = await self.get_token()
        header = self._HEADER
        header['cookie'] = ck
        data = await self._va_request(
            OnlineAPI,
            header=header,
            json={
                'uuid': uid,
                'scene': scene,
            },
        )
        logger.info(data)
        if isinstance(data, int):
            return data
        return cast(CardOnline, data['data'])

    async def get_gun(self, scene: str, seeson_id: str):
        _, ck = await self.get_token()
        header = self._HEADER
        header['cookie'] = ck
        data = await self._va_request(
            GunAPI,
            header=header,
            json={
                'scene': scene,
                'season_id': season_id,
                'queue_id': "255",
            },
        )
        if isinstance(data, int):
            return data
        return cast(List[GunInfo], data['data']['list'])

    async def get_map(self, scene: str, seeson_id: str):
        _, ck = await self.get_token()
        header = self._HEADER
        header['cookie'] = ck
        data = await self._va_request(
            MapAPI,
            header=header,
            json={
                'scene': scene,
                'season_id': season_id,
                'queue_id': "255",
            },
        )
        if isinstance(data, int):
            return data
        return cast(List[MapInfo], data['data']['list'])
