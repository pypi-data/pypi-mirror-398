# Configuration

**Everything you actually need to know about FastroAI's settings.**

FastroAI has a lot of configuration options. You don't need most of them right now. This guide shows you what matters today and what can wait until later.

The configuration lives in environment variables, which is good because your secrets stay out of your code and deployment stays simple. But there are three different `.env` files and hundreds of options, which can be overwhelming. So we'll focus on what you actually need to change.

## The Configuration Files

FastroAI splits configuration across three files for good reasons:

```
fastroai/
├── .env                    # Docker Compose orchestration
├── backend/.env           # Your API settings (95% of your work)
└── landing_page/.env      # Landing page (ignore unless you're using it)
```

The `backend/.env` file is where everything important happens. The root `.env` is just for Docker Compose, and the landing page has its own config that you probably won't need.

!!! tip "Start from the examples"
    FastroAI includes `.env.example` files with all available options and sensible defaults. Copy these and modify only what you need - don't write configs from scratch.

## Settings That Matter Now

You just want to get building. Here are the only settings you need to understand today:

### Security Settings

```bash
# backend/.env

# This encrypts sessions and tokens - MUST be unique
SECRET_KEY=your-very-long-random-string-here

# Generate a proper key:
# openssl rand -hex 32
```

The `SECRET_KEY` is non-negotiable. If you use the default, anyone can forge sessions and impersonate users. Generate a real one:

```bash
openssl rand -hex 32
# Output: 7f4d3e2a9b8c1d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e
```

### AI Provider Settings

FastroAI works with OpenAI and Anthropic. Pick one (or configure both):

```bash
# For OpenAI
OPENAI_API_KEY=sk-proj-...

# For Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...

# Choose your default model
AI_DEFAULT_MODEL=gpt-4o-mini  # Good balance of cost/quality
# AI_DEFAULT_MODEL=claude-3-5-haiku-20241022  # Cheap and fast

# Optional AI tuning
AI_TEMPERATURE=0.7  # Creativity (0.0-2.0)
AI_MAX_TOKENS=4000  # Max response length
```

The model choice matters. Start with cheaper models (`gpt-4o-mini` or `claude-3-5-haiku`) during development. You're going to make a lot of test calls.

### Database Connection

FastroAI supports two database configuration patterns:

**Development Pattern (Individual Components):**
```bash
# For Docker Compose (recommended)
POSTGRES_SERVER=db  # Docker service name
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethisinproduction
POSTGRES_DB=fastroai

# For local PostgreSQL (without Docker)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=fastroai
```

**Production Pattern (Single Connection String):**
```bash
# Managed database services (AWS RDS, Supabase, etc.)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Example with SSL (common in production)
DATABASE_URL=postgresql+asyncpg://myuser:mypass@prod.example.com:5432/mydb?sslmode=require
```

!!! tip "Production Database Configuration"
    When both `DATABASE_URL` and individual `POSTGRES_*` variables are set, `DATABASE_URL` takes precedence. This lets you use individual components for development and a full connection string for production without changing your code.
    
    **Important:** FastroAI uses async PostgreSQL, so your connection string must use `postgresql+asyncpg://` (not `postgresql://`). Managed database providers often give you `postgresql://` URLs - just add the `+asyncpg` part.

That's it. Everything else has defaults that work.

### Admin Access

FastroAI has two admin systems (we covered this in Getting Started):

```bash
# Application superuser and admin panel credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=actuallysecurepassword
ADMIN_EMAIL=you@yourdomain.com
```

In production, restrict admin panel access at the reverse proxy level (see Caddy configuration).

## Settings for Later

These sections are important but not on day one. Come back when you need them.

### When You Want to Charge Money

Stripe integration is built in, but you don't need it until you're ready to charge:

```bash
# Get these from stripe.com/dashboard
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# For webhooks (local testing)
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
# Copy the whsec_... it shows you
STRIPE_WEBHOOK_SECRET=whsec_...
```

