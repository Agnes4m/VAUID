from typing import TypeVar, Optional

from sqlmodel import Field
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.webconsole.mount_app import PageSchema, GsAdminModel, site
from gsuid_core.utils.database.startup import exec_list
from gsuid_core.utils.database.base_models import Bind, User, with_session

exec_list.extend(
    [
        'ALTER TABLE VAUser ADD COLUMN platform TEXT DEFAULT ""',
        'ALTER TABLE VAUser ADD COLUMN latest_battle_id TEXT DEFAULT ""',
        "ALTER TABLE VAUser ADD COLUMN latest_battle_time INTEGER DEFAULT 0",
    ]
)

T_ValUser = TypeVar("T_ValUser", bound="ValUser")


class ValBind(Bind):
    uid: Optional[str] = Field(default=None, title="VAUID")

    model_config = {"table": True}  # type: ignore


class ValUser(User):
    uid: Optional[str] = Field(default=None, title="VAUID")
    latest_battle_id: Optional[str] = Field(default=None, title="最新战绩ID")
    latest_battle_time: Optional[int] = Field(default=0, title="最新战绩时间")

    model_config = {"table": True}  # type: ignore

    @classmethod
    @with_session
    async def get_latest_battle_id(cls, user_id: str, bot_id: str) -> Optional[str]:
        """获取用户最新战绩ID"""
        data = await cls.select_data(user_id, bot_id)
        return data.latest_battle_id if data else None

    @classmethod
    @with_session
    async def update_latest_battle(
        cls, session: AsyncSession, user_id: str, bot_id: str, battle_id: str, battle_time: int
    ) -> None:
        """更新用户最新战绩ID"""
        data = await cls.select_data(user_id, bot_id)
        if data:
            data.latest_battle_id = battle_id
            data.latest_battle_time = battle_time
            session.add(data)
            await session.commit()

    @classmethod
    @with_session
    async def insert_or_update_user(
        cls: type[T_ValUser],
        session: AsyncSession,
        bot_id: str,
        user_id: str,
        uid: str,
        cookie: str,
    ) -> T_ValUser:
        obj = await cls.base_select_data(
            bot_id=bot_id,
            user_id=user_id,
            uid=uid,
        )
        if obj:
            obj.cookie = cookie
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj
        obj = cls(
            bot_id=bot_id,
            user_id=user_id,
            cookie=cookie,
            uid=uid,
        )
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj


@site.register_admin
class VABindadmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(
        label="VA绑定管理",
        icon="fa fa-users",
    )  # type: ignore

    # 配置管理模型
    model = ValBind


@site.register_admin
class VAUseradmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(
        label="VA用户管理",
        icon="fa fa-users",
    )  # type: ignore

    # 配置管理模型
    model = ValUser
