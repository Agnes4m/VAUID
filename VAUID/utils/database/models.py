from typing import TypeVar, Optional

from sqlmodel import Field
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.webconsole.mount_app import PageSchema, GsAdminModel, site
from gsuid_core.utils.database.startup import exec_list
from gsuid_core.utils.database.base_models import (
    Bind,
    User,
    with_session,
)

exec_list.extend(['ALTER TABLE VAUser ADD COLUMN platform TEXT DEFAULT ""'])

T_ValUser = TypeVar("T_ValUser", bound="ValUser")


class ValBind(Bind):
    uid: Optional[str] = Field(default=None, title="VAUID")

    class Config:
        table = True


class ValUser(User):
    uid: Optional[str] = Field(default=None, title="VAUID")

    class Config:
        table = True

    @classmethod
    @with_session
    async def insert_or_update_user(
        cls: type[T_ValUser],
        session: AsyncSession,
        bot_id: str,
        user_id: str,
        uid: str,
        cookie: str,
        # platform: str = "Windows",
    ) -> T_ValUser:
        obj = await cls.base_select_data(
            bot_id=bot_id,
            user_id=user_id,
            uid=uid,
        )
        if obj:
            obj.cookie = cookie
            # obj.platform = platform
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj
        obj = cls(
            bot_id=bot_id,
            user_id=user_id,
            cookie="",
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
