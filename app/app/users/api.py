import logging
from datetime import timedelta
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.core import security
from app.core.config import settings
from app.utils import APIResponse, APIResponseType, PaginatedContent
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS

from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "user"
logger = logging.getLogger(__name__)


@router.post("/login")
async def login(
    request: Request,
    db: AsyncSession = Depends(deps.get_db_async),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    
    user = await crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise exc.InternalServiceError(
            status_code=401,
            detail="Incorrect username or password",
            msg_code=utils.MessageCodes.incorrect_username_or_password,
        )
    elif not crud.user.is_active(user):
        raise exc.InternalServiceError(
            status_code=401,
            detail="Incorrect username or password",
            msg_code=utils.MessageCodes.incorrect_username_or_password,
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return schemas.Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        token_type="bearer",
    )


@router.get("/")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_users(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemas.ParamsUser = Depends(),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[PaginatedContent[list[schemas.User]]]:
    """
    Retrieve users.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    users, total_count = await crud.user.get_multi_by_filter(db, params=params)
    return APIResponse(
        PaginatedContent(
            data=users,
            total_count=total_count,
            size=params.size,
            page=params.page,
        )
    )


@router.get("/me")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.User]:
    """
    Retrieve users.
    """
    return APIResponse(current_user)


@router.post("/")
# @invalidate(namespace=namespace)
async def create_user(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.User]:
    """
    Create new user.
    user access to this [ ADMINISTRATOR ]
    """
    user = await crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise exc.ServiceFailure(
            detail="The user with this username already exists in the system.",
            msg_code=utils.MessageCodes.bad_request,
        )
    user = await crud.user.create(db, obj_in=user_in)
    return APIResponse(user)


@router.get("/{user_id}")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_user_by_id(
    user_id: int,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[schemas.User]:
    """
    Get a specific user by id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.ServiceFailure(
            detail="User not found",
            msg_code=utils.MessageCodes.not_found,
        )
    if user == current_user:
        return APIResponse(user)
    if not crud.user.is_superuser(current_user):
        raise exc.ServiceFailure(
            detail="The user doesn't have enough privileges",
            msg_code=utils.MessageCodes.bad_request,
        )
    return APIResponse(user)


@router.delete("/{user_id}")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def delete_user(
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    user_id: int,
) -> APIResponseType[schemas.User]:
    """
    Get a specific user by id.
    user access to this [ ADMINISTRATOR ]
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.ServiceFailure(
            detail="User not found",
            msg_code=utils.MessageCodes.not_found,
        )
    del_user = await crud.user.remove(db, id=user_id, commit=True)
    return APIResponse(del_user)


@router.put("/{user_id}")
async def update_user(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.User]:
    """
    Update a user.
    user access to this [ ADMINISTRATOR ]
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.ServiceFailure(
            detail="The user with this username does not exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    user = await crud.user.update(db, db_obj=user, obj_in=user_in)
    return APIResponse(user)


@router.post("/introspection")
async def introspection(
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    token: str,
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[schemas.User]:
    """
    Introspect the given token and return user information
    """
    user = await deps.get_current_user(db, token)
    user = await deps.get_current_active_user(current_user=user)
    return APIResponse(user)
