# Configuration

Most of what you'll want to change lives in `content.yml`. This file controls all the text, pricing, testimonials, colors, and which sections appear. The `.env` file handles environment-specific stuff like analytics IDs and API URLs.

## The Content File

Open `landing_page/content.yml` and you'll see it's organized into logical sections. Let's walk through what you can customize.

### App Information

These details show up in the navbar, page title, and meta tags:

```yaml
app:
  name: "Your AI Product"
  tagline: "Revolutionary AI Solution"
  description: "Build amazing AI products with our powerful platform"
  domain: "yourapp.com"
  url: "https://yourapp.com"
  adminEmail: "hello@yourapp.com"
```

The `name` appears in the navbar and browser tab. The `description` goes into meta tags for SEO. The `adminEmail` gets used for contact form notifications.

### Hero Section

This is your main banner. You've got the headline, subtext, and a call-to-action button:

```yaml
hero:
  title: "Build Amazing AI Products"
  subtitle: "Get started with our powerful AI platform in minutes"
  cta:
    text: "Get Started"
    url: "#interest-signup"
```

There's also social proof you can customize:

```yaml
  socialProof:
    users: "1000+"
    userLabel: "developers"
    rating: "4.9"
    ratingLabel: "out of 5"
    avatars:
      - "JD"
      - "SM"
      - "+K"
```

The avatars array creates those circular initials you see on landing pages. Add as many as you want.

### Features

List what makes your product special. Each feature gets a title, description, and icon:

```yaml
features:
  title: "Why Choose Us"
  subtitle: "Discover the powerful features..."
  items:
    - title: "Fast & Secure"
      description: "Built with security and performance in mind."
      icon: "Zap"
    - title: "AI Powered"
      description: "Leverage cutting-edge AI technology."
      icon: "Bot"
```

Icons come from Lucide. Some popular ones: `Zap`, `Bot`, `Shield`, `Code`, `TrendingUp`, `MousePointer`, `Mail`, `User`, `Check`, `Star`, `Lock`, `Cloud`.

### Pricing

Define your pricing tiers. You can have as many plans as you want:

```yaml
pricing:
  title: "Simple Pricing"
  subtitle: "Choose the perfect plan for your needs."
  plans:
    - name: "Starter"
      price: "$19"
      period: "/month"
      description: "Perfect for individuals"
      features:
        - "Up to 10,000 API calls/month"
        - "Basic AI models"
        - "Email support"
      highlighted: false
      ctaText: "Get Started"
    - name: "Professional"
      price: "$49"
      period: "/month"
      description: "Ideal for growing businesses"
      features:
        - "Up to 100,000 API calls/month"
        - "Advanced AI models"
      highlighted: true
      ctaText: "Start Free Trial"
```

Set `highlighted: true` on one plan to make it stand out visually.

### Testimonials

Add customer quotes for social proof:

```yaml
testimonials:
  title: "What Our Customers Say"
  subtitle: "Join thousands of developers..."
  items:
    - name: "Sarah Chen"
      role: "CTO"
      company: "TechFlow"
      content: "This platform transformed how we handle AI integration."
      rating: 5
      avatar: "SC"
```

The rating displays as stars. The avatar uses initials.

### Stats

Key numbers for credibility:

```yaml
stats:
  customers: "10,000+"
  uptime: "99.9%"
  rating: "4.9/5"
  apiCalls: "1M+"
```

### Call-to-Action

The final conversion section at the bottom:

```yaml
cta:
  title: "Ready to Get Started?"
  subtitle: "Join thousands of developers..."
  primary:
    text: "Get Started"
    url: "#interest-signup"
  secondary:
    text: "Learn More"
    url: "#features"
  note: "No credit card required • Free 14-day trial"
```

### Branding

Set your colors and logo:

```yaml
branding:
  primaryColor: "#3B82F6"
  secondaryColor: "#1E40AF"
  logoUrl: "/images/logo.svg"
```

Colors should be hex values. The logo path is relative to `public/`.

### Theme Mode

Control light/dark appearance:

```yaml
theme:
  mode: "light"
```

Options are `auto` (respects system preference), `light`, or `dark`.

### Component Variants

Pick which design variant to use for each section:

```yaml
variants:
  hero: "centered"
  features: "showcase"
  pricing: "comparison"
  testimonials: "slider"
  cta: "cards"
```

### Feature Toggles

Turn sections on or off:

```yaml
features_enabled:
  pricing: true
  testimonials: true
  blog: false
  interestList: true
  contactForm: true
  navbar: true
```

### API Connection

Where form submissions go:

```yaml
api:
  baseUrl: "/api/v1"
  contactUrl: "/api/v1/landing/contact"
  interestUrl: "/api/v1/landing/interest"
```

### Social Links

Social media profiles for the footer:

```yaml
social:
  twitter: "https://twitter.com/yourcompany"
  github: "https://github.com/yourcompany"
  linkedin: "https://linkedin.com/company/yourcompany"
  facebook: ""
  instagram: ""
```

Leave a field empty to hide that icon.

## Environment Variables

The `.env` file handles settings that vary between environments.

### Analytics

Google Analytics tracking (leave empty to disable):

```bash
GA_TRACKING_ID=""
```

### API URL for Development

When running the backend separately during local development:

```bash
API_BASE_URL="http://localhost:8000/api/v1"
```

In production, you won't need this since Caddy handles the routing.

### Site URL

Required for sitemap generation:

```bash
APP_URL="https://yourapp.com"
```

## Static Assets

Put images and other static files in `public/`. A file at `public/images/logo.svg` is accessible at `/images/logo.svg`.

Common locations:

- `public/images/logo.svg` - Your logo
- `public/favicon.ico` - Browser favicon
- `public/images/og-image.png` - Social sharing image

## Key Files

| File | Purpose |
|------|---------|
| `content.yml` | All page content |
| `.env` | Environment-specific settings |
| `astro.config.mjs` | Astro build configuration |
| `tailwind.config.cjs` | TailwindCSS settings |
| `src/lib/content.ts` | Content loader with TypeScript types |

---

[← Overview](index.md){ .md-button }
