from typing import Optional

from sqlmodel import Field
from gsuid_core.utils.database.base_models import Bind, User
from gsuid_core.webconsole.mount_app import PageSchema, GsAdminModel, site


class VALBind(Bind, table=True):
    uid: Optional[str] = Field(default=None, title='VAUID')


class VALUser(User, table=True):
    uid: Optional[str] = Field(default=None, title='VAUID')


@site.register_admin
class VABindadmin(GsAdminModel):
    pk_name = 'id'
    page_schema = PageSchema(
        label='VAL绑定管理',
        icon='fa fa-users',
    )  # type: ignore

    # 配置管理模型
    model = VALBind


@site.register_admin
class VAUseradmin(GsAdminModel):
    pk_name = 'id'
    page_schema = PageSchema(
        label='VAL用户管理',
        icon='fa fa-users',
    )  # type: ignore

    # 配置管理模型
    model = VALUser
