# Email

FastroAI uses Postmark for transactional email delivery. Emails are rendered from Jinja2 templates and can be sent synchronously through the email service or queued as background tasks.

## Configuration

```bash
EMAIL_ENABLED=true
POSTMARK_SERVER_TOKEN=your-server-token  # Required
EMAIL_SENDER_ADDRESS=noreply@yourdomain.com
EMAIL_SENDER_NAME=Your App Name

# Tracking
EMAIL_TRACK_OPENS=true
EMAIL_TRACK_LINKS=None           # None, HtmlAndText, HtmlOnly, TextOnly

# Retry behavior
EMAIL_TIMEOUT=30
EMAIL_MAX_RETRIES=3

# Test mode (writes to filesystem instead of sending)
EMAIL_TEST_MODE=false
EMAIL_TEST_OUTPUT_DIR=./email_previews
```

Get your `POSTMARK_SERVER_TOKEN` from the Postmark dashboard under Server > API Tokens.

## Sending Emails

### Direct Service Usage

For immediate sending within a request:

```python
from modules.email.service import EmailService
from modules.email.enums import EmailType, EmailPriority

email_service = EmailService()

message_id = await email_service.send_email(
    db=db,
    recipient="user@example.com",
    subject="Welcome to our service",
    template_name="account/welcome",
    template_vars={
        "user_name": "Jane",
        "user_email": "jane@example.com",
    },
    email_type=EmailType.WELCOME,
    priority=EmailPriority.NORMAL,
    user_id=user.id,  # optional, for tracking
)
```

### Background Task Usage

For non-blocking sends (recommended for most cases):

```python
from modules.email.tasks import send_email_task

await send_email_task.kiq(
    recipient_email="user@example.com",
    subject="Welcome",
    template_name="account/welcome",
    template_vars={"user_name": "Jane", "user_email": "jane@example.com"},
    email_type="welcome",
    priority="normal",
    user_id=user.id,
)
```

The task returns immediately. A worker processes the actual send in the background.

### Built-in Task Functions

| Task | Purpose |
|------|---------|
| `send_email_task` | Generic email send |
| `send_bulk_email_task` | Multiple recipients |
| `send_welcome_email_task` | New user welcome |
| `send_password_reset_email_task` | Password reset link |
| `send_verification_email_task` | Email verification |
| `send_notification_email_task` | General notification |
| `send_system_wide_notification_emails_task` | Broadcast to all users |

## Templates

Templates live in `backend/src/modules/email/templates/`. Each email needs both an HTML and a plain text version:

```
templates/
├── base.html                   # Base HTML layout
├── base.txt                    # Base text layout
├── account/
│   ├── welcome.html
│   └── welcome.txt
├── notification/
│   ├── general.html
│   └── general.txt
└── landing/
    ├── contact_confirmation.html
    └── contact_confirmation.txt
```

### Creating a Template

Templates use Jinja2 with inheritance. Extend the base template and fill in the content block:

**HTML version** (`templates/account/welcome.html`):

```html
{% extends "base.html" %}

{% block content %}
<h1>Welcome to {{ company_name | default("FastroAI") }}!</h1>

<p>Hi {{ user_name }},</p>
<p>Your account is ready. We're glad to have you.</p>

{% if verification_required %}
<div class="alert alert-warning">
    <strong>Please verify your email</strong><br>
    <a href="{{ verification_url }}" class="btn">Verify Email Address</a>
</div>
{% endif %}

<p>Best regards,<br>The {{ company_name }} Team</p>
{% endblock %}
```

**Text version** (`templates/account/welcome.txt`):

```text
{% extends "base.txt" %}

{% block content %}
Welcome to {{ company_name | default("FastroAI") }}!

Hi {{ user_name }},

Your account is ready. We're glad to have you.

{% if verification_required %}
Please verify your email address:
{{ verification_url }}
{% endif %}

Best regards,
The {{ company_name }} Team
{% endblock %}
```

### Base Template Features

The HTML base template (`base.html`) handles the boilerplate so your templates can focus on content. It includes a responsive layout that works on mobile, pre-styled alert boxes (`alert-info`, `alert-warning`, `alert-error`, `alert-success`), button styles with hover effects, and a consistent header/footer with your company name and the current year.

### Always-Available Variables

These variables are available in every template:

| Variable | Description |
|----------|-------------|
| `company_name` | Defaults to "FastroAI" |
| `current_year` | Current year for footer |
| `domain` | Your domain for links |
| `unsubscribe_url` | Optional unsubscribe link |

## Email Tracking

Every email is logged to the database with status updates from Postmark webhooks:

| Status | Meaning |
|--------|---------|
| `PENDING` | Queued but not sent |
| `SENT` | Sent to Postmark |
| `DELIVERED` | Confirmed delivery |
| `OPENED` | Recipient opened |
| `CLICKED` | Link clicked |
| `BOUNCED` | Bounced back |
| `SPAM` | Marked as spam |

The `EmailLog` model in `backend/src/modules/email/models.py` stores recipient, subject, template, status, timestamps, and Postmark message ID for each email.

## Test Mode

During development, you might not want to actually send emails. Enable test mode:

```bash
EMAIL_TEST_MODE=true
EMAIL_TEST_OUTPUT_DIR=./email_previews
```

Emails get written to the output directory as HTML files instead of being sent. This lets you preview templates without using Postmark credits or spamming test addresses.

## Error Handling

The email system defines specific exceptions:

| Exception | When |
|-----------|------|
| `EmailSendError` | Postmark API failure, network issues |
| `EmailTemplateError` | Missing template, syntax error |
| `EmailConfigurationError` | Missing credentials, invalid settings |

When using background tasks, errors are logged and the task can be retried based on `EMAIL_MAX_RETRIES`.

## Key Files

| Component | Location |
|-----------|----------|
| Email service | `backend/src/modules/email/service.py` |
| Email tasks | `backend/src/modules/email/tasks.py` |
| Templates | `backend/src/modules/email/templates/` |
| EmailLog model | `backend/src/modules/email/models.py` |
| Postmark client | `backend/src/infrastructure/email/client.py` |
| Settings | `backend/src/infrastructure/email/settings.py` |

---

[← Background Tasks](background-tasks.md){ .md-button } [Observability →](../observability/index.md){ .md-button .md-button--primary }