Start with test keys. Switch to live keys only when real money is involved.

### When You Need Email

FastroAI uses Postmark because it actually delivers emails:

```bash
# From postmark.com (they have a free tier)
POSTMARK_SERVER_TOKEN=your-postmark-server-token-here
EMAIL_SENDER_ADDRESS=noreply@yourdomain.com
EMAIL_SENDER_NAME=Your App Name

# For testing without sending real emails
EMAIL_ENABLED=false  # Logs emails to console instead
```

No Postmark account? Set `EMAIL_ENABLED=false`. Emails appear in your logs instead of inboxes.

### When Users Want Social Login

OAuth is nice but not essential:

```bash
# Google (from console.cloud.google.com)
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...

# GitHub (from github.com/settings/developers)
OAUTH_GITHUB_CLIENT_ID=...
OAUTH_GITHUB_CLIENT_SECRET=...
```

Skip this entirely at first. Email/password authentication works fine.

### When You Hit Performance Limits

Redis handles caching and rate limiting:

```bash
# These defaults work for Docker Compose
CACHE_REDIS_HOST=redis
DEFAULT_RATE_LIMIT_LIMIT=100  # Requests/minute

# Tune these if you need to
CACHE_ENABLED=true  # Turn off during debugging
RATE_LIMITER_ENABLED=true  # Turn off for load testing
```

The defaults handle thousands of requests. You won't need to touch these until you have real traffic.

## Production Configuration

Production is different. You need real security, scaling decisions, and proper deployment configuration.

### Essential Production Settings

```bash
# Enables strict security validation
ENVIRONMENT=production

# Use a strong, unique secret key
SECRET_KEY=<generated-with-openssl-rand-hex-32>

# Strong database password
POSTGRES_PASSWORD=<actually-secure-password>

# Your actual domain for CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Setting `ENVIRONMENT=production` enables security validations. FastroAI will refuse to start if you're using default passwords or weak settings.

### Deployment Patterns

How you configure workers depends on your deployment strategy:

**Cloud/Container Orchestration (Recommended)**
```bash
WORKERS=1  # Single worker per container
```
Scale by increasing container replicas. Let Kubernetes, Docker Swarm, or your cloud platform handle load balancing. This is the modern approach - each container runs one worker, you scale by adding more containers.

**Self-Hosted/Single Server**
```bash
WORKERS=4  # Usually 2x CPU cores
```
Scale by increasing workers within a single container. Good for VPS or dedicated servers where you're not using container orchestration. Set `WORKERS` to match your server's CPU cores.

### Monitoring

You want to know when things break:

```bash
# Logfire (from logfire.pydantic.dev - free tier available)
LOGFIRE_TOKEN=...
LOGFIRE_PROJECT_NAME=your-project

# Traces every request, AI call, database query
LOGFIRE_SEND_TO_LOGFIRE=true
```

Logfire shows you exactly what your app is doing - request times, AI costs, error traces. The free tier is generous.

## Configuration Strategy

<div class="grid cards" markdown>

-   :material-rocket-launch: **Day 1: Just Starting**

    ---

    You're exploring, building features, learning the stack. Focus on getting started, not perfection.

    - Generate a real `SECRET_KEY`
    - Add your AI API key (OpenAI or Anthropic)
    - Set a secure admin password
    - Everything else: use defaults

-   :material-cog: **Week 1: Building Features**

    ---

    You know what you're building. Start configuring for your specific needs.

    - Configure your preferred AI model
    - Set up email if you need it
    - Add OAuth if users ask for it
    - Tune your development workflow

-   :material-account-group: **Month 1: Getting Users**

    ---

    People are actually using your app. Time for business configuration.

    - Add Stripe keys for payments
    - Configure monitoring and observability
    - Tune rate limits based on usage
    - Set up proper error tracking

-   :material-shield-check: **Production: Real Business**

    ---

    Money flowing, users depending on you. Security and reliability matter.

    - Set `ENVIRONMENT=production`
    - Configure your domain for CORS
    - Add IP restrictions for admin access
    - Set up monitoring alerts

</div>

## Docker Compose Configuration

The root `.env` file configures Docker itself:

```bash
# .env (root directory)

