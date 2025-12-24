"""
Blog Pydantic schemas.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Category schemas
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: str = ""


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# Post schemas
class PostBase(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: str = ""
    published: bool = False
    featured: bool = False


class PostCreate(PostBase):
    category_id: Optional[int] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None
    category_id: Optional[int] = None


class PostResponse(PostBase):
    id: int
    views: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostList(BaseModel):
    items: list[PostResponse]
    total: int
    page: int = 1
    per_page: int = 10


# Comment schemas
class CommentBase(BaseModel):
    name: str
    email: EmailStr
    content: str


class CommentCreate(CommentBase):
    post_id: int


class CommentResponse(CommentBase):
    id: int
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True
