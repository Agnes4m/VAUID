from typing import Dict, List, Literal, TypedDict, Union


class ResultInfo(TypedDict):
    error_code: int
    error_message: str


class GameInfo(TypedDict):
    uuid: str
    '''用户的id'''
    sence: str
    '''用户的sc'''
    gameHeadUrl: str
    '''用户头像'''
    areaName: str
    '''服务器地区'''
    roleName: str
    '''游戏名称# 114514'''
    gameShortName: str
    '''VAL'''
    level: int
    '''游戏等级'''
    gameColor: str
    '''游戏颜色？'''
    league_point: str
    '''大概是账户里现有氪金货币'''
    role_identity: str
    '''role_id用途未知'''


class SummonerInfo(TypedDict):
    uuid: str
    '''用户的ID'''
    nickName: str
    '''用户的名称'''
    headUrl: str
    '''用户头像url'''
    backgroundImgUrl: str
    '''背景图url'''
    appNum: int
    '''qq号'''
    gameinfolist: List[GameInfo]

class FeedBase(TypedDict):
    layoutType: str


class Tag_point(TypedDict):
    name: str
    '''段位名'''
    bgColor: str
    '''背景颜色#'''
    textColor: str
    '''文字颜色#'''


class InfoBody(TypedDict):
    userId: str
    userName: str
    userIcon: str
    userGender: str
    '''是否未被封号'''
    userDesc: str
    '''qq昵称'''
    userAppNum: str
    '''掌瓦自定义id'''
    showIndex: int
    '''是否展示信息'''
    focus: bool
    '''默认不是不知道是啥'''
    isVip: bool
    '''默认false'''
    tag: List[Tag_point]
    isOnline: bool
    '''是否在线'''


class InfoBodyList(TypedDict):
    userList: List[InfoBody]


class FeedNews(TypedDict):
    header: dict
    '''判断是否是好友，没用'''
    body: InfoBodyList

class PlayerInfo(TypedDict):
    feedBase: FeedBase
    feedNews: FeedNews