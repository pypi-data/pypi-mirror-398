# Huitzo SDK

Official Python SDK for the Huitzo Developer Tools platform. This SDK provides easy-to-use clients for interacting with Huitzo's CRON Scheduling Service, Email Service, Telegram Service, LLM Completions Service, and Static Site Hosting Service.

## Features

- **CRON Scheduling Service**: Schedule and manage recurring command executions
- **Email Service**: Send emails and manage templates with Jinja2 support
- **Telegram Service**: Send Telegram messages using plugin-owned bot tokens
- **LLM Completions Service**: Generate text completions using OpenAI, Claude, and other LLM providers
- **Static Site Hosting Service**: Deploy temporary static sites from .zip archives
- **Async/Await Support**: Built on aiohttp for high-performance async operations
- **Type Hints**: Full type hint coverage for IDE support
- **Error Handling**: Comprehensive exception hierarchy for error handling
- **Request Validation**: Pydantic models with automatic validation

## Installation

```bash
pip install huitzo-sdk
```

For local development:

```bash
cd huitzo-sdk
pip install -e .
```

## Quick Start

```python
import asyncio
from huitzo_sdk import HuitzoTools

async def main():
    async with HuitzoTools(api_token="your_token") as sdk:
        # Schedule a CRON job
        job = await sdk.cron.schedule(
            name="daily_report",
            command="finance.report.generate",
            schedule="0 9 * * *",  # Daily at 9 AM
            timezone="America/New_York",
            arguments={"format": "pdf"}
        )
        print(f"Job scheduled: {job['id']}")

        # Send an email
        result = await sdk.email.send(
            recipient_user_id="user-uuid",
            subject="Report Ready",
            html_body="<p>Your daily report is ready!</p>"
        )
        print(f"Email queued: {result['message_id']}")

        # Send Telegram message
        telegram_result = await sdk.telegram.send(
            bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            chat_id="123456789",
            message="<b>Report Ready!</b> Your daily report is available.",
            parse_mode="HTML"
        )
        print(f"Telegram sent: {telegram_result['message_id']}")

        # Generate LLM completion
        completion = await sdk.llm.complete(
            prompt="Summarize this report in 2 sentences",
            model="gpt-4o-mini"
        )
        print(f"AI Summary: {completion['content']}")

        # Deploy a static site
        site = await sdk.sites.deploy(
            zip_file_path="./dist.zip",
            project_name="my-portfolio",
            expiration_minutes=2880  # 2 days
        )
        print(f"Site deployed: {site['access_url']}")

asyncio.run(main())
```

## CRON Scheduling Service

### Schedule a Job

```python
async with HuitzoTools(api_token="your_token") as sdk:
    job = await sdk.cron.schedule(
        name="weekly_report",
        command="finance.report.generate",
        schedule="0 10 * * 1",  # Every Monday at 10 AM
        timezone="America/New_York",
        arguments={"format": "html", "include_charts": True},
        enabled=True
    )
```

**CRON Expression Examples:**
- `"0 9 * * *"` - Every day at 9:00 AM
- `"30 14 * * 5"` - Every Friday at 2:30 PM
- `"0 */6 * * *"` - Every 6 hours
- `"0 0 1 * *"` - First day of every month at midnight

### List Jobs

```python
# Get all active jobs
result = await sdk.cron.list(status="active", limit=50)
for job in result["jobs"]:
    print(f"{job['name']}: {job['next_run_at']}")

# Pagination
result = await sdk.cron.list(limit=10, offset=20)
```

### Get Job Details

```python
job = await sdk.cron.get(job_id)
print(f"Status: {job['status']}")
print(f"Last run: {job['last_run_at']}")
print(f"Next run: {job['next_run_at']}")

# View recent executions
for execution in job.get("executions", []):
    print(f"  {execution['started_at']}: {execution['status']}")
```

### Update Job

```python
# Pause a job
await sdk.cron.update(job_id, enabled=False)

# Change schedule
await sdk.cron.update(
    job_id,
    schedule="0 14 * * *",  # 2 PM daily
    timezone="UTC"
)

# Update arguments
await sdk.cron.update(
    job_id,
    arguments={"format": "csv", "compressed": True}
)
```

### Delete Job

```python
await sdk.cron.delete(job_id)
```

## Email Service

### Send Email

```python
async with HuitzoTools(api_token="your_token") as sdk:
    result = await sdk.email.send(
        recipient_user_id="user-uuid",
        subject="Welcome to Huitzo",
        html_body="<h1>Welcome!</h1><p>Thank you for joining.</p>",
        plain_text_body="Welcome! Thank you for joining."
    )
    print(f"Message ID: {result['message_id']}")
```

### Create Email Template

