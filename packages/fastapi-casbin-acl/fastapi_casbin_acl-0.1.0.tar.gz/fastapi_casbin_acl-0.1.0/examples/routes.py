"""
API 路由定义
"""

from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import select as sqlmodel_select

from fastapi_casbin_acl.dependency import permission_required
from fastapi_casbin_acl.exceptions import Unauthorized, Forbidden
from examples.database import get_session, AsyncSessionLocal
from examples.models import (
    User,
    UserCreate,
    UserResponse,
    Order,
    OrderCreate,
    OrderUpdate,
    OrderResponse,
)

router = APIRouter()


# ==================== 认证相关 ====================


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User | None:
    """
    从请求头获取当前用户
    在实际应用中，这里应该从 JWT token 或其他认证机制中获取

    注意：请求头 x-user-id 现在应该传递用户 ID（整数），而不是 username
    """
    user_id_str = request.headers.get("x-user-id")
    if not user_id_str:
        # 如果没有提供用户 ID，返回 None 会导致 Unauthorized
        return None

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format: '{user_id_str}'. Expected integer.",
        )

    statement = sqlmodel_select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    return user


# ==================== 用户获取器 ====================


async def get_subject_from_user(
    user: User | None = Depends(get_current_user),
) -> str | None:
    """
    根据用户对象获取用户 ID（用于权限检查）
    返回用户 ID 的字符串形式，用于 Casbin 权限检查
    """
    if user is None:
        return None
    return str(user.id)


# ==================== 组合依赖：认证 + 鉴权 ====================


def require_permission(action: str, resource=None, owner_getter=None):
    """
    创建一个组合依赖，同时完成认证和权限检查，并返回 User 对象

    使用示例:
        # RBAC: 不需要资源
        current_user: User = Depends(require_permission("read"))

        # ABAC: 使用模型的 get_owner_sub 方法（如果资源对象实现了该方法）
        current_user: User = Depends(require_permission("write", resource=get_order_resource))

        # ABAC: 使用自定义 owner_getter（推荐，更灵活）
        current_user: User = Depends(
            require_permission("write", resource=get_order_resource, owner_getter=get_order_owner)
        )

    :param action: 操作类型 (read, write, delete 等)
    :param resource: 可选的资源获取器，用于 ABAC
    :param owner_getter: 可选的 owner 提取器，用于从资源对象中提取 owner
                        如果不提供，将尝试使用资源对象的 get_owner_sub() 方法
    """

    def _dependency(
        user: User = Depends(get_current_user),
        _: None = Depends(
            permission_required(
                get_subject=get_subject_from_user,
                resource=resource,
                action=action,
                owner_getter=owner_getter,
                model="abac",  # 使用 ABAC 模型
            )
        ),
    ) -> User:
        """
        返回认证后的用户对象
        如果权限检查失败，会抛出 Forbidden 异常
        """
        return user

    return _dependency


# ==================== 资源获取器 (用于 ABAC) ====================


async def get_order_resource(request: Request) -> Order | None:
    """
    根据路径参数获取订单资源
    用于 ABAC 权限检查（检查订单所有者）
    """
    order_id = request.path_params.get("id")
    if not order_id:
        return None

    # 创建数据库会话
    async with AsyncSessionLocal() as session:
        # 查询订单，同时加载关联的用户信息
        statement = (
            sqlmodel_select(Order, User)
            .join(User, Order.owner_id == User.id)
            .where(Order.id == int(order_id))
        )
        result = await session.execute(statement)
        row = result.first()

        if not row:
            return None

        order, user = row
        # 将用户信息附加到订单对象，供 owner_getter 使用
        order._owner_user = user  # type: ignore
        return order


def get_order_owner(order: Order, request: Request | None = None) -> str | None:
    """
    从订单对象中提取所有者用户 ID
    这是一个灵活的 owner_getter，优先使用模型上的 get_owner_sub 方法

    注意：必须返回用户 ID（字符串），与 get_subject_from_user 返回的格式保持一致
    这样才能在 ABAC 权限检查时正确匹配 subject 和 owner

    使用示例:
        require_permission("read", resource=get_order_resource, owner_getter=get_order_owner)
    """
    # 优先使用模型上的 get_owner_sub 方法
    if hasattr(order, "get_owner_sub"):
        owner = order.get_owner_sub()
        if owner is not None:
            return owner

    # 如果模型方法返回 None，直接使用 owner_id
    if order.owner_id is not None:
        return str(order.owner_id)

    # 如果都没有，返回 None（将使用 RBAC 检查）
    return None


# ==================== 用户路由 ====================


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("read")),
):
    """
    列出所有用户（需要 read 权限）
    """
    statement = sqlmodel_select(User)
    result = await session.execute(statement)
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("read")),
):
    """
    获取单个用户信息（需要 read 权限）
    """
    statement = sqlmodel_select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("write")),
):
    """
    创建新用户（需要 write 权限）
    """
    # 检查用户名是否已存在
    statement = sqlmodel_select(User).where(User.username == user_data.username)
    result = await session.execute(statement)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    # 创建新用户
    user = User(**user_data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


# ==================== 订单路由 ====================


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("read")),
):
    """
    列出所有订单（需要 read 权限）
    注意：这里没有使用 ABAC，所以所有有 read 权限的用户都能看到所有订单
    在实际应用中，你可能需要添加过滤逻辑
    """
    statement = sqlmodel_select(Order)
    result = await session.execute(statement)
    orders = result.scalars().all()
    return orders


@router.get("/orders/{id}", response_model=OrderResponse)
async def get_order(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(
        require_permission("read", resource=get_order_resource)
    ),
):
    """
    获取单个订单（使用 ABAC：只有订单所有者或管理员可以访问）
    """
    # 查询订单
    statement = sqlmodel_select(Order).where(Order.id == id)
    result = await session.execute(statement)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return order


@router.post(
    "/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("write")),
):
    """
    创建新订单（需要 write 权限）
    订单的 owner_id 设置为当前用户
    """
    # 使用当前用户的 ID 作为订单所有者
    order = Order(
        **order_data.model_dump(),
        owner_id=current_user.id,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    return order


@router.put("/orders/{id}", response_model=OrderResponse)
async def update_order(
    id: int,
    order_data: OrderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(
        require_permission(
            "write", resource=get_order_resource, owner_getter=get_order_owner
        )
    ),
):
    """
    更新订单（使用 ABAC：只有订单所有者或管理员可以更新）
    """
    # 查询订单
    statement = sqlmodel_select(Order).where(Order.id == id)
    result = await session.execute(statement)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # 更新订单
    update_data = order_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    session.add(order)
    await session.commit()
    await session.refresh(order)

    return order


@router.delete("/orders/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(
        require_permission(
            "delete", resource=get_order_resource, owner_getter=get_order_owner
        )
    ),
):
    """
    删除订单（使用 ABAC：只有订单所有者或管理员可以删除）
    """
    # 查询订单
    statement = sqlmodel_select(Order).where(Order.id == id)
    result = await session.execute(statement)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    await session.delete(order)
    await session.commit()

    return None
