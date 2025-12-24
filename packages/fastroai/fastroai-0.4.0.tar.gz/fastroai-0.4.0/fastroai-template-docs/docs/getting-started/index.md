# Getting Started

**From purchase to working AI API in 5 minutes.**

You bought FastroAI to skip months of infrastructure work. Smart move. This guide gets you running immediately - not in theory, but actually running on your machine with a real AI responding to requests.

Some people like to understand everything before they start (check out the [Learn section](../learn/index.md) if that's you). Others want to see it working first. This guide is for the second group - we'll get you running immediately, then you can explore how it works.

## What You're Getting

Before we dive into setup, you should know what you actually bought. FastroAI is a backend template that handles all the boring infrastructure so you can focus on building your AI product.

<div class="grid cards" markdown>

-   :material-robot:{ .lg .middle } **FastroAgent**

    ---

    Production-ready wrapper around PydanticAI with memory management, usage tracking, and tool integration.

-   :material-shield-account:{ .lg .middle } **Authentication**

    ---

    JWT + OAuth that actually works. Email/password, Google, GitHub - all configured.

-   :material-credit-card:{ .lg .middle } **Payments**

    ---

    Complete Stripe integration with subscriptions, webhooks, and entitlements.

-   :material-server:{ .lg .middle } **Infrastructure**

    ---

    Database, caching, background tasks, monitoring - everything production needs.

</div>

The key thing here is that everything works together. Authentication talks to payments, payments talk to entitlements, entitlements control AI access. You don't have to wire this up yourself - it's already done.

## The 5-Minute Setup

This isn't marketing fluff - you really will have a working AI API in 5 minutes. The setup is deliberately simple because complexity kills momentum. Get it running first, understand it later.

### Prerequisites

You need three things to get started:

| Requirement | Why |
|------------|-----|
| **Python 3.11+** | Modern type hints and async features |
| **Docker & Docker Compose** | Runs all services with one command |
| **AI API Key** | OpenAI, Anthropic, or your provider |

Don't have Docker? Install it from [docker.com](https://docker.com). Don't have an AI key? Get one from [OpenAI](https://platform.openai.com), [Anthropic](https://console.anthropic.com), or [Groq](https://console.groq.com) (Groq has a free tier that's perfect for testing).

### 1. Clone Your Template

When you purchased FastroAI, you received access to a private GitHub repository. First, click the green `Use this template` button in the top right corner of the repository to create your own copy. **Important: Keep your new repository private** - this is commercial code you paid for.

Then clone your new repository:

```bash
git clone <your-new-repo-url>
cd fastroai
```

This gives you the complete FastroAI codebase. No missing pieces, no "upgrade to pro for full features" - you have everything.

### 2. Configure Environment

FastroAI uses environment variables for configuration. This keeps secrets out of your code and makes deployment straightforward. There are three config files:

```bash
# Copy all the example files
cp .env.example .env                          # Docker Compose settings
cp backend/.env.example backend/.env          # Backend API configuration
cp landing_page/.env.example landing_page/.env # Landing page (optional)

# Edit backend/.env with your values
nano backend/.env
```

The backend configuration is what matters most. The configuration files have lots of options, but right now you only need to change these essential settings:

**Required changes in backend/.env:**

```env
# Security - MUST change this (generate with: openssl rand -hex 32)
SECRET_KEY=<your-generated-secret-key>

# AI Provider (at least one is required)
OPENAI_API_KEY=<your-openai-key>
# ANTHROPIC_API_KEY=<your-anthropic-key>

# Admin Panel (web interface at /admin)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<choose-strong-password>
ADMIN_EMAIL=admin@yourdomain.com
```

Generate your SECRET_KEY with this command:
```bash
openssl rand -hex 32
```

The admin credentials are used for both the application superuser (for API access) and the admin web interface at `/admin`.

### 3. Start Everything

One command starts your entire stack:

```bash
# Launch the entire stack
docker compose up -d

# Wait ~30 seconds, then initialize database
docker compose run --rm setup_initial_data
```

What's happening here? Docker is starting PostgreSQL, Redis, your FastAPI backend, Taskiq workers, and the admin interface. The initialization script creates your database tables and sets up the admin user.

### 4. Verify It Works

Let's make sure everything started correctly:

```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

If you see that response, congratulations - you have a working AI backend. The API is running, the database is configured, and the AI integration is ready.

## What's Running

Now that your stack is running, let's explore what you actually have. These aren't placeholder pages - they're fully functional interfaces to your system:

<div class="grid cards" markdown>

-   :material-api:{ .lg .middle } **[Interactive API Docs](http://localhost:8000/docs)**

    ---

    Swagger UI with live testing. Try endpoints directly in your browser.

-   :material-view-dashboard:{ .lg .middle } **[Admin Panel](http://localhost:8000/admin)**

    ---

    Manage users, payments, and data. Login with your admin credentials.

-   :material-heart-pulse:{ .lg .middle } **[Health Check](http://localhost:8000/health)**

    ---

    System status monitoring. Verify all services are operational.

</div>

The API docs are particularly useful. Open [localhost:8000/docs](http://localhost:8000/docs) and you'll see every endpoint your API provides. You can test them right in the browser - no Postman needed.

## Test Your AI Integration

Reading about features is boring. Let's actually use the AI to make sure everything works. We'll create a user, get authenticated, and have a conversation with the AI.

### 1. Register a User

Open [localhost:8000/docs](http://localhost:8000/docs) and find `POST /api/v1/auth/register`. Click "Try it out" and use this body:

```json
{
  "email": "test@example.com",
  "password": "testpassword123",
  "full_name": "Test User"
}
```

Click Execute. You just created your first user.

### 2. Login to Get Session

Now find `POST /api/v1/auth/login` and use the same email/password. The response will include:
```json
{
  "csrf_token": "abc123..."
}
```
Copy this CSRF token - you'll need it for authenticated requests. The session cookie is set automatically.

### 3. Create AI Conversation

Find `POST /api/v1/conversations/`. In the request, add the CSRF token in the `X-CSRF-Token` header field. Then try this request body:

```json
{
  "title": "First Chat",
  "messages": [
    {
      "role": "user",
      "content": "What is FastroAI?"
    }
  ]
}
```

When you click Execute, the AI will respond with information about FastroAI. If you see that response, everything is working perfectly - authentication, database, AI integration, the whole stack.

## Next Steps

You have a working AI backend. Now you need to decide what to do with it:

<div class="grid cards" markdown>

-   :material-map:{ .lg .middle } **[Explore the Template](./understanding-template.md)**

    ---

    Understand what's included: authentication, payments, entitlements, and how to start building.

-   :material-cog:{ .lg .middle } **[Configure Settings](./configuration.md)**

    ---

    Adjust environment variables, set up AI providers, configure payments and monitoring.

-   :material-tune:{ .lg .middle } **[Customize Features](./customizing-features.md)**

    ---

    Remove what you don't need. Start minimal, add complexity only when required.

-   :material-book-open:{ .lg .middle } **[Learn AI Development](../learn/index.md)**

    ---

    New to AI? Work through our structured learning path from concepts to implementation.

</div>

Most people start by exploring the template to understand what they have, then begin customizing.

## Troubleshooting

Things don't always work perfectly on the first try. Here are the most common issues and their solutions:

| Problem | Solution |
|---------|----------|
| **API not starting** | Check logs: `docker compose logs web` |
| **Database errors** | Run migrations: `docker compose exec web alembic upgrade head` |
| **AI not responding** | Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `backend/.env` |
| **Port conflicts** | Stop conflicting services or change ports in `docker-compose.yml` |

The logs are your friend. If something isn't working, `docker compose logs` will usually tell you exactly what's wrong.

---

**You're ready to build.** You have a working AI backend with authentication, payments, and all the infrastructure you need. The boring stuff is done. Now go build something interesting.

<div style="text-align: center; margin-top: 50px;">
    <a href="../getting-started/understanding-template/" class="md-button md-button--primary">
        Next: Understanding Your Template →
    </a>
</div>
