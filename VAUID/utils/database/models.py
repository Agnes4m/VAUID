from typing import Optional

from sqlmodel import Field
from gsuid_core.utils.database.base_models import Bind, User
from gsuid_core.webconsole.mount_app import PageSchema, GsAdminModel, site


class VABind(Bind, table=True):
    uid: Optional[str] = Field(default=None, title='VAUID')


class VAUser(User, table=True):
    uid: Optional[str] = Field(default=None, title='VAUID')


@site.register_admin
class VABindadmin(GsAdminModel):
    pk_name = 'id'
    page_schema = PageSchema(
        label='VA绑定管理',
        icon='fa fa-users',
    )  # type: ignore

    # 配置管理模型
    model = VABind


@site.register_admin
class VAUseradmin(GsAdminModel):
    pk_name = 'id'
    page_schema = PageSchema(
        label='VA用户管理',
        icon='fa fa-users',
    )  # type: ignore

    # 配置管理模型
    model = VAUser