# Use production compose file
COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml

# Container naming
COMPOSE_PROJECT_NAME=fastroai

# Auto-restart after reboots
RESTART_POLICY=always
```

Most people never need to change these.

## Loading Priority

Configuration loads in this order (later overrides earlier):

1. Defaults in code
2. `.env` files
3. Environment variables
4. Command line arguments

This means you can override anything without changing files:

```bash
# Override for one run
AI_DEFAULT_MODEL=gpt-4o docker compose up

# Override in production
export ENVIRONMENT=production
docker compose up
```

## Quick Reference

Complete list of all environment variables across FastroAI's configuration files:

### Backend Configuration (`backend/.env`)

| Category | Variable | Default | Description |
|----------|----------|---------|-------------|
| **Environment** | `ENVIRONMENT` | `development` | Application environment (development, staging, production) |
| **Security** | `SECRET_KEY` | `insecure-secret-key-change-this` | Session encryption key (generate with `openssl rand -hex 32`) |
| **Database** | `DATABASE_URL` | - | Complete database URL (production pattern, takes precedence) |
| | `POSTGRES_USER` | `postgres` | Database username |
| | `POSTGRES_PASSWORD` | `postgres` | Database password |
| | `POSTGRES_SERVER` | `localhost` | Database host |
| | `POSTGRES_PORT` | `5432` | Database port |
| | `POSTGRES_DB` | `postgres` | Database name (example uses `fastroai`) |
| **AI Providers** | `OPENAI_API_KEY` | - | OpenAI API key |
| | `ANTHROPIC_API_KEY` | - | Anthropic API key |
| | `AI_DEFAULT_MODEL` | `gpt-4o-mini` | Default AI model |
| | `AI_TEMPERATURE` | `0.7` | AI response creativity (0.0-2.0) |
| | `AI_MAX_TOKENS` | `4000` | Maximum AI response length |
| **Authentication** | `OAUTH_GOOGLE_CLIENT_ID` | - | Google OAuth client ID |
| | `OAUTH_GOOGLE_CLIENT_SECRET` | - | Google OAuth client secret |
| | `OAUTH_GITHUB_CLIENT_ID` | - | GitHub OAuth client ID |
| | `OAUTH_GITHUB_CLIENT_SECRET` | - | GitHub OAuth client secret |
| **Email** | `EMAIL_ENABLED` | `true` | Enable email sending |
| | `POSTMARK_SERVER_TOKEN` | - | Postmark API token |
| | `EMAIL_SENDER_ADDRESS` | - | From email address |
| | `EMAIL_SENDER_NAME` | - | From name |
| **Payments** | `STRIPE_SECRET_KEY` | - | Stripe secret key |
| | `STRIPE_PUBLISHABLE_KEY` | - | Stripe publishable key |
| | `STRIPE_WEBHOOK_SECRET` | - | Stripe webhook secret |
| **Cache & Rate Limiting** | `CACHE_ENABLED` | `true` | Enable caching |
| | `CACHE_REDIS_HOST` | `localhost` | Redis host for cache |
| | `DEFAULT_RATE_LIMIT_LIMIT` | `100` | Requests per minute |
| | `RATE_LIMITER_ENABLED` | `true` | Enable rate limiting |
| **Admin** | `ADMIN_USERNAME` | - | Admin panel username |
| | `ADMIN_PASSWORD` | - | Admin panel password |
| | `ADMIN_EMAIL` | - | Admin email address |
| | `ADMIN_ENABLED` | `true` | Enable/disable admin panel |
| **Monitoring** | `LOGFIRE_TOKEN` | - | Logfire monitoring token |
| | `LOGFIRE_PROJECT_NAME` | - | Logfire project name |
| | `LOGFIRE_SEND_TO_LOGFIRE` | `true` | Send data to Logfire |
| **Deployment** | `WORKERS` | `1` | Number of FastAPI workers (production) |

### Docker Compose Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | `localhost` | Domain for Caddy proxy |
| `APP_URL` | `http://localhost` | Application URL |
| `ADMIN_EMAIL` | `admin@localhost` | Admin email for certificates |
| `BACKEND_HOST` | `web` | Backend service name |
| `BACKEND_PORT` | `8000` | Backend service port |
| `LANDING_HOST` | `landing-page` | Landing page service name |
| `LANDING_PORT` | `4321` | Landing page service port |
| `LANDING_PAGE_PORT` | `4321` | External port for landing page |
| `LOG_FILE` | `/var/log/caddy/access.log` | Caddy log file path |

