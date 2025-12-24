# Admin Interface

FastroAI includes a built-in admin panel powered by SQLAdmin. It gives you a web interface for managing users, subscriptions, products, and other data without writing custom CRUD endpoints.

## Accessing the Admin Panel

The admin panel lives at `/admin`. It's enabled by default, but you can disable it in production if you prefer:

```bash
ADMIN_ENABLED=true  # Set to false to disable
```

Admin authentication is separate from your app's user authentication. It uses simple username/password credentials stored in environment variables:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key  # Used for session encryption
```

When you visit `/admin`, you'll see a login form. Enter the credentials from your environment, and you're in.

## What's Included

FastroAI registers nine model views out of the box, organized into categories:

**Users & Access**

- **Users** - Create, edit, and manage user accounts
- **User Entitlements** - View and manage what users have access to

**Products & Pricing**

- **Tiers** - Subscription tiers with rate limits and features
- **Products** - What you sell (plans, add-ons, credit packs)
- **Prices** - Pricing options for products (monthly, yearly, etc.)

**Billing**

- **Payments** - Payment history and transaction records
- **Subscriptions** - Active and cancelled subscriptions
- **Discount Codes** - Promotional codes and coupons
- **Subscription Discounts** - Discounts applied to subscriptions

Each view gives you a paginated list with search, sort, and filter capabilities. Click on a record to see all its fields, edit it, or delete it.

## Common Operations

### Creating a User

Navigate to Users, click "Create", fill in the form. The password field expects a plain text password, which gets hashed automatically before saving.

### Managing Subscriptions

The Subscriptions view has bulk actions. Select subscriptions from the list and use "Cancel" to mark them as cancelled, or "Reactivate" to bring them back. Note that these actions update the database directly without calling Stripe, so use them for data cleanup rather than actual subscription management.

### Working with Discount Codes

Discount codes also have bulk actions for activating and deactivating. When you create a new code, it automatically creates the corresponding coupon in Stripe if you've configured the Stripe integration.

### Revoking Entitlements

The User Entitlements view lets you revoke or reactivate entitlements in bulk. Useful for handling refunds or support cases where you need to manually adjust what a user has access to.

## How Authentication Works

The admin panel uses session-based authentication, separate from the JWT/session auth used by your API. When you log in, your credentials are validated against the environment variables, a session cookie is set with `admin_authenticated = True`, and subsequent requests check this flag.

This is simpler than the main app's auth because the admin panel is meant for internal use by a small number of trusted people, not for end users.

## Key Files

| Component | Location |
|-----------|----------|
| Admin setup | `backend/src/interfaces/admin/initialize.py` |
| Authentication | `backend/src/interfaces/admin/auth.py` |
| Model views | `backend/src/interfaces/admin/views/` |
| Dataclass mixin | `backend/src/interfaces/admin/mixins.py` |

---

[← Webhooks](../payments/webhooks.md){ .md-button } [Customizing Admin →](customizing.md){ .md-button .md-button--primary }
