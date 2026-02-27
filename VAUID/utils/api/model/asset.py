from typing import Any, List, Optional, TypedDict


# --- 资金相关 (Money) ---
class MoneyItem(TypedDict):
    icon: str
    title: str
    value: str


class MoneyData(TypedDict):
    title: str
    total_num: str
    access_num: str
    more: str
    intent: str
    show_new_icon: bool
    list: List[MoneyItem]


# --- 英雄相关 (Agent) ---
class AgentItem(TypedDict):
    id: int
    guid: str
    name: str
    avatar: str
    icon: str
    bg_color_start: str
    bg_color_end: str
    type_url: str
    access_time: str
    unlock_time: str
    lock_status: int
    intent: str
    record_stones: Optional[Any]
    is_record_stones_agent: bool
    icon_grey: str


class AgentData(TypedDict):
    title: str
    total_num: str
    access_num: str
    more: str
    intent: str
    show_new_icon: bool
    list: List[AgentItem]


# --- 皮肤图鉴相关 (Skin) ---
class SkinItem(TypedDict):
    id: str
    icon: str
    access_time: str
    unlock_time: str
    name: str
    e_name: str
    quality: int
    intent: str
    lock_status: int
    accessed_points: int
    total_points: int
    battle_pass_status: int
    limited_status: int
    use_count: int
    like_num: str
    like_num_desc: str
    like_status: int


class SkinData(TypedDict):
    title: str
    total_num: str
    access_num: str
    more: str
    intent: str
    show_new_icon: bool
    list: List[SkinItem]


# --- 收藏品相关 (Spray, Card, Charm) ---
class CollectionItem(TypedDict):
    name: str
    icon: str
    unlock_time: str
    lock_status: int
    guid: str


class CollectionData(TypedDict):
    title: str
    total_num: str
    access_num: str
    more: str
    intent: str
    show_new_icon: bool
    list: List[CollectionItem]


# --- 枪卡相关 (Skin Card) ---
class ResourceConf(TypedDict):
    name: str
    resource: str
    resource_imgname_list: str  # JSON 字符串形式
    resource_type: str
    preview_url: str


class EvolutionConf(TypedDict):
    process: str
    desc: str
    required_task_num: str
    resource_imgname: str
    resource_conf: Optional[ResourceConf]
    index: Optional[int]


class UpgradeConf(TypedDict):
    icon: str
    unlock_icon: str
    task_id: str
    index: Optional[int]


class SkinCardItem(TypedDict):
    skin_card_id: str
    quality: str
    bg_img: str
    list_img: str
    skin_limit: int
    skin_list_str: List[str]
    name: str
    desc: str
    sub_desc: str
    main_tag: str
    signer: str
    is_exchange: int
    is_unique: int
    limit_num: int
    resource_link: str
    resource_type: str
    resource_img_name_list: List[Any]
    resource_imgname_list: str
    status: int
    acquire_time: int
    is_upgrade: int
    upgrade_type: str
    upgrade_conf: str
    evolution_conf: str
    base_resource: str
    upgrade_conf_list: List[UpgradeConf]
    evolution_conf_list: List[EvolutionConf]
    base_resource_conf: ResourceConf
    is_lock: bool
    is_wear: bool
    unique_num: str


class SkinCardData(TypedDict):
    title: str
    total_num: str
    access_num: str
    more: str
    intent: str
    show_new_icon: bool
    list: List[SkinCardItem]


# --- 简单模块 (Skin Assemble, Stone Overview) ---
class SimpleSection(TypedDict):
    title: str
    total_num: str
    access_num: str
    more: str
    intent: str
    show_new_icon: bool


# --- 数据主体 (Data Body) ---
class AssetData(TypedDict):
    money: MoneyData
    agent: AgentData
    skin: SkinData
    spray: CollectionData
    card: CollectionData
    charm: CollectionData
    skin_card: SkinCardData
    skin_assemble: SimpleSection
    stone_overview: SimpleSection
    is_master: int
    use_all: bool
