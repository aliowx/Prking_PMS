from typing import Annotated

from fastapi import Depends

from app.core import exceptions as exc
from app.acl.role import UserRoles
from app.api import deps
from app.users.models import User
from app.utils.message_codes import MessageCodes



class RoleChecker:
    def __init__(self, allowed_roles: list[UserRoles]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, user: Annotated[User, Depends(deps.get_current_active_user)]
    ):
        if user.role in self.allowed_roles:
            return True
        else:
            raise exc.ServiceFailure(
                detail="You do not have permission to perform this operation",
                msg_code=MessageCodes.not_permission,
            )
