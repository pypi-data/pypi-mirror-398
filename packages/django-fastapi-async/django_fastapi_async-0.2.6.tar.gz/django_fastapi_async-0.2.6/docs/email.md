# Email Framework

FastDjango provides an async email framework with multiple backends.

## Configuration

Configure email in `settings.py`:

```python
# SMTP settings
EMAIL_BACKEND = "smtp"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "your@gmail.com"
EMAIL_HOST_PASSWORD = "your-app-password"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 30

# Default from email
DEFAULT_FROM_EMAIL = "noreply@example.com"

# Subject prefix
EMAIL_SUBJECT_PREFIX = "[MyApp] "

# Admins for error emails
ADMINS = [
    ("Admin Name", "admin@example.com"),
]

MANAGERS = [
    ("Manager Name", "manager@example.com"),
]
```

## Sending Emails

### Simple Email

```python
from fastdjango.core.mail import send_mail

await send_mail(
    subject="Hello",
    message="This is the email body.",
    from_email="from@example.com",
    recipient_list=["to@example.com"],
)
```

### HTML Email

```python
await send_mail(
    subject="Hello",
    message="Plain text version",
    from_email="from@example.com",
    recipient_list=["to@example.com"],
    html_message="<h1>HTML Version</h1><p>Rich content here.</p>",
)
```

### EmailMessage Class

For more control:

```python
from fastdjango.core.mail import EmailMessage

msg = EmailMessage(
    subject="Hello",
    body="Email body",
    from_email="from@example.com",
    to=["to@example.com"],
    cc=["cc@example.com"],
    bcc=["bcc@example.com"],
    reply_to=["reply@example.com"],
    headers={"X-Custom-Header": "value"},
)

await msg.send()
```

### Attachments

```python
from fastdjango.core.mail import EmailMessage

msg = EmailMessage(
    subject="Report",
    body="Please find attached report.",
    to=["to@example.com"],
)

# Attach content directly
msg.attach("report.csv", csv_content.encode(), "text/csv")

# Attach from file
msg.attach_file("/path/to/document.pdf")

await msg.send()
```

### Mass Emails

Send multiple emails efficiently:

```python
from fastdjango.core.mail import send_mass_mail

messages = [
    ("Subject 1", "Body 1", "from@example.com", ["user1@example.com"]),
    ("Subject 2", "Body 2", "from@example.com", ["user2@example.com"]),
    ("Subject 3", "Body 3", "from@example.com", ["user3@example.com"]),
]

await send_mass_mail(messages)
```

### Admin/Manager Emails

```python
from fastdjango.core.mail import mail_admins, mail_managers

# Email to admins
await mail_admins(
    subject="Error Report",
    message="An error occurred...",
)

# Email to managers
await mail_managers(
    subject="Weekly Report",
    message="Here's the weekly report...",
)
```

## Email Backends

### SMTP Backend

Default production backend:

```python
EMAIL_BACKEND = "smtp"
```

### Console Backend

Prints to console (development):

```python
EMAIL_BACKEND = "console"
```

### File Backend

Saves to files (development/testing):

```python
EMAIL_BACKEND = "file"
# Emails saved to 'emails/' directory
```

### In-Memory Backend

Stores in memory (testing):

```python
EMAIL_BACKEND = "memory"

# In tests
from fastdjango.core.mail import InMemoryBackend

InMemoryBackend.clear()
# ... send emails ...
assert len(InMemoryBackend.outbox) == 1
```

### Dummy Backend

Does nothing (disable email):

```python
EMAIL_BACKEND = "dummy"
```

## Custom Backend

Create a custom email backend:

```python
from fastdjango.core.mail import EmailBackend

class MyEmailBackend(EmailBackend):
    async def send_messages(self, email_messages, fail_silently=False):
        for message in email_messages:
            # Send via your service
            await my_email_service.send(
                to=message.to,
                subject=message.subject,
                body=message.body,
            )
        return len(email_messages)
```

## Templates

Send templated emails:

```python
from fastdjango.core.mail import EmailMessage
from fastdjango.templates import templates

# Render template
html_content = templates.get_template("emails/welcome.html").render({
    "user": user,
    "activation_link": link,
})

msg = EmailMessage(
    subject="Welcome!",
    body="Welcome to our site.",  # Plain text fallback
    html_body=html_content,
    to=[user.email],
)
await msg.send()
```

## Error Handling

```python
from fastdjango.core.mail import send_mail

try:
    await send_mail(
        subject="Test",
        message="Body",
        recipient_list=["to@example.com"],
        fail_silently=False,
    )
except Exception as e:
    logger.error(f"Failed to send email: {e}")

# Or silently fail
await send_mail(
    subject="Test",
    message="Body",
    recipient_list=["to@example.com"],
    fail_silently=True,  # Won't raise exceptions
)
```

## Gmail Configuration

For Gmail with 2FA:

1. Enable 2-Factor Authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in settings:

```python
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "your@gmail.com"
EMAIL_HOST_PASSWORD = "xxxx-xxxx-xxxx-xxxx"  # App password
EMAIL_USE_TLS = True
```

## Best Practices

1. **Use templates** for complex emails
2. **Always provide plain text** fallback with HTML
3. **Use fail_silently=False** in development
4. **Use async sending** for better performance
5. **Configure SPF/DKIM** for deliverability
