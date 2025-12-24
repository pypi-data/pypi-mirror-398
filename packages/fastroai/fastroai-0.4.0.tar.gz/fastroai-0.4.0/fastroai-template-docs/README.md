<div align="center">

# FastroAI

### **Complete AI stack: FastAPI + AstroJS + PydanticAI.**

<p align="center">
  <a href="https://docs.fastro.ai">
    <img src="docs/assets/logo.png" alt="FastroAI Logo" width="25%">
  </a>
</p>

[FastroAI](https://fastro.ai) • [Documentation](https://docs.fastro.ai) • [Discord](https://discord.com/invite/TEmPs22gqB)

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![PydanticAI](https://img.shields.io/badge/PydanticAI-E92063?style=for-the-badge&logoColor=white)](https://pydantic-ai.org)

</div>

---

You bought FastroAI to skip months of infrastructure work. Smart move. Here's exactly what you got, a quick getting started guide and pointers to other resources.

## What You Got

Authentication, payments, AI agents, background tasks, monitoring - everything production needs. No assembly required.

* 🤖 **AI Integration** - FastroAgent wrapper around PydanticAI with memory strategies, tools, and usage tracking
* 🔐 **Auth System** - Session-based auth with OAuth (Google, GitHub) + JWT available for mobile/API
* 💳 **Payment System** - Complete Stripe integration with subscriptions, credits, discounts, and webhooks
* 🎯 **Entitlement System** - Unified access control supporting tiers, credits, products, and hybrid models
* 🧰 **Database** - FastCRUD + PostgreSQL with async operations and clean patterns
* 📧 **Email System** - Template-based emails with multiple providers and automation workflows
* 🚦 **Background Tasks** - Taskiq async workers for high-performance task processing with monitoring
* 🛡️ **Rate Limiting** - Intelligent throttling with multiple backends (Redis/Memcached)
* 📊 **Observability** - Structured logging, tracing, and Logfire integration
* 🎨 **Landing Page** - AstroJS marketing site with conversion optimization
* 🧑‍💼 **Admin Interface** - SQLAdmin for data management with security
* 🔑 **API Keys** - Full API key management with scoping and analytics
* 🐳 **Production Ready** - Docker setup with uv optimization and security validation

Now that you know everything you got, let's actually see it running.

## Quick Start: 5-Minute Setup

You will have a working AI API in 5 minutes by following this simple guide.

### Prerequisites

<table>
<tr>
<td align="center">🐍</td>
<td><strong>Python 3.11+</strong><br/>For modern type hints and performance</td>
</tr>
<tr>
<td align="center">🐳</td>
<td><strong>Docker & Docker Compose</strong><br/>For easy development setup</td>
</tr>
<tr>
<td align="center">🔑</td>
<td><strong>AI API Key</strong><br/>OpenAI, Anthropic, or your provider</td>
</tr>
</table>

Ensure you have Python 3.11+, docker, and an API Key from your favorite provider before we start. [Groq](https://groq.com/) has free tier API keys if you want to just test it.

### 1. Clone Your Template

First, click the green Use this template button in the top right corner of the repository to create your own copy. Important: Keep your new repository private - this is commercial code you paid for.

Then clone your new repository:

```bash
git clone <your-new-repo-url>
cd fastroai
```

Next we need to configure our environment to pick the features we want.

### 2. Configure Environment

FastroAI uses environment variables for configuration, for a complete guide on all possible settings and what every variable in your .env means, [check the docs](https://docs.fastro.ai/getting-started/configuration/).

For this quick guide you can just copy the example files and customize them later:

```bash
cp .env.example .env                             # Docker Compose settings
cp backend/.env.example backend/.env             # Backend API configuration
cp landing_page/.env.example landing_page/.env   # Landing page (optional)
```

Edit `backend/.env` with the required values (almost everything has defaults, but change these):

```bash
# Security - change this in production (generate with: openssl rand -hex 32)
SECRET_KEY=<your-generated-secret-key>

# AI Provider (at least one is required)
OPENAI_API_KEY=<your-openai-key>
# ANTHROPIC_API_KEY=<your-anthropic-key>

# Admin User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<choose-strong-password>
ADMIN_EMAIL=admin@yourdomain.com
```

Now that your configuration is done, let's see how to start FastroAI.

### 3. Start Everything

One command starts your entire stack:

```bash
docker compose up -d
```

Wait about 30 seconds for all services to start, then initialize the database:

```bash
docker compose run --rm setup_initial_data
```

### **🎉 Your AI API is Ready!**

That's it. Open the following links to see your actual services running locally:

<table>
<tr>
<td align="center">🎨</td>
<td><strong><a href="http://localhost:4321">Landing Page</a></strong><br/>Marketing site with conversion optimization</td>
</tr>
<tr>
<td align="center">📖</td>
<td><strong><a href="http://localhost:8000/docs">Interactive API Docs</a></strong><br/>Swagger UI with live testing</td>
</tr>
<tr>
<td align="center">🔧</td>
<td><strong><a href="http://localhost:8000/admin">Admin Interface</a></strong><br/>Manage users, payments, and data</td>
</tr>
<tr>
<td align="center">📊</td>
<td><strong><a href="http://localhost:8000/health">Health Check</a></strong><br/>System status monitoring</td>
</tr>
</table>

And to see about each part in more details, check the docs.

## Next Steps

Here's what you should do next:

- 💬 **[Join the Discord Server](https://discord.com/invite/TEmPs22gqB)** - DM your Github username to someone from the team to get access to exclusive FastroAI channels and support
- 🚀 **[Get Started](https://docs.fastro.ai/getting-started/)** - Detailed setup guide with environment configuration, testing, and troubleshooting
- 🎓 **[Learn AI Development](https://docs.fastro.ai/learn/)** - Build your first AI application step-by-step from problem identification to working implementation

And if you need support, check the next section.

## Support & Community

We have different communication channels, each with its purpose.

**For FastroAI-specific issues:** Use [GitHub Issues](https://github.com/fastroai/fastroai/issues) or [GitHub Discussions](https://github.com/fastroai/fastroai/discussions) - these are the source of truth for technical problems and feature requests.

**For quick questions and community chat:** you can just ask in discord specific channels in a less formal way. Maybe someone else had the same doubt and found an answer - this may indicate an issue (lack of clarity) or not (maybe you just didn't find something in the docs).

**For support priority:** GitHub gets detailed responses but may take longer. Discord gets quicker responses but less detailed answers. Discord is also better for sync discussions.

## Releases & Updates

FastroAI is actively developed and improved based on user feedback. Here's how releases work:

### Versioning System

We use [ZeroVer](https://0ver.org/) (`0.x.y`) during active development:

- **Minor updates (0.1.0 → 0.1.1)**: No breaking changes. Safe updates with bug fixes and small improvements
- **Feature updates (0.1.0 → 0.2.0)**: Might include breaking changes. Significant new features and improvements

### What to Expect

**Migration Guides**: Every release includes detailed migration instructions. We assume you haven't heavily modified core infrastructure, but always explain the rationale so you can adapt if you have.

**Support Policy**: While in ZeroVer, we support the latest version only. Once `0.x+1.y` is released, support for `0.x.y` ends. This lets us move fast and fix things.

**Release Notes**: Each release includes detailed descriptions of changes, motivations, and step-by-step migration guides.

### Staying Updated

- **Watch** the [FastroAI repository](https://github.com/fastroai/fastroai) for release notifications
- **Join** our [Discord server](https://discord.com/invite/TEmPs22gqB) for early access to release discussions and beta features
- **Check** [GitHub Releases](https://github.com/fastroai/fastroai/releases) for detailed migration guides and changelogs

We built FastroAI for our own use, so improvements are continuous. You're helping shape the product, your feedback and usage directly influences development priorities.

## License

FastroAI is a commercial product owned by **Benav Labs LLC**. <br/>
Build unlimited projects, can't share or redistribute the template.

### ✅ **What You Can Do**

- Use FastroAI for unlimited commercial projects
- Modify and customize the code for your needs
- Deploy applications built with FastroAI commercially
- Build and sell applications using the template
- Share your closed source code built on top of FastroAI with your teammates

### 🚫 **What You Cannot Do**

- Redistribute, resell, or sublicense the original template
- Remove copyright notices or attribution
- Create competing development frameworks using proprietary FastroAI components
- Create open source projects that include proprietary FastroAI components
- Share your license or allow unauthorized access

Full terms: [fastro.ai/terms](https://fastro.ai/terms)

## What Now?

That's it. Check the [docs](https://docs.fastro.ai/), use FastroAI to build something awesome, and share it with us on [Discord](https://discord.com/invite/TEmPs22gqB).

---

<p align="center"><i>Built with 💜 by <a href="https://benav.io">Benav Labs</a></i></p>
