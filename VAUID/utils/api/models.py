from typing import List, Optional, TypedDict


class ResultInfo(TypedDict):
    error_code: int
    error_message: str


class GameInfo(TypedDict):
    uuid: str
    '''用户的id'''
    scene: str
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
    appNum: str
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


class TitleContent(TypedDict):
    title: str
    '''标题'''
    content: str
    '''内容'''


class LeftData(TypedDict):
    list: List[TitleContent]
    image_url: str
    '''段位图片'''
    title: str
    '''段位名称'''


class RightData(TypedDict):
    list: List[TitleContent]
    image_url: str
    '''武器图片'''
    title: str
    '''删除武器内容'''
    high_light: str
    '''高亮武器'''


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
    '''分享或复制按钮url'''
    qr_code_url: str
    '''二维码'''
    left_data: Optional[LeftData]
    middle_data: Optional[TitleContent]
    '''KAST'''
    right_data: Optional[RightData]
    round_win_rate: Optional[TitleContent]
    '''回合胜率'''
    card_switch_tips: str
    '''无'''
    is_vip: int
    '''0'''
    tab: dict
    '''按钮相关参数'''


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


class CardOnline(TypedDict):
    '''在线数据'''

    online_state: int
    '''是否在线'''
    online_text: str
    '''在线文字'''
    online_color: str
    '''在线颜色'''


class GunInfo(TypedDict):
    '''武器数据'''

    id: str
    '''武器id'''
    name: str
    '''武器名称'''
    image_url: str
    '''武器图片'''
    kill: str
    '''击杀数'''
    kill_head: str
    '''爆头率'''
    kill_round: str
    '''回合击杀'''
    kill_farthest: str
    '''最远击杀距离(无单位)'''


class MapInfo(TypedDict):
    '''地图信息'''

    agent_id: str
    '''地图id'''
    map_id: str
    '''地图id路径'''
    name: str
    '''地图名称'''
    map_icon: str
    '''地图图标'''
    win_rate: str
    '''胜率(100.0)'''
    best_hero_win_rate: str
    '''最佳英雄胜率(100.0)'''
    best_hero_url: str
    '''最佳英雄图标'''
    kd: str
    '''kd'''
    round_score: str
    '''回合评分'''
    map_mask_color: str
    '''地图遮罩颜色
    linear-gradient(67.11deg,
            #21414B 10.25%,
            rgba(65,
            81,
            85,
            0) 81.97%)"
    '''


class ScoreLevel(TypedDict):
    '''评分数据'''

    id: int
    '''评分id, 0'''
    level: str
    '''评分评价, B'''
    title: str
    '''评分名称'''
    guide: str
    '''评分说明'''
    high_light: str
    '''高亮评分 | 无'''
    intent: str
    icon: str
    '''评分小图标'''
    head_icon_win: str
    '''胜利头像评分小图标'''
    head_icon_fail: str
    '''失败头像评分小图标'''
    head_icon_draw: str
    '''平局头像评分小图标'''
    white_icon: str
    '''白色小图标'''


class UsedMap(TypedDict):
    '''地图信息'''

    id: int
    '''地图id, 0'''
    name: str
    '''地图名称'''
    e_name: str
    '''地图英文名称'''
    icon: str
    '''地图图标'''


class Competitve(TypedDict):
    '''排位信息'''

    competitive_tier_change_icon: str
    '''排位变化图标'''
    competitive_tier_icon: str
    '''排位图标'''
    competitive_point_change: str
    '''排位变化'''
    competitive_tier_color: str
    '''排位颜色 #24B7AF'''
    competitive_tier_change: int


class Achievement(TypedDict):
    '''成就信息'''

    id: str
    '''成就id'''
    icon: str
    '''成就图标130* 40'''
    width: int
    '''成就图标宽度'''
    height: int
    '''成就图标高度'''
    desc: str
    '''成就描述'''
    aclos_icon: str
    '''旧版本成就图标'''
    aclos_desc: str
    '''旧版本成就描述'''


class Battle(TypedDict):
    '''战斗数据'''

    battle_id: str
    '''战斗id'''
    match_id: str
    '''匹配id'''
    image_url: str
    '''使用角色url'''
    result_title: str
    '''胜利  |  平局  |  失败'''
    result_color: str
    '''颜色 #24B7AF'''
    hero_name: str
    '''使用英雄名称'''
    content: str
    '''普通模式 | 深寒东港'''
    kda: str
    '''kda'''
    score: str
    '''回合评分'''
    score_color: str
    '''回合评分颜色'''
    time: str
    '''时间'''
    ts: int
    '''持续时间戳'''
    intent: str
    '''游戏内跳转链接'''
    role_id: str
    '''角色id'''
    kda_score: str
    '''kda分数'''
    score_avg: str
    '''平均分数'''
    kill_death: str
    '''空值'''
    game_mode: str
    '''游戏模式(普通、排位)'''
    game_mode_icon: str
    '''游戏模式图标'''
    used_map: UsedMap
    round_fail: int
    '''回合失败次数'''
    round_won: int
    '''回合胜利次数'''
    game_enum: str
    '''游戏模式 | unrated'''
    rank: int
    '''段位'''
    score_level: ScoreLevel
    '''评分数据'''
    is_friend: int
    '''是否好友'''
    competitive_tier: Competitve
    '''排位信息'''
    achievement: List[Achievement]
    '''成就信息'''


class ValBattle(TypedDict):
    '''战斗数据'''

    next_baton: str
    '''下一把武器uid'''
    battle_list: List[Battle]
    msg: str
    '''两个月内的记录'''
