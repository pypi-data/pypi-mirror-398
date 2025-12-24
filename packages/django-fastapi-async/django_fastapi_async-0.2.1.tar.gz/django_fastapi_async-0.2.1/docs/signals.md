# Signals

FastDjango provides an async signal system for decoupled communication between components.

## Overview

Signals allow senders to notify receivers when certain actions occur. All signal handlers are async.

## Built-in Signals

### Model Signals

```python
from fastdjango.core.signals import (
    pre_save,
    post_save,
    pre_delete,
    post_delete,
    m2m_changed,
)
```

### Request Signals

```python
from fastdjango.core.signals import (
    request_started,
    request_finished,
)
```

### User Signals

```python
from fastdjango.core.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
```

## Connecting Receivers

### Decorator Syntax

```python
from fastdjango.core.signals import post_save
from myapp.models import User

@post_save.connect
async def on_any_save(sender, instance, created, **kwargs):
    """Called when any model is saved."""
    print(f"Saved: {instance}")

@post_save.connect(sender=User)
async def on_user_save(sender, instance, created, **kwargs):
    """Called only when User is saved."""
    if created:
        await send_welcome_email(instance)
```

### Manual Connection

```python
async def my_handler(sender, instance, **kwargs):
    pass

post_save.connect(my_handler, sender=User)
```

## Disconnecting Receivers

```python
post_save.disconnect(my_handler, sender=User)
```

## Sending Signals

### Basic Send

```python
from fastdjango.core.signals import Signal

my_signal = Signal(providing_args=["data"])

# Send signal
responses = await my_signal.send(sender=MyClass, data={"key": "value"})

# responses is list of (receiver, response) tuples
for receiver, response in responses:
    print(f"{receiver} returned {response}")
```

### Robust Send

Catches exceptions from receivers:

```python
responses = await my_signal.send_robust(sender=MyClass, data=data)

for receiver, response in responses:
    if isinstance(response, Exception):
        logger.error(f"Handler {receiver} failed: {response}")
```

## Custom Signals

```python
from fastdjango.core.signals import Signal

# Define custom signal
order_placed = Signal(providing_args=["order", "user"])

# Connect receiver
@order_placed.connect
async def send_confirmation(sender, order, user, **kwargs):
    await send_email(
        to=user.email,
        subject=f"Order #{order.id} confirmed",
        body=f"Thank you for your order!",
    )

@order_placed.connect
async def notify_warehouse(sender, order, **kwargs):
    await warehouse_api.create_shipment(order)

# Send signal
await order_placed.send(
    sender=Order,
    order=order,
    user=request.state.user,
)
```

## Model Signal Arguments

### pre_save / post_save

```python
@post_save.connect(sender=Post)
async def on_post_save(
    sender,       # Model class
    instance,     # Model instance
    created,      # True if new, False if update
    raw=False,    # True if loading fixtures
    using=None,   # Database alias
    update_fields=None,  # Fields being updated
    **kwargs
):
    if created:
        await notify_followers(instance.author, instance)
```

### pre_delete / post_delete

```python
@pre_delete.connect(sender=Post)
async def on_post_delete(
    sender,       # Model class
    instance,     # Model instance being deleted
    using=None,   # Database alias
    **kwargs
):
    # Clean up related files
    await delete_attachments(instance)
```

### m2m_changed

```python
@m2m_changed.connect(sender=Post.tags.through)
async def on_tags_changed(
    sender,       # Through model
    instance,     # Model instance
    action,       # "pre_add", "post_add", "pre_remove", etc.
    reverse,      # True if relation is reversed
    model,        # Related model class
    pk_set,       # Set of primary keys
    using=None,
    **kwargs
):
    if action == "post_add":
        await update_tag_counts(pk_set)
```

## Request Signals

```python
@request_started.connect
async def on_request_start(sender, scope, **kwargs):
    # Log request start
    logger.info(f"Request started: {scope['path']}")

@request_finished.connect
async def on_request_end(sender, scope, **kwargs):
    # Clean up request resources
    pass
```

## User Signals

```python
@user_logged_in.connect
async def on_login(sender, request, user, **kwargs):
    await log_login(user, request.client.host)

@user_logged_out.connect
async def on_logout(sender, request, user, **kwargs):
    await log_logout(user)

@user_login_failed.connect
async def on_login_failed(sender, credentials, request, **kwargs):
    await log_failed_attempt(credentials.get("username"), request.client.host)
```

## Weak References

By default, receivers are stored as weak references:

```python
# Receiver may be garbage collected
@post_save.connect(weak=True)  # Default
async def handler(sender, **kwargs):
    pass

# Receiver won't be garbage collected
@post_save.connect(weak=False)
async def persistent_handler(sender, **kwargs):
    pass
```

## Checking for Listeners

```python
if post_save.has_listeners(sender=User):
    # There are handlers for User saves
    pass
```

## Best Practices

1. **Keep handlers fast** - Don't block with slow operations
2. **Use send_robust in production** - Catch handler errors
3. **Filter by sender** - Avoid unnecessary handler calls
4. **Document signals** - List providing_args for clarity
5. **Handle exceptions** - Signals shouldn't crash the app
6. **Use for decoupling** - Not for direct function calls

## Example: Audit Log

```python
from fastdjango.core.signals import post_save, post_delete, Signal
from myapp.models import AuditLog

# Track all model changes
@post_save.connect
async def log_save(sender, instance, created, **kwargs):
    if sender == AuditLog:
        return  # Don't log audit logs

    await AuditLog.objects.create(
        model=sender.__name__,
        object_id=instance.pk,
        action="create" if created else "update",
        changes=kwargs.get("update_fields"),
    )

@post_delete.connect
async def log_delete(sender, instance, **kwargs):
    if sender == AuditLog:
        return

    await AuditLog.objects.create(
        model=sender.__name__,
        object_id=instance.pk,
        action="delete",
    )
```
