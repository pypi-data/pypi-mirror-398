"""
Blog routes - API and HTML views.
"""

from fastapi import Request, Query, WebSocket, WebSocketDisconnect
from fastdjango.routing import Router
from fastdjango.templates import render
from fastdjango.contrib.auth.decorators import login_required
from fastdjango.routing.websocket import ConnectionManager

from .models import Post, Category, Comment
from .schemas import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostList,
    CommentCreate,
    CommentResponse,
)

router = Router(prefix="/blog", tags=["blog"])

# WebSocket connection manager for live updates
manager = ConnectionManager()


# ============== HTML Views ==============

@router.get("/")
async def blog_index(request: Request):
    """Blog homepage - list published posts."""
    posts = await Post.objects.filter(published=True).prefetch_related("author", "category")
    categories = await Category.objects.all()

    return render(
        "blog/index.html",
        {
            "posts": posts,
            "categories": categories,
        },
        request=request,
    )


@router.get("/post/{slug}")
async def blog_post(request: Request, slug: str):
    """Single post view."""
    post = await Post.objects.get_or_404(slug=slug, published=True)

    # Increment views
    post.views += 1
    await post.save(update_fields=["views"])

    # Get approved comments
    comments = await Comment.objects.filter(post=post, approved=True)

    return render(
        "blog/post.html",
        {
            "post": post,
            "comments": comments,
        },
        request=request,
    )


@router.get("/category/{slug}")
async def blog_category(request: Request, slug: str):
    """Posts by category."""
    category = await Category.objects.get_or_404(slug=slug)
    posts = await Post.objects.filter(category=category, published=True)

    return render(
        "blog/category.html",
        {
            "category": category,
            "posts": posts,
        },
        request=request,
    )


# ============== API Endpoints ==============

@router.get("/api/posts", response_model=PostList)
async def api_list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: str | None = None,
    featured: bool | None = None,
):
    """List posts API."""
    qs = Post.objects.filter(published=True)

    if category:
        qs = qs.filter(category__slug=category)
    if featured is not None:
        qs = qs.filter(featured=featured)

    total = await qs.count()
    posts = await qs.offset((page - 1) * per_page).limit(per_page)

    return {
        "items": posts,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/api/posts/{slug}", response_model=PostResponse)
async def api_get_post(slug: str):
    """Get single post API."""
    return await Post.objects.get_or_404(slug=slug, published=True)


@router.post("/api/posts", response_model=PostResponse)
@login_required
async def api_create_post(request: Request, data: PostCreate):
    """Create post API (authenticated)."""
    post = await Post.objects.create(
        **data.model_dump(),
        author=request.state.user,
    )
    return post


@router.put("/api/posts/{slug}", response_model=PostResponse)
@login_required
async def api_update_post(request: Request, slug: str, data: PostUpdate):
    """Update post API (authenticated)."""
    post = await Post.objects.get_or_404(slug=slug)

    # Check ownership
    if post.author_id != request.state.user.pk:
        from fastdjango.core.exceptions import PermissionDenied
        raise PermissionDenied("You can only edit your own posts")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(post, key, value)

    await post.save()
    return post


@router.delete("/api/posts/{slug}")
@login_required
async def api_delete_post(request: Request, slug: str):
    """Delete post API (authenticated)."""
    post = await Post.objects.get_or_404(slug=slug)

    if post.author_id != request.state.user.pk:
        from fastdjango.core.exceptions import PermissionDenied
        raise PermissionDenied("You can only delete your own posts")

    await post.delete()
    return {"message": "Post deleted"}


@router.post("/api/posts/{slug}/comments", response_model=CommentResponse)
async def api_create_comment(slug: str, data: CommentCreate):
    """Create comment on a post."""
    post = await Post.objects.get_or_404(slug=slug)

    comment = await Comment.objects.create(
        post=post,
        name=data.name,
        email=data.email,
        content=data.content,
    )

    # Notify via WebSocket
    await manager.broadcast(
        {
            "type": "new_comment",
            "post_slug": slug,
            "comment": {
                "name": comment.name,
                "content": comment.content[:100],
            },
        },
        group=f"post_{post.pk}",
    )

    return comment


# ============== WebSocket ==============

@router.websocket("/ws/post/{post_id}")
async def post_websocket(websocket: WebSocket, post_id: int):
    """WebSocket for real-time post updates."""
    await manager.connect(websocket, group=f"post_{post_id}")

    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, group=f"post_{post_id}")


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    """WebSocket for live blog updates (new posts, etc.)."""
    await manager.connect(websocket, group="live_updates")

    try:
        await websocket.send_json({"type": "connected", "message": "Welcome to live updates!"})

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, group="live_updates")
