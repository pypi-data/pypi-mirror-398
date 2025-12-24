# Products & Prices

In Stripe's model, products describe what you sell, and prices describe how much it costs. A single product (like "Pro Plan") can have multiple prices (monthly and yearly options, different currencies, promotional pricing). FastroAI mirrors this structure in its database.

## Creating Products

Products are typically created through the admin interface or via Stripe directly. The `Product` model stores the local record and links to Stripe:

```python
class Product(Base):
    name: str                          # "Pro Plan", "Credit Pack", etc.
    description: str | None            # What the user gets
    stripe_product_id: str | None      # Links to Stripe
    tier_id: int | None                # Which tier this product grants
    product_type: str | None           # "subscription", "credits", "feature_access"
    is_active: bool                    # Available for purchase
```

The `product_type` field tells FastroAI what to do when someone buys this product. A subscription product grants tier access. A credits product adds credits to the user's balance. A feature_access product unlocks specific features.

### Product Types and What They Grant

Products can grant different things depending on their type:

| Type | Grants | Uses |
|------|--------|------|
| `subscription` | Tier access, recurring entitlements | Monthly/yearly plans |
| `credits` | Credit balance (uses `credit_amount` field) | AI token packs, API call bundles |
| `feature_access` | Specific feature unlock (uses `feature_access` JSON) | Add-ons like "Advanced Analytics" |
| `tier_upgrade` | One-time tier upgrade (uses `grants_tier_id`) | Lifetime deals |

The `access_duration_days` field controls how long the access lasts. Leave it `null` for permanent access or subscriptions (which manage their own duration).

## Creating Prices

Each product needs at least one price. The `Price` model defines the cost and billing cycle:

```python
class Price(Base):
    product_id: int                    # Which product
    unit_amount: int                   # Amount in cents (2999 = $29.99)
    currency: str                      # "usd", "eur", etc.
    price_type: PriceType              # ONE_TIME, RECURRING, CREDIT_PACK, etc.
    billing_interval: BillingInterval  # MONTH, YEAR (for recurring)
    stripe_price_id: str | None        # Links to Stripe
    extra_metadata: dict | None        # Entitlement configuration
```

### Price Types

FastroAI supports several pricing models beyond the basic ones:

| Type | Description |
|------|-------------|
| `ONE_TIME` | Single purchase, no recurring billing |
| `RECURRING` | Subscription with regular billing |
| `CREDIT_PACK` | Prepaid credits (like buying tokens) |
| `USAGE_BASED` | Pay per use (tokens, API calls) |
| `HYBRID` | Subscription base + usage overages |
| `SEAT_BASED` | Per-user pricing for teams |

For recurring prices, set the `billing_interval`:

| Interval | Meaning |
|----------|---------|
| `MONTH` | Monthly billing |
| `YEAR` | Annual billing |
| `WEEK` | Weekly billing |
| `DAY` | Daily billing |

The `billing_interval_count` field lets you do things like "every 3 months" by setting `interval=MONTH, interval_count=3`.

## Configuring Entitlements in Prices

The `extra_metadata` field on prices tells FastroAI what to grant when someone purchases this price. This is where you configure the entitlements:

```json
{
    "entitlements": [
        {
            "type": "CREDIT_GRANT",
            "credit_type": "ai_tokens",
            "quantity": 100000
        },
        {
            "type": "FEATURE_UNLOCK",
            "feature": "advanced_analytics"
        }
    ]
}
```

When the webhook handler processes a successful payment, it reads this configuration and grants the appropriate entitlements to the user. This means you can change what a price grants without modifying code.

## Syncing with Stripe

Products and prices exist in both FastroAI's database and Stripe. You can create them in either place, but they need to stay in sync.

### Creating via ProductService

When you create a product through `ProductService`, it automatically creates the Stripe product and stores the `stripe_product_id`:

```python
from src.modules.product.service import ProductService
from src.modules.product.schemas import ProductCreate

product_service = ProductService()

product = await product_service.create(
    ProductCreate(
        name="Pro Plan",
        description="Full access to all features",
        tier_id=1,
        product_type="subscription",
    ),
    db,
)
# product now has stripe_product_id populated
```

Set `create_stripe_product=False` in your schema if you only want a local record.

### Syncing from Stripe

If you've created products or prices directly in the Stripe Dashboard, you can pull them into your local database:

```python
from src.modules.product.service import ProductService
from src.modules.price.service import PriceService

product_service = ProductService()
price_service = PriceService()

# Sync all products from Stripe
result = await product_service.sync_from_stripe(db)
print(f"Created: {result['created_count']}, Updated: {result['updated_count']}")

# Sync all prices from Stripe
result = await price_service.sync_from_stripe(db)

# Or sync prices for a specific product
result = await price_service.sync_from_stripe(db, product_id=123)
```

The sync methods match records by `stripe_product_id` and `stripe_price_id`. Existing records get updated, new ones get created. Local-only records (without Stripe IDs) are left untouched.

This is useful when you want to manage your product catalog in Stripe's Dashboard and have FastroAI mirror it.

## Tier Association

Products can be associated with tiers through the `tier_id` field. When someone subscribes to a product that has a tier association, they get access to that tier's features.

This is different from `grants_tier_id`. The `tier_id` field says "this product belongs to the Pro tier" (for organization), while `grants_tier_id` says "purchasing this product upgrades the user to this tier" (for one-time tier upgrades).

## Purchase Requirements

Some products should only be available to certain users. The `requires_subscription` and `requires_tier_id` fields let you control this:

```python
# This add-on requires an active subscription
addon_product = Product(
    name="Advanced Analytics Add-on",
    requires_subscription=True,
)

# This product is only for Enterprise users
enterprise_tool = Product(
    name="Enterprise Integration Tool",
    requires_tier_id=enterprise_tier.id,
)
```

The payment service checks these requirements before creating a checkout session.

## Key Files

| Component | Location |
|-----------|----------|
| Product model | `backend/src/modules/product/models.py` |
| Product service | `backend/src/modules/product/service.py` |
| Price model | `backend/src/modules/price/models.py` |
| Price service | `backend/src/modules/price/service.py` |
| Price enums | `backend/src/modules/price/enums.py` |
| Stripe service | `backend/src/infrastructure/stripe/client.py` |

---

[← Payments Overview](index.md){ .md-button } [Subscriptions →](subscriptions.md){ .md-button .md-button--primary }