```python
template = await sdk.email.create_template(
    name="weekly_report",
    subject="Weekly Report for {{ user_name }}",
    html_body="""
        <h1>Hello {{ user_name }}!</h1>
        <p>Your report for {{ week_ending }}:</p>
        <ul>
            <li>Tasks completed: {{ tasks_completed }}</li>
            <li>Hours worked: {{ hours_worked }}</li>
        </ul>
    """,
    variables=["user_name", "week_ending", "tasks_completed", "hours_worked"]
)
```

### Send Email with Template

```python
result = await sdk.email.send(
    recipient_user_id="user-uuid",
    subject="Weekly Report",
    template_id=template_id,
    template_variables={
        "user_name": "John Doe",
        "week_ending": "2025-10-06",
        "tasks_completed": "15",
        "hours_worked": "40"
    }
)
```

### List Templates

```python
templates = await sdk.email.list_templates()
for template in templates["templates"]:
    print(f"{template['name']}: {template['variables']}")
```

### List Sent Emails

```python
# Get all sent emails
result = await sdk.email.list(status="sent", limit=50)

# Filter by date range
from datetime import datetime, timezone, timedelta
week_ago = (datetime.now() - timedelta(days=7)).isoformat()
result = await sdk.email.list(date_from=week_ago)
```

### Get Email Details

```python
email = await sdk.email.get(message_id)
print(f"Status: {email['status']}")
print(f"Sent at: {email['sent_at']}")
if email['status'] == 'failed':
    print(f"Error: {email['error_message']}")
```

## Telegram Service

Send messages to users via Telegram using plugin-owned bot tokens.

**Security:** Bot tokens are plugin-owned secrets. Tokens are never persisted by the platform and are masked in all logs.

### Send Message

```python
async with HuitzoTools(api_token="your_token") as sdk:
    # Send a simple text message
    result = await sdk.telegram.send(
        bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
        chat_id="123456789",
        message="Hello from Huitzo!"
    )
    print(f"Message sent! ID: {result['message_id']}")
```

### Send Formatted Message

```python
# Send HTML formatted message
result = await sdk.telegram.send(
    bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    chat_id="@mychannel",
    message="<b>Bold text</b> and <i>italic text</i>",
    parse_mode="HTML",
    disable_notification=True  # Send silently
)

# Send MarkdownV2 formatted message
result = await sdk.telegram.send(
    bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    chat_id="123456789",
    message="*Bold* and _italic_ text",
    parse_mode="MarkdownV2"
)
```

**Supported parse_mode values:**
- `"HTML"`: Supports `<b>`, `<i>`, `<u>`, `<s>`, `<a>`, `<code>`, `<pre>`, etc.
- `"MarkdownV2"`: Telegram's modern Markdown (requires escaping special chars)
- `None`: Plain text (no formatting)

### Send to Forum Topic

```python
# Send message to specific forum topic
result = await sdk.telegram.send(
    bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    chat_id="-1001234567890",
    message="Message to forum topic",
    message_thread_id=42  # Forum topic ID
)
```

### Send with Advanced Options

```python
# Send with all options
result = await sdk.telegram.send(
    bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    chat_id="123456789",
    message="Important message",
    parse_mode="HTML",
    disable_notification=False,
    protect_content=True,  # Prevent forwarding/saving
    link_preview_options={"is_disabled": True},
    reply_parameters={"message_id": 100}  # Reply to message 100
)
```

### Handle Rate Limiting

Telegram enforces rate limits. Handle 429 errors gracefully:

```python
from huitzo_sdk.exceptions import RateLimitError

try:
    result = await sdk.telegram.send(
        bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
        chat_id="123456789",
        message="Hello!"
    )
except RateLimitError as e:
    retry_after = e.retry_after or 60
    print(f"Rate limited! Retry after {retry_after} seconds")
    # Wait and retry
    await asyncio.sleep(retry_after)
```

### Handle Other Errors

```python
from huitzo_sdk.exceptions import NotFoundError, HuitzoAPIError

try:
    result = await sdk.telegram.send(...)
except NotFoundError:
    print("Chat not found")
except HuitzoAPIError as e:
    if "blocked" in str(e).lower():
        print("Bot was blocked by the user")
    elif "forbidden" in str(e).lower():
        print("Bot is not in the chat or was removed")
    else:
        print(f"Error: {e}")
```

### Getting a Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Save the API token provided (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Configure your bot with `/setdescription`, `/setabouttext`, `/setuserpic`

### Rate Limits

Telegram enforces the following rate limits:
- **Per chat:** ≤1 msg/second (short bursts tolerated)
- **Groups:** ≤20 msgs/minute
- **Global (free tier):** ~30 msgs/second

When rate limited (429), `retry_after` indicates seconds to wait.

