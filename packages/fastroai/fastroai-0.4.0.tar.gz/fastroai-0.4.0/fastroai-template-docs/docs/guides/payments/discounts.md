# Discounts

Promotional codes and coupons help with customer acquisition and retention. FastroAI integrates with Stripe's coupon system while adding local tracking for usage limits, expiration, and scope control.

## Creating Discount Codes

Discount codes are created through the admin interface or via the DiscountService. Each code has a Stripe coupon backing it, which is created automatically when you create the discount code.

### Discount Types

You can offer discounts as either a percentage off or a fixed amount:

| Type | `discount_value` means |
|------|------------------------|
| `PERCENTAGE` | Percentage to deduct (20 means 20% off) |
| `FIXED_AMOUNT` | Amount in cents to deduct (500 means $5.00 off) |

### Duration

How long should the discount apply?

| Duration | Behavior |
|----------|----------|
| `ONCE` | Applies to the next invoice only |
| `REPEATING` | Applies for N billing cycles (set `duration_in_months`) |
| `FOREVER` | Applies to every invoice while subscription is active |

For `REPEATING` discounts, set `duration_in_months` to specify how many months the discount lasts:

```python
# 20% off for the first 3 months
DiscountCode(
    code="NEWYEAR2024",
    discount_type=DiscountType.PERCENTAGE,
    discount_value=20,
    duration=DiscountDuration.REPEATING,
    duration_in_months=3,
)
```

### Scope

Control which payment types can use a discount:

| Scope | What it applies to |
|-------|-------------------|
| `ONE_TIME_ONLY` | Only one-time purchases, rejected for subscriptions |
| `SUBSCRIPTION_ONLY` | Only subscriptions, rejected for one-time purchases |
| `BOTH` | Any payment type |

This prevents accidents like someone using a "first month free" subscription coupon on a one-time credit pack purchase.

## Applying Discounts at Checkout

Users enter a discount code when starting checkout:

```python
from src.modules.payment.service import PaymentService
from src.modules.payment.schemas import PaymentCreate

payment_service = PaymentService()

result = await payment_service.create_checkout_session(
    user_id=123,
    payment_data=PaymentCreate(
        price_id=456,
        discount_code="SAVE20",
    ),
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    db=db,
)
```

The payment service validates the code before creating the checkout session:

1. **Scope check**: Is the code valid for this payment type?
2. **Expiration check**: Has the code expired?
3. **Usage limit check**: Has the code reached its maximum uses?
4. **Status check**: Is the code still active?

If validation fails, the checkout creation fails with an appropriate error message. If it passes, the discount is applied to the Stripe checkout session.

## Applying Discounts to Existing Subscriptions

You can also apply discounts to subscriptions that are already active:

```python
from src.infrastructure.stripe.client import AsyncStripeService

stripe_service = AsyncStripeService()

await stripe_service.apply_coupon_to_subscription_async(
    subscription_id="sub_...",
    coupon_id="coupon_...",
)
```

This is useful for win-back campaigns or customer service situations where you want to give an existing subscriber a discount.

## Usage Limits and Tracking

Each discount code can have optional limits:

| Field | What it controls |
|-------|------------------|
| `max_uses` | Maximum redemptions (null = unlimited) |
| `current_uses` | How many times it's been used |
| `expires_at` | Expiration date (null = never expires) |

When a checkout completes successfully, the webhook handler increments `current_uses`. If a code reaches `max_uses`, its status changes to `EXHAUSTED` and it can no longer be used.

```python
# Limited-time promotion: 100 uses, expires at year end
DiscountCode(
    code="BLACKFRIDAY",
    discount_type=DiscountType.PERCENTAGE,
    discount_value=50,
    duration=DiscountDuration.ONCE,
    max_uses=100,
    expires_at=datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC),
)
```

## Tracking Subscription Discounts

For recurring discounts, FastroAI tracks how many billing cycles the discount has been applied. The `SubscriptionDiscount` model keeps this history:

```python
class SubscriptionDiscount(Base):
    subscription_id: int         # Which subscription
    discount_code_id: int        # Which discount
    stripe_subscription_id: str  # Stripe reference

    cycles_applied: int          # How many cycles so far
    max_cycles: int | None       # Limit for REPEATING discounts
    is_active: bool              # Still applying?
    ended_at: datetime | None    # When it stopped
```

For a `REPEATING` discount that lasts 3 months, `cycles_applied` starts at 0 and increments with each invoice. When it hits `max_cycles`, `is_active` becomes `False` and `ended_at` is set.

## Checking If a Discount Is Usable

A discount code's usability is determined by checking multiple fields rather than a single status field. The code is usable if `is_active` is `True`, `expires_at` hasn't passed (or is null), and `current_uses` is below `max_uses` (or `max_uses` is null for unlimited).

The payment service validates all of these conditions when a discount code is applied at checkout. If any check fails, the checkout creation fails with an appropriate error message explaining why the code can't be used.

## Removing Subscription Discounts

Sometimes you need to end a subscription discount early:

```python
await stripe_service.remove_subscription_discount_async(
    subscription_id="sub_...",
)
```

This removes the discount from Stripe and FastroAI marks the `SubscriptionDiscount` record as ended.

## Key Files

| Component | Location |
|-----------|----------|
| Discount enums | `backend/src/modules/discount/enums.py` |
| Discount models | `backend/src/modules/discount/models.py` |
| Discount service | `backend/src/modules/discount/service.py` |
| Stripe coupon methods | `backend/src/infrastructure/stripe/client.py` |

---

[← Subscriptions](subscriptions.md){ .md-button } [Credits →](credits.md){ .md-button .md-button--primary }
