from typing import List, Optional, TypedDict


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
    '''VA'''
    level: int
    '''游戏等级'''
    tier: Optional[str]
    '''段位'''
    gameColor: str
    '''游戏颜色？'''
    content: Optional[str]
    '''游戏段位内容'''
    gameId: Optional[str]
    '''不知道'''

    league_point: str
    '''当前段位分数'''
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
    gameInfoList: List[GameInfo]


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
    '''掌盟账号'''
    userAppNum: str
    '''qq号'''
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


class RoleInfo(TypedDict):
    session_id: str
    '''session_id'''
    my_scene: str
    '''我的场景'''
    friend_scene: str
    '''和上面那个一样'''
    my_roleid: str
    '''角色roleid'''


class ReportInfo(TypedDict):
    name: str
    '''报告名称'''


class Tool(TypedDict):
    title: str
    '''标题'''
    icon: str
    '''图标'''
    dark_icon: str
    '''暗色图标'''
    intent: str
    '''意图'''
    reportInfo: ReportInfo
    '''报告信息'''


class CardUrl(TypedDict):
    bg_main_url: str
    '''背景图片'''
    bg_text_url: str
    '''背景文字|通常是空的'''
    bg_bottom_layer_url: str
    '''背景底图'''
    bg_good_red_url: str
    '''背景红物品'''
    bg_hero_name_url: str
    '''背景英雄名称'''
    intent: str
    '''意图'''
    intent_text: str
    '''意图文字'''
    right_arrow_url: str
    '''右箭头'''
    head_url: str
    '''头像'''
    name: str
    '''名称'''
    content: str
    '''内容'''
    hero_url: str
    '''英雄图标'''
    hero_name: str
    '''英雄名称'''
    share_or_copy_url: str
    '''分享或复制按钮'''
    qr_code_url: str
    '''二维码'''


class CardInfo(TypedDict):
    has_role: int
    '''是否有角色？'''
    role_info: RoleInfo
    tools: List[Tool]
    scene: str
    '''场景'''
    card_visible: int
    '''是否可见'''
    layer_small: str
    '''小图标'''
    layer_big: str
    '''大图标'''
    bg_header_layer_url: str
    '''背景头图'''
    card: CardUrl


class tc(TypedDict):
    title: str
    '''标题'''
    content: str
    '''内容'''


class ListInfo(TypedDict):
    list: List[tc]
    image_url: str
    '''图片'''
    title: str
    '''标题'''
    high_light: str
    '''高亮'''


class CardDetail(TypedDict):
    left_data: ListInfo
    '''左边数据
    赛季KDA  | 生涯时长
    段位图片
    段位名称
    '''
    right_data: ListInfo
    '''右边数据
    赛季胜率 | 赛季爆头率
    武器图片
    武器名称
    擅长武器名称
    '''
    hero_url: str
    hero_name: str