### Message Constraints

- **Length:** 1-4096 characters (after entity parsing)
- Messages >4096 chars must be split manually
- Invalid formatting will result in 400 errors

## LLM Completions Service

### Basic Completion

```python
async with HuitzoTools(api_token="your_token") as sdk:
    result = await sdk.llm.complete(
        prompt="Explain quantum computing in 2 sentences",
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500
    )

    print(f"Response: {result['content']}")
    print(f"Model: {result['model']}")
    print(f"Tokens: {result['tokens']['total']}")
    print(f"Cost: ${result['cost_usd']:.4f}")
```

**Available Models:**
- `gpt-4o` - OpenAI GPT-4o (most capable)
- `gpt-4o-mini` - OpenAI GPT-4o Mini (fast and affordable)
- `claude-sonnet-4.5` - Claude Sonnet 4.5 (balanced)
- `claude-haiku-4` - Claude Haiku 4 (fast)

### Streaming Completion

```python
# Stream response as it's generated
async for chunk in await sdk.llm.complete(
    prompt="Write a haiku about coding",
    stream=True
):
    print(chunk, end="", flush=True)
```

### Create LLM Template

```python
template = await sdk.llm.create_template(
    name="code_review",
    template="""Review this {{language}} code and provide feedback:

{{code}}

Focus on:
- Code quality
- Best practices
- Potential bugs""",
    variables=["language", "code"],
    provider_preference="auto",
    model_preference="gpt-4o",
    temperature=0.3
)
```

### Use Template for Completion

```python
result = await sdk.llm.complete_with_template(
    template_name="code_review",
    variables={
        "language": "Python",
        "code": "def add(a, b):\n    return a + b"
    }
)
print(result['content'])
```

### List Available Models

```python
models = await sdk.llm.list_models()
print(f"Providers: {models['providers']}")

for model in models['models']:
    print(f"{model['name']}: ${model['cost_per_1k_prompt']:.4f}/1K tokens")
```

### Get Usage Statistics

```python
# Get today's usage
usage = await sdk.llm.get_usage()
print(f"Requests: {usage['requests_count']}")
print(f"Tokens: {usage['tokens_used']}")
print(f"Cost: ${usage['cost_usd']:.2f}")

# Get usage for specific date
from datetime import date
usage = await sdk.llm.get_usage(period=date(2025, 10, 1))
```

### Check Quota

```python
quota = await sdk.llm.get_quota(user_plan="FREE")
print(f"Daily limit: {quota['daily_limit']}")
print(f"Used today: {quota['current_daily_usage']}")
print(f"Remaining: {quota['quota_remaining']}")

if quota['quota_exceeded']:
    print("Quota exceeded! Upgrade plan or wait for reset.")
```

### List Templates

```python
templates = await sdk.llm.list_templates()
for template in templates:
    print(f"{template['name']}: {template['variables']}")
```

### Get Template Details

```python
template = await sdk.llm.get_template("code_review")
print(f"Template: {template['template']}")
print(f"Model: {template['model_preference']}")
```

## Static Site Hosting Service

### Deploy a Site

Deploy temporary static sites directly from .zip archives:

```python
import asyncio
from huitzo_sdk import HuitzoTools

async def deploy_my_site():
    async with HuitzoTools(api_token="your_token") as sdk:
        # Deploy a static site
        site = await sdk.sites.deploy(
            zip_file_path="./my-site.zip",
            project_name="my-portfolio",
            expiration_minutes=2880  # 2 days (default: 1440 = 24h)
        )

        print(f"Site deployed at: {site['access_url']}")
        print(f"Project: {site['project_name']}")
        print(f"Size: {site['size_bytes']} bytes")
        print(f"Expires at: {site['expires_at']}")

asyncio.run(deploy_my_site())
```

**Features:**
- Upload .zip archives up to 50MB
- Automatic extraction and hosting
- Configurable expiration (default 24h, max 7 days)
- Automatic cleanup of expired sites
- Per-user quotas (5 sites, 200MB total storage)

**Project Name Requirements:**
- 1-100 characters
- Lowercase letters, numbers, and hyphens only
- Must start and end with alphanumeric character
- Examples: `my-portfolio`, `landing-page-v2`, `test-site-123`

### List Sites

```python
# Get all active sites
sites = await sdk.sites.list()
for site in sites:
    print(f"{site['project_name']}: {site['access_url']}")
    print(f"  Status: {site['status']}")
    print(f"  Expires: {site['expires_at']}")

# Include expired sites
all_sites = await sdk.sites.list(include_expired=True)
print(f"Total sites: {len(all_sites)}")
```

### Get Site Details

