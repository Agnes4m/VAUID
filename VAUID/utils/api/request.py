import json as js
import urllib.parse
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union, cast

import aiofiles
from aiohttp import FormData
from gsuid_core.logger import logger
from gsuid_core.utils.download_resource.download_file import download
from httpx import AsyncClient
from PIL import Image

from ..database.models import VAUser
from .api import (
    SearchAPI,
    SummonerAPI,
)
from .models import PlayerInfo, SummonerInfo


class WeGameApi:
    ssl_verify = False
    _HEADER: Dict[str, str] = {
        'User-Agent': 'mval/1.4.1.10011 Channel/3'
        'Mozilla/5.0 (Linux; Android 9; V2171A Build/PQ3A.190605.10171107; wv)'
        'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0'
        'Chrome/91.0.4472.114 Mobile Safari/537.36',
        'Content-Type': 'application/json; charset=utf-8',
    }
   
    async def search_player(
        self,
        key_word: str,
    ):
        """使用名称来搜索玩家"""
        data = await self._va_request(
            SearchAPI,
            params={'keyWord': key_word, 'app_scope': 'lol'},
        )
        if isinstance(data, int):
            return data
        return cast(List[PlayerInfo], data['data']['searchInfo'])

    async def get_player_info(self, uid: str):
        """使用uid来获取玩家信息"""
        data = await self._va_request(
            SummonerAPI,
            json={
                'opUuid': uid,
                'isNeedGameInfo': 1,
                'isNeedMedal': 0,
                'isNeedCommunityInfo': '0',
                'clientType': 9,
                'isNeedDress': 1,
                'isNeedRemark': 1,
                'uuidSceneList': [
                    {
                        'uuid': uid,
                    }
                ]
            },
        )
        if isinstance(data, int):
            return data
        if data["msg"] != 'success':
            return cast(str, data['data'])
        return cast(List[SummonerInfo], data['data'])


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
            logger.debug(raw_data)
            if (
                'result' in raw_data
                and 'error_code' in raw_data['result']
                and raw_data['result']['error_code'] != 0
            ):
                return raw_data['result']['error_code']
            return raw_data
