# Credits

Credits are consumable resources that users spend when they use your product. Think AI tokens, API calls, document analyses, or any metered feature. FastroAI's credit system tracks balances from multiple sources and maintains a complete transaction history.

## How Credits Work

Credits come from different places: subscription allowances, one-time purchases, bonuses, promotions. Each source is tracked separately in a "pool," but they all contribute to a user's total balance for a given credit type.

A user might have 10,000 AI tokens from their Pro subscription, plus 5,000 from a promotional grant. When they use the AI features, credits are consumed from the oldest pools first (FIFO).

## Credit Types

The `CreditType` enum defines what kinds of credits your app supports:

| Type | Typical use |
|------|-------------|
| `AI_TOKENS` | LLM token consumption |
| `AI_GENERATIONS` | Number of AI generations |
| `API_CALLS` | API request quota |
| `DOCUMENT_ANALYSIS` | Document processing |
| `STORAGE` | Storage quota |
| `BANDWIDTH` | Bandwidth allowance |
| `FEATURES` | Feature access unlocks |
| `CUSTOM` | Whatever you need |

You can add more by extending the enum in `backend/src/modules/credits/enums.py`.

## Pools: Where Credits Come From

Each credit balance belongs to a "pool" that identifies its source. This lets you track where credits came from and apply different expiration rules:

| Pool | Description |
|------|-------------|
| `SUBSCRIPTION_ALLOWANCE` | Monthly credits included with subscription |
| `PURCHASED` | Bought directly by the user |
| `BONUS` | Given as a bonus (referral, loyalty) |
| `PROMOTIONAL` | Promotional campaign grants |
| `TRIAL` | Trial period credits |
| `ROLLOVER` | Unused credits rolled over from previous period |
| `TOP_UP` | Additional purchase on top of subscription |

Pools matter for expiration. Subscription allowance credits might expire at the end of each billing cycle, while purchased credits might never expire.

## Credit Balances

The `CreditBalance` model tracks how many credits a user has:

```python
class CreditBalance(Base):
    user_id: int                    # Who owns these credits
    credit_type: CreditType         # AI_TOKENS, API_CALLS, etc.
    pool_identifier: PoolIdentifier # Where they came from
    balance: int                    # Available credits
    reserved: int                   # Held for pending operations
    expires_at: datetime | None     # When they expire
```

A user can have multiple `CreditBalance` records for the same credit type if they have credits from different pools.

## Transaction History

Every credit change is recorded in `CreditTransaction`:

```python
class CreditTransaction(Base):
    user_id: int                    # Whose credits changed
    credit_type: CreditType         # Which type
    amount: int                     # How many (positive or negative)
    balance_before: int             # Balance before this transaction
    balance_after: int              # Balance after this transaction
    transaction_type: TransactionType  # PURCHASE, USAGE, GRANT, etc.
    description: str                # Human-readable explanation
    reference_id: str | None        # Link to payment, subscription, etc.
```

This gives you a complete audit trail for billing disputes, usage analytics, and debugging.

## Transaction Types

| Type | When it's used |
|------|----------------|
| `PURCHASE` | User bought credits |
| `GRANT` | Subscription, promotion, or admin grant |
| `USAGE` | Credits consumed by user action |
| `REFUND` | Credits returned after refund |
| `EXPIRATION` | Credits expired |
| `BONUS` | Bonus credits awarded |
| `ADJUSTMENT` | Manual admin adjustment |
| `TRANSFER` | Moved between pools |

## Credits and Entitlements

In FastroAI, credits are actually granted through the entitlement system. When a user subscribes or purchases a credit pack, the webhook handler grants a `CREDIT_GRANT` entitlement. The credit service queries entitlements to calculate the total available balance.

This connection is documented in the [Entitlements](../access-control/entitlements.md) guide. The short version: entitlements are the source of truth for what credits a user has, and the credit system provides the convenience API for checking and consuming them.

## Checking Balances

To get a user's credit balance:

```python
from src.modules.credits.service import CreditService
from src.modules.credits.enums import CreditType

credit_service = CreditService()

balance = await credit_service.get_user_balance(
    user_id=123,
    credit_type=CreditType.AI_TOKENS,
    db=db,
)

print(f"Available: {balance['available']}")
print(f"Reserved: {balance['reserved']}")
print(f"Expires: {balance['expires_at']}")
```

Or get all balances at once:

```python
balances = await credit_service.get_user_balances(user_id=123, db=db)

for credit_type, balance in balances.items():
    print(f"{credit_type}: {balance['available']}")
```

## Reserving and Consuming Credits

For long-running operations, you might want to reserve credits before starting work:

1. **Reserve** credits when the operation starts (moves from `balance` to `reserved`)
2. **Consume** when the operation completes (deducts from `reserved`)
3. **Release** if the operation fails (moves back to `balance`)

This prevents race conditions where a user could start multiple operations that together exceed their balance.

For simple immediate consumption, see the [Credit Dependencies](../access-control/entitlements.md#credit-dependencies) pattern in the Entitlements guide.

## Expiring Credits

Credits can have expiration dates. Subscription allowances typically expire at the end of each billing period so they don't accumulate indefinitely.

When credits expire, create a transaction with `transaction_type=EXPIRATION` and reduce the balance. You can set up a scheduled task to handle this automatically.

## Key Files

| Component | Location |
|-----------|----------|
| Credit enums | `backend/src/modules/credits/enums.py` |
| Credit models | `backend/src/modules/credits/models.py` |
| Credit service | `backend/src/modules/credits/service.py` |
| Entitlement integration | `backend/src/modules/entitlement/service.py` |

---

[← Discounts](discounts.md){ .md-button } [Webhooks →](webhooks.md){ .md-button .md-button--primary }