```python
site = await sdk.sites.get("site-uuid")
print(f"Project: {site['project_name']}")
print(f"URL: {site['access_url']}")
print(f"Status: {site['status']}")
print(f"Size: {site['size_bytes']} bytes")
print(f"Created: {site['created_at']}")
print(f"Expires: {site['expires_at']}")
```

### Delete a Site

```python
# Free up quota by deleting a site
await sdk.sites.delete("site-uuid")
print("Site deleted successfully")
```

### Complete Example

```python
import asyncio
import zipfile
import tempfile
from pathlib import Path
from huitzo_sdk import HuitzoTools, QuotaExceededError

async def deploy_example():
    async with HuitzoTools(api_token="your_token") as sdk:
        # Create a simple test site
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create HTML file
            site_dir = Path(tmpdir) / "site"
            site_dir.mkdir()

            (site_dir / "index.html").write_text("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>My Test Site</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 50px; }
                        h1 { color: #333; }
                    </style>
                </head>
                <body>
                    <h1>Hello from Huitzo Sites!</h1>
                    <p>This is a temporary static site deployed via the Huitzo SDK.</p>
                </body>
                </html>
            """)

            # Create zip file
            zip_path = Path(tmpdir) / "site.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(site_dir / "index.html", "index.html")

            # Deploy the site
            try:
                site = await sdk.sites.deploy(
                    zip_file_path=str(zip_path),
                    project_name="test-site",
                    expiration_minutes=60  # 1 hour
                )

                print(f"✅ Site deployed!")
                print(f"   URL: {site['access_url']}")
                print(f"   Size: {site['size_bytes']} bytes")
                print(f"   Expires: {site['expires_at']}")

                # List all sites
                all_sites = await sdk.sites.list()
                print(f"\n📋 You have {len(all_sites)} active site(s)")

                # Clean up
                await sdk.sites.delete(site['id'])
                print(f"🗑️  Site deleted")

            except QuotaExceededError as e:
                print(f"❌ Quota exceeded: {e}")
                print("   Delete some sites or upgrade your plan")

asyncio.run(deploy_example())
```

## Error Handling

The SDK provides a comprehensive exception hierarchy:

```python
from huitzo_sdk import (
    HuitzoAPIError,          # Base exception
    AuthenticationError,     # 401/403 errors
    NotFoundError,           # 404 errors
    RateLimitError,          # 429 errors
    ValidationError,         # 400 errors
    QuotaExceededError,      # 403 quota errors
)

try:
    job = await sdk.cron.schedule(...)
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except QuotaExceededError as e:
    print(f"Quota exceeded: {e}")
    print("Delete existing resources or upgrade your plan")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    if hasattr(e, 'retry_after') and e.retry_after:
        print(f"Retry after {e.retry_after} seconds")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except HuitzoAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response data: {e.response_data}")
```

## Configuration

### Environment Variables

```bash
# API token (required)
export HUITZO_API_TOKEN="your_token"

# Base URL (optional, default: http://localhost:8010)
export HUITZO_BASE_URL="https://api.huitzo.com"
```

### SDK Configuration

```python
sdk = HuitzoTools(
    api_token="your_token",
    base_url="http://localhost:8010",  # Default
    timeout=30,  # Request timeout in seconds
)
```

## Rate Limits

### CRON Scheduling Service
- **FREE**: 10 jobs
- **PRO**: 100 jobs
- **ENTERPRISE**: Unlimited

### Email Service (per day)
- **FREE**: 100 emails
- **PRO**: 1,000 emails
- **ENTERPRISE**: Unlimited

### Telegram Service
- **Per chat**: ≤1 msg/second (short bursts tolerated)
- **Groups**: ≤20 msgs/minute
- **Global (free tier)**: ~30 msgs/second
- Rate limits are enforced by Telegram, not Huitzo
- 429 errors include `retry_after` (seconds to wait)

### LLM Completions Service (per day)
- **FREE**: 100 requests, $5/month
- **PRO**: 1,000 requests, $50/month
- **ENTERPRISE**: Unlimited

### Static Site Hosting Service
- **Per User Quotas**:
  - Maximum sites: 5 active sites
  - Total storage: 200MB across all sites
  - File size: 50MB per .zip upload
  - Expiration: 1 hour minimum, 7 days maximum
- **Rate Limiting**: Standard API rate limits apply

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=huitzo_sdk --cov-report=html
```

### Example Script

An example usage script is provided:

```bash
# Set API token
export HUITZO_API_TOKEN="your_token"

# Run examples
python example_usage.py
```

## Requirements

- Python 3.10+
- aiohttp >= 3.9.0
- pydantic >= 2.5.0

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/huitzo/huitzo-sdk
- Documentation: https://docs.huitzo.com
- Email: support@huitzo.com