### Landing Page Configuration (`landing_page/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `GA_TRACKING_ID` | - | Google Analytics tracking ID (optional) |
| `API_BASE_URL` | `http://localhost:8000/api/v1` | Backend API URL |
| `NODE_ENV` | `development` | Node environment (development/production) |
| `PORT` | `4321` | Landing page port |

!!! note "Content Configuration"
    Most landing page customization happens in `content.yml`, not environment variables. The `.env` file only handles analytics and API connections.

### Landing Page Content (`landing_page/content.yml`)

The landing page is configured through a YAML file that controls all content, styling, and features without touching code:

| Section | Key | Purpose |
|---------|-----|---------|
| **App Info** | `app.name`, `app.tagline`, `app.description` | Basic product information |
| **Hero Section** | `hero.title`, `hero.subtitle`, `hero.cta` | Main landing page header |
| **Features** | `features.items[]` | Feature list with icons and descriptions |
| **Pricing** | `pricing.plans[]` | Pricing tiers with features and CTAs |
| **Testimonials** | `testimonials.items[]` | Customer testimonials with ratings |
| **Social Proof** | `stats.customers`, `stats.uptime`, etc. | Numbers and statistics |
| **Branding** | `branding.primaryColor`, `branding.logoUrl` | Colors and logo |
| **Layout** | `variants.hero`, `variants.features`, etc. | Component variants |
| **Features** | `features_enabled.pricing`, etc. | Enable/disable sections |

**Common Customizations:**

```yaml
# Update your product name and description
app:
  name: "Your AI SaaS"
  tagline: "AI-Powered Business Solutions"
  description: "Transform your workflow with intelligent automation"

# Change pricing (reflects your Stripe configuration)
pricing:
  plans:
    - name: "Starter"
      price: "$29"
      features:
        - "10,000 AI credits/month"
        - "Basic models (GPT-4o-mini)"
        - "Email support"

# Switch component layouts
variants:
  hero: "split"        # Hero with image on side
  features: "cards"    # Feature cards instead of showcase
  pricing: "simple"    # Simple pricing instead of comparison
```

**Layout Variants Available:**

- **Hero**: `centered`, `split`, `minimal`, `fullscreen`
- **Features**: `showcase`, `cards`, `grid`, `minimal`
- **Pricing**: `comparison`, `simple`, `detailed`
- **Testimonials**: `slider`, `grid`, `featured`
- **CTA**: `cards`, `banner`, `minimal`, `split`

Changes to `content.yml` are reflected immediately in development mode.

## Next Steps

Configuration done? Now learn how to customize FastroAI by removing features you don't need.

Remember: you don't need perfect configuration on day one. Start simple, add settings as you need them.

<div style="text-align: center; margin-top: 50px;">
    <a href="../customizing-features/" class="md-button md-button--primary">
        Next: Customizing Features →
    </a>
</div>
