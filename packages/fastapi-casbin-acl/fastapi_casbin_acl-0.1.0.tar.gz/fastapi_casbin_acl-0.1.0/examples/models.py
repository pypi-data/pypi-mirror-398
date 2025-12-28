"""
SQLModel 数据模型
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """
    用户模型
    """

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)

    # 关系：一个用户可以有多个订单
    orders: list["Order"] = Relationship(back_populates="owner")


class Order(SQLModel, table=True):
    """
    订单模型
    """

    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    amount: float = Field(default=0.0)
    status: str = Field(
        default="pending", max_length=20
    )  # pending, completed, cancelled
    owner_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # 关系：订单属于一个用户
    owner: User = Relationship(back_populates="orders")

    def get_owner_sub(self) -> str | None:
        """
        获取订单的所有者标识（用于 ABAC 权限检查）
        返回所有者的用户 ID（字符串），与 get_subject_from_user 返回的格式保持一致
        """
        # 直接返回 owner_id，转换为字符串以匹配 subject 格式
        if self.owner_id is not None:
            return str(self.owner_id)
        return None


# Pydantic 模型用于 API 请求/响应
class UserCreate(SQLModel):
    """创建用户的请求模型"""

    username: str
    email: str


class UserResponse(SQLModel):
    """用户响应模型"""

    id: int
    username: str
    email: str
    created_at: datetime


class OrderCreate(SQLModel):
    """创建订单的请求模型"""

    title: str
    description: Optional[str] = None
    amount: float


class OrderUpdate(SQLModel):
    """更新订单的请求模型"""

    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None


class OrderResponse(SQLModel):
    """订单响应模型"""

    id: int
    title: str
    description: Optional[str]
    amount: float
    status: str
    owner_id: int
    created_at: datetime
